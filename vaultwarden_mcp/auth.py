"""Resolve connector configuration at the client boundary.

Configuration is read at call time from the shared ``scion_sdk.config``
settings layer. Secret values may be given inline or as ``env://`` / secret-store
references; references are resolved only here, at runtime:

* ``VAULTWARDEN_URL`` and the ``VAULTWARDEN_TLS_PROFILE`` / ``VAULTWARDEN_CA_BUNDLE_REF``
  family (``scion_sdk.tls``) -- the server and its trust;
* ``VAULTWARDEN_CLIENT_ID`` / ``VAULTWARDEN_CLIENT_SECRET`` -- the account's personal API key;
* ``VAULTWARDEN_MASTER_PASSWORD`` -- needed only for decrypted vault operations;
* ``VAULTWARDEN_ADMIN_TOKEN`` -- needed only for instance administration;
* ``VAULTWARDEN_CRYPTO_BACKEND`` -- ``native`` (default) or ``bw_cli``.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from scion_sdk.config import setting
from scion_sdk.credentials.resolution import resolve_secret_reference
from scion_sdk.exceptions import AuthError, UnauthorizedError
from scion_sdk.tls.profile import ResolvedTLSProfile
from scion_sdk.tls.resolve import resolve_tls_profile

from .api import VaultwardenApi, VaultwardenCredentials
from .crypto.base import VaultCrypto

PROVIDER = "vaultwarden"
_CREDENTIAL_KEYS = ("CLIENT_ID", "CLIENT_SECRET", "ADMIN_TOKEN", "MASTER_PASSWORD")

logger = logging.getLogger(__name__)
_client: VaultwardenApi | None = None
_provider_runtime: "ResolvedProviderRuntime | None" = None
_vault_crypto: VaultCrypto | None = None


@dataclass
class ResolvedProviderRuntime:
    """Endpoint, trust, credential values and selectors for one Vaultwarden server."""

    endpoint: str | None
    tls: ResolvedTLSProfile | None
    credentials: Mapping[str, str] = field(default_factory=dict)
    selectors: Mapping[str, str] = field(default_factory=dict)

    def close(self) -> None:
        """Release the TLS material this runtime materialized."""
        if self.tls is not None:
            self.tls.cleanup()
            self.tls = None


def _secret(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith(("env://", "openbao://")):
        return resolve_secret_reference(text)
    return text


def resolve_provider_runtime_profile() -> ResolvedProviderRuntime:
    """Build the runtime from ``VAULTWARDEN_*`` settings and the TLS profile."""
    credentials = {
        key: _secret(setting(f"VAULTWARDEN_{key}", "")) for key in _CREDENTIAL_KEYS
    }
    selectors = {"CRYPTO_BACKEND": str(setting("VAULTWARDEN_CRYPTO_BACKEND", "") or "")}
    endpoint = str(setting("VAULTWARDEN_URL", "") or "").strip() or None
    return ResolvedProviderRuntime(
        endpoint=endpoint,
        tls=resolve_tls_profile(PROVIDER) if endpoint else None,
        credentials=MappingProxyType(credentials),
        selectors=MappingProxyType(selectors),
    )


def _credentials(runtime: ResolvedProviderRuntime) -> VaultwardenCredentials:
    values = runtime.credentials
    return VaultwardenCredentials(
        client_id=values.get("CLIENT_ID") or None,
        client_secret=values.get("CLIENT_SECRET") or None,
        admin_token=values.get("ADMIN_TOKEN") or None,
    )


def get_client() -> VaultwardenApi:
    """Build one client from the ``VAULTWARDEN_*`` settings."""
    global _client, _provider_runtime
    if _client is not None:
        return _client

    runtime = resolve_provider_runtime_profile()
    if not runtime.endpoint or runtime.tls is None:
        runtime.close()
        raise RuntimeError("VAULTWARDEN_URL is required")

    import httpx
    from scion_sdk.auth.delegation import (
        DelegationSettings,
        current_user_token,
        exchange_token,
    )
    from scion_sdk.exceptions import LoginRequiredError

    # --- Path 1: OIDC Delegation (RFC 8693 Token Exchange) ---
    delegation_settings = DelegationSettings.from_settings()
    if delegation_settings.enabled:
        try:
            subject_token = current_user_token()
            if not subject_token:
                raise LoginRequiredError("no verified caller token to delegate")
            with httpx.Client(timeout=30) as http_client:
                access_token = exchange_token(
                    delegation_settings,
                    subject_token=subject_token,
                    http_client=http_client,
                )
            logger.info("Using OIDC delegated token")
            _client = VaultwardenApi(
                base_url=runtime.endpoint,
                tls_profile=runtime.tls,
                credentials=_credentials(runtime),
                token=access_token.value,
            )
            _provider_runtime = runtime
            return _client
        except Exception as e:
            runtime.close()
            logger.error(
                "OIDC delegation failed",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": type(e).__name__,
                },
            )
            raise RuntimeError(f"Token exchange failed: {type(e).__name__}") from e

    # --- Path 2: referenced personal API key ---
    logger.info("Using referenced API key credentials")
    try:
        _client = VaultwardenApi(
            base_url=runtime.endpoint,
            tls_profile=runtime.tls,
            credentials=_credentials(runtime),
        )
        _provider_runtime = runtime
    except (AuthError, UnauthorizedError) as e:
        runtime.close()
        raise RuntimeError(
            "AUTHENTICATION ERROR: The configured credentials were rejected. "
            "Check the VAULTWARDEN_CLIENT_ID / VAULTWARDEN_CLIENT_SECRET settings."
        ) from e
    except Exception as e:
        runtime.close()
        raise RuntimeError(
            "AUTHENTICATION ERROR: Failed to instantiate client. "
            f"Error details: {type(e).__name__}"
        ) from e

    return _client


def get_vault_crypto() -> VaultCrypto:
    """Return the unlocked-on-demand vault backend selected by ``VAULTWARDEN_CRYPTO_BACKEND``."""
    global _vault_crypto
    if _vault_crypto is not None:
        return _vault_crypto
    client = get_client()
    runtime = _provider_runtime
    if runtime is None:
        raise RuntimeError("Provider runtime is not available")
    values = runtime.credentials
    selectors: Any = runtime.selectors or {}
    backend = str(selectors.get("CRYPTO_BACKEND") or "native")
    if backend == "native":
        from .crypto.native import NativeVaultCrypto

        _vault_crypto = NativeVaultCrypto(
            client, master_password=values.get("MASTER_PASSWORD")
        )
    elif backend == "bw_cli":
        from .crypto.bw_cli import BwCliVaultCrypto

        _vault_crypto = BwCliVaultCrypto(
            server_url=client.base_url,
            master_password=values.get("MASTER_PASSWORD"),
            client_id=values.get("CLIENT_ID"),
            client_secret=values.get("CLIENT_SECRET"),
            ca_bundle_path=getattr(runtime.tls, "ca_bundle_path", None),
        )
    else:
        raise RuntimeError(f"Unsupported CRYPTO_BACKEND selector: {backend}")
    return _vault_crypto


def reset_clients() -> None:
    """Drop cached clients and key material (used on reconfiguration and in tests)."""
    global _client, _provider_runtime, _vault_crypto
    if _vault_crypto is not None:
        _vault_crypto.lock()
    if _provider_runtime is not None:
        _provider_runtime.close()
    _client = None
    _provider_runtime = None
    _vault_crypto = None
