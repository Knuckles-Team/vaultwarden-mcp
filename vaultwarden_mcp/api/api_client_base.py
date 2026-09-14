"""HTTP transport and authentication for the Vaultwarden (Bitwarden-compatible) API.

Each request declares how it authenticates:

* ``user`` — a bearer token obtained with the account's personal API key
  (``grant_type=client_credentials``), cached until shortly before it expires and
  renewed once when the server answers 401;
* ``admin`` — the ``VW_ADMIN`` session cookie issued after posting the instance admin
  token to ``/admin``;
* ``none`` — public endpoints such as prelogin, ``/alive``, and ``/api/config``.

Requests stay on the configured origin, never follow redirects, and are bounded in time
and size. Error messages carry the server's short message only — never request bodies,
tokens, or credentials.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import SplitResult, urljoin, urlsplit

from agent_utilities.core.http_client import create_http_client
from agent_utilities.core.transport_security import ResolvedTLSProfile

_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
_MAX_RESPONSE_SECONDS = 60.0
_REQUEST_TIMEOUT_S = 30.0
_TOKEN_EXPIRY_SKEW_S = 60.0
_MAX_ERROR_MESSAGE = 300
_DEVICE_TYPE_LINUX_CLI = "25"

ADMIN_COOKIE = "VW_ADMIN"
DEFAULT_DEVICE_IDENTIFIER = str(
    uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Knuckles-Team/vaultwarden-mcp")
)

AuthMode = Literal["user", "admin", "none"]


def _origin(parsed: SplitResult) -> tuple[str, str, int]:
    scheme = parsed.scheme.lower()
    return (
        scheme,
        (parsed.hostname or "").lower(),
        parsed.port or (443 if scheme == "https" else 80),
    )


def _validate_base_url(base_url: str) -> tuple[str, tuple[str, str, int], str]:
    rendered = str(base_url or "").strip()
    if not rendered or len(rendered) > 2048 or any(c in rendered for c in "\x00\r\n"):
        raise ValueError("Invalid service base URL")
    try:
        parsed = urlsplit(rendered)
        origin = _origin(parsed)
    except ValueError as exc:
        raise ValueError("Invalid service base URL") from exc
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Service base URL must be HTTP(S) without credentials")
    return rendered.rstrip("/") + "/", origin, parsed.hostname.lower()


def _request_url(
    base_url: str, expected_origin: tuple[str, str, int], path: str
) -> str:
    rendered = str(path or "")
    if len(rendered) > 4096 or any(c in rendered for c in "\x00\r\n"):
        raise ValueError("Invalid API path")
    try:
        url = urljoin(base_url, rendered.lstrip("/"))
        if _origin(urlsplit(url)) != expected_origin:
            raise ValueError("API path changed the configured service origin")
    except ValueError as exc:
        raise ValueError("Invalid API path") from exc
    return url


@dataclass(frozen=True, repr=False)
class VaultwardenCredentials:
    """Resolved credential values. Never logged, never rendered."""

    client_id: str | None = None
    client_secret: str | None = None
    admin_token: str | None = None
    device_identifier: str = DEFAULT_DEVICE_IDENTIFIER
    device_name: str = "vaultwarden-mcp"

    def __repr__(self) -> str:
        return "VaultwardenCredentials(<redacted>)"


class VaultwardenApiError(RuntimeError):
    """The server rejected a request. ``message`` is the server's short explanation."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message[:_MAX_ERROR_MESSAGE]
        super().__init__(f"Vaultwarden API error {status}: {self.message}")


def _error_message(body: bytes) -> str:
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "request failed"
    if not isinstance(payload, dict):
        return "request failed"
    model = payload.get("errorModel") or payload.get("ErrorModel") or {}
    for candidate in (
        payload.get("message"),
        payload.get("Message"),
        payload.get("error_description"),
        model.get("message") if isinstance(model, dict) else None,
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return "request failed"


def _decode(status: int, body: bytes) -> Any:
    if status == 204 or not body:
        return {"status": status}
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"status": status, "text": body.decode("utf-8", errors="replace")[:4096]}


