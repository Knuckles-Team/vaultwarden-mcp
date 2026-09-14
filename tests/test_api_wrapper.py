"""Transport and authentication boundaries of the Vaultwarden API client."""

import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from vaultwarden_mcp.api import (
    VaultwardenApi,
    VaultwardenApiError,
    VaultwardenCredentials,
)
from vaultwarden_mcp.api.api_client_base import ADMIN_COOKIE, _MAX_RESPONSE_BYTES


def _tls_profile():
    profile = MagicMock()
    profile.proxy_url = None
    profile.trust_env = False
    profile.httpx_kwargs.return_value = {"verify": True, "trust_env": False}
    return profile


class FakeSession:
    """Replays queued (status, body) responses and records every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.cookies = {}

    @contextmanager
    def stream(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        status, body, cookie = self.responses.pop(0)
        if cookie:
            self.cookies[ADMIN_COOKIE] = "session"
        response = MagicMock()
        response.status_code = status
        response.headers = {}
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        response.iter_bytes.return_value = [raw]
        yield response

    def close(self):
        pass


def _client(responses, **credentials):
    with patch(
        "vaultwarden_mcp.api.api_client_base.create_http_client",
        return_value=FakeSession(responses),
    ):
        return VaultwardenApi(
            base_url="https://vault.example.invalid",
            tls_profile=_tls_profile(),
            credentials=VaultwardenCredentials(**credentials),
        )


TOKEN = (
    200,
    {"access_token": "tok-1", "expires_in": 7200, "Key": "2.k", "Kdf": 0},
    False,
)


def test_public_request_returns_json():
    client = _client([(200, {"version": "2026.6.0"}, False)])
    assert client.server_config() == {"version": "2026.6.0"}
    method, url, kwargs = client.session.calls[0]
    assert (method, url) == ("GET", "https://vault.example.invalid/api/config")
    assert "Authorization" not in kwargs["headers"]
    assert kwargs["follow_redirects"] is False


def test_request_rejects_origin_change():
    client = _client([])
    with pytest.raises(ValueError, match="API path"):
        client.request("GET", "https://example.invalid/api/sync")


def test_request_rejects_oversized_response():
    client = _client([(200, b"x" * (_MAX_RESPONSE_BYTES + 1), False)])
    with pytest.raises(RuntimeError, match="size limit"):
        client.request("GET", "alive", auth="none")


def test_user_requests_obtain_and_reuse_an_api_key_token():
    client = _client(
        [TOKEN, (200, {"ciphers": []}, False), (200, {"ciphers": []}, False)],
        client_id="user.1",
        client_secret="secret-value",
    )
    client.sync_vault()
    client.sync_vault()
    token_call, first, second = client.session.calls
    assert token_call[1].endswith("/identity/connect/token")
    assert token_call[2]["data"]["grant_type"] == "client_credentials"
    assert first[2]["headers"]["Authorization"] == "Bearer tok-1"
    assert second[2]["headers"]["Authorization"] == "Bearer tok-1"
    assert client.token_response() == {"expires_in": 7200, "Key": "2.k", "Kdf": 0}


def test_a_401_renews_the_token_once():
    client = _client(
        [
            TOKEN,
            (401, {"message": "expired"}, False),
            TOKEN,
            (200, {"ok": True}, False),
        ],
        client_id="user.1",
        client_secret="secret-value",
    )
    assert client.request("GET", "api/accounts/profile") == {"ok": True}
    assert len(client.session.calls) == 4


def test_errors_carry_the_server_message_but_never_credentials():
    client = _client(
        [TOKEN, (400, {"message": "Cipher is not write accessible"}, False)],
        client_id="user.1",
        client_secret="secret-value",
    )
    with pytest.raises(VaultwardenApiError) as exc_info:
        client.request("PUT", "api/ciphers/x", json_body={"name": "2.enc"})
    assert exc_info.value.status == 400
    assert "not write accessible" in str(exc_info.value)
    assert "secret-value" not in str(exc_info.value)


def test_user_requests_without_an_api_key_fail_clearly():
    client = _client([])
    with pytest.raises(VaultwardenApiError, match="API key"):
        client.sync_vault()


def test_admin_requests_log_in_with_the_admin_token_cookie():
    client = _client(
        [(303, b"", True), (200, [{"id": "u1"}], False)], admin_token="admin-secret"
    )
    assert client.request("GET", "admin/users", auth="admin") == [{"id": "u1"}]
    login, users = client.session.calls
    assert login[1].endswith("/admin") and login[2]["data"] == {"token": "admin-secret"}
    assert "Authorization" not in users[2]["headers"]


def test_a_rejected_admin_token_raises():
    client = _client([(200, b"<html>login</html>", False)], admin_token="wrong")
    with pytest.raises(VaultwardenApiError, match="admin token"):
        client.request("GET", "admin/users", auth="admin")


def test_soft_delete_uses_put():
    client = _client(
        [TOKEN, (200, b"", False)], client_id="user.1", client_secret="secret-value"
    )
    client.soft_delete_ciphers(["a", "b"])
    method, url, kwargs = client.session.calls[1]
    assert (method, url) == ("PUT", "https://vault.example.invalid/api/ciphers/delete")
    assert kwargs["json"] == {"ids": ["a", "b"]}


def test_credentials_are_redacted():
    assert "secret" not in repr(VaultwardenCredentials(client_secret="secret"))
