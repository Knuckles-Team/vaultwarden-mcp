#!/usr/bin/python

"""Resolve reference-only provider configuration at the client boundary.

``provider_configs.vaultwarden`` in AgentConfig carries references only:

* ``endpoint_ref`` and ``tls_profile`` / ``tls_profile_ref`` — the server and its trust;
* ``credential_refs.CLIENT_ID`` / ``CLIENT_SECRET`` — the account's personal API key;
* ``credential_refs.MASTER_PASSWORD`` — needed only for decrypted vault operations;
* ``credential_refs.ADMIN_TOKEN`` — needed only for instance administration;
* ``selector_refs.CRYPTO_BACKEND`` — ``native`` (default) or ``bw_cli``.

Aliases are upper-case, as AgentConfig requires; values are ``env://`` or secret-store
references resolved only at runtime.
"""

import logging
from typing import Any

from agent_connector_sdk.exceptions import AuthError, UnauthorizedError

# No agent_connector_sdk equivalent for AgentConfig / provider_runtime profile
# resolution exists yet (SDK gap — see PR description); kept on agent_utilities.
from agent_utilities.core import config as config_module
from agent_utilities.core.provider_runtime import (
    ResolvedProviderRuntime,
    resolve_provider_runtime_profile,
)

from .api import VaultwardenApi, VaultwardenCredentials
from .crypto.base import VaultCrypto

PROVIDER = "vaultwarden"

logger = logging.getLogger(__name__)
_client: VaultwardenApi | None = None
_provider_runtime: ResolvedProviderRuntime | None = None
_vault_crypto: VaultCrypto | None = None


def _credentials(runtime: ResolvedProviderRuntime) -> VaultwardenCredentials:
    values = runtime.credentials
    return VaultwardenCredentials(
        client_id=values.get("CLIENT_ID") or None,
        client_secret=values.get("CLIENT_SECRET") or None,
        admin_token=values.get("ADMIN_TOKEN") or None,
    )


def get_client(config: config_module.AgentConfig | None = None) -> VaultwardenApi:
    """Build one client from ``provider_configs.vaultwarden`` in AgentConfig."""
    global _client, _provider_runtime
    if _client is not None:
        return _client

    active_config = config or config_module.AgentConfig()
    runtime = resolve_provider_runtime_profile(PROVIDER, config=active_config)
    if not runtime.endpoint or runtime.tls is None:
        runtime.close()
        raise RuntimeError("Provider profile requires endpoint and TLS references")

    import httpx
    from agent_connector_sdk.auth.delegation import (
        DelegationSettings,
        current_user_token,
        exchange_token,
    )
    from agent_connector_sdk.exceptions import LoginRequiredError

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
            "Check the provider profile's runtime references."
        ) from e
    except Exception as e:
        runtime.close()
        raise RuntimeError(
            "AUTHENTICATION ERROR: Failed to instantiate client. "
            f"Error details: {type(e).__name__}"
        ) from e

    return _client


def get_vault_crypto(config: config_module.AgentConfig | None = None) -> VaultCrypto:
    """Return the unlocked-on-demand vault backend selected by the provider profile."""
    global _vault_crypto
    if _vault_crypto is not None:
        return _vault_crypto
    client = get_client(config)
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