class VaultwardenApiBase:
    """Transport, authentication, and the few calls other layers depend on."""

    def __init__(
        self,
        base_url: str,
        tls_profile: ResolvedTLSProfile,
        credentials: VaultwardenCredentials | None = None,
        *,
        token: str | None = None,
    ) -> None:
        self.base_url, self._origin, hostname = _validate_base_url(base_url)
        self.tls_profile = tls_profile
        self.credentials = credentials or VaultwardenCredentials()
        self._access_token: str | None = token or None
        self._token_expires_at = float("inf") if token else 0.0
        self._token_payload: dict[str, Any] = {}
        self._admin_authenticated = False
        self.session = create_http_client(
            timeout=_REQUEST_TIMEOUT_S,
            headers={"Accept": "application/json"},
            follow_redirects=False,
            pin_egress=not tls_profile.proxy_url and not tls_profile.trust_env,
            allowed_private_hosts=(hostname,),
            allow_loopback=True,
            **tls_profile.httpx_kwargs(),
        )

    # -- transport -------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        auth: AuthMode = "user",
        json_body: Any = None,
        form: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send one request and return decoded JSON (or ``{"status", "text"}``)."""
        return self._request(
            method, path, auth=auth, json_body=json_body, form=form, params=params
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        auth: AuthMode,
        json_body: Any = None,
        form: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        retry: bool = True,
    ) -> Any:
        url = _request_url(self.base_url, self._origin, path)
        kwargs: dict[str, Any] = {
            "headers": self._auth_headers(auth),
            "follow_redirects": False,
        }
        if params:
            kwargs["params"] = {k: v for k, v in params.items() if v is not None}
        if json_body is not None:
            kwargs["json"] = json_body
        if form is not None:
            kwargs["data"] = form
        status, body = self._send(method, url, kwargs)
        if retry and self._needs_reauthentication(auth, status):
            self._forget(auth)
            return self._request(
                method,
                path,
                auth=auth,
                json_body=json_body,
                form=form,
                params=params,
                retry=False,
            )
        if status >= 400:
            raise VaultwardenApiError(status, _error_message(body))
        return _decode(status, body)

    def _send(self, method: str, url: str, kwargs: dict[str, Any]) -> tuple[int, bytes]:
        with self.session.stream(method, url, **kwargs) as response:
            declared = response.headers.get("content-length")
            if declared:
                try:
                    declared_size = int(declared)
                except ValueError as exc:
                    raise RuntimeError("Invalid response content length") from exc
                if declared_size < 0 or declared_size > _MAX_RESPONSE_BYTES:
                    raise RuntimeError("Response size limit exceeded")
            body = bytearray()
            deadline = time.monotonic() + _MAX_RESPONSE_SECONDS
            for chunk in response.iter_bytes():
                if time.monotonic() > deadline:
                    raise RuntimeError("Response time limit exceeded")
                body.extend(chunk)
                if len(body) > _MAX_RESPONSE_BYTES:
                    raise RuntimeError("Response size limit exceeded")
            return int(response.status_code), bytes(body)

    # -- authentication ---------------------------------------------------------------

    def _auth_headers(self, auth: AuthMode) -> dict[str, str]:
        if auth == "none":
            return {}
        if auth == "admin":
            if not self._admin_authenticated:
                self._authenticate_admin()
            return {}
        if not self._access_token or time.monotonic() >= self._token_expires_at:
            self._authenticate_user()
        return {"Authorization": f"Bearer {self._access_token}"}

    def _needs_reauthentication(self, auth: AuthMode, status: int) -> bool:
        if auth == "user":
            return status == 401 and bool(self.credentials.client_id)
        if auth == "admin":
            return status == 401 or 300 <= status < 400
        return False

    def _forget(self, auth: AuthMode) -> None:
        if auth == "user":
            self._access_token = None
            self._token_expires_at = 0.0
        elif auth == "admin":
            self._admin_authenticated = False

    def _authenticate_user(self) -> None:
        creds = self.credentials
        if not (creds.client_id and creds.client_secret):
            raise VaultwardenApiError(
                401, "an API key (client_id and client_secret) is required"
            )
        payload = self._request(
            "POST",
            "identity/connect/token",
            auth="none",
            form={
                "grant_type": "client_credentials",
                "scope": "api",
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "device_identifier": creds.device_identifier,
                "device_name": creds.device_name,
                "device_type": _DEVICE_TYPE_LINUX_CLI,
            },
            retry=False,
        )
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise VaultwardenApiError(401, "token response carried no access token")
        lifetime = float(payload.get("expires_in") or 0)
        self._access_token = token
        self._token_expires_at = time.monotonic() + max(
            lifetime - _TOKEN_EXPIRY_SKEW_S, 0.0
        )
        self._token_payload = {
            k: v
            for k, v in payload.items()
            if k not in {"access_token", "refresh_token"}
        }

    def _authenticate_admin(self) -> None:
        if not self.credentials.admin_token:
            raise VaultwardenApiError(401, "an admin token is required")
        url = _request_url(self.base_url, self._origin, "admin")
        status, _ = self._send(
            "POST",
            url,
            {
                "data": {"token": self.credentials.admin_token},
                "follow_redirects": False,
            },
        )
        if status >= 400 or ADMIN_COOKIE not in self.session.cookies:
            raise VaultwardenApiError(401, "the admin token was rejected")
        self._admin_authenticated = True

    def token_response(self) -> dict[str, Any]:
        """Identity response fields other than tokens: ``Key``, ``PrivateKey``, KDF."""
        if not self._token_payload:
            self._authenticate_user()
        return dict(self._token_payload)

    # -- calls other layers depend on ---------------------------------------------------

    def server_alive(self) -> Any:
        return self.request("GET", "alive", auth="none")

    def server_version(self) -> Any:
        return self.request("GET", "api/version", auth="none")

    def server_config(self) -> Any:
        return self.request("GET", "api/config", auth="none")

    def sync_vault(self, *, exclude_domains: bool = True) -> dict[str, Any]:
        result = self.request(
            "GET", "api/sync", params={"excludeDomains": str(exclude_domains).lower()}
        )
        if not isinstance(result, dict):
            raise VaultwardenApiError(502, "sync response was not an object")
        return result

    def soft_delete_ciphers(self, ids: list[str]) -> Any:
        """Move items to trash in bulk.

        ``PUT /api/ciphers/delete`` is a soft delete. ``POST /api/ciphers/delete`` and
        ``DELETE /api/ciphers`` are permanent in Vaultwarden — never use them here.
        """
        return self.request("PUT", "api/ciphers/delete", json_body={"ids": list(ids)})

    def close(self) -> None:
        self.session.close()
