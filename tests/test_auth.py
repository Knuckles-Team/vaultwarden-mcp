from types import MappingProxyType
from unittest.mock import MagicMock, patch

import pytest

import vaultwarden_mcp.auth as auth_module
from vaultwarden_mcp.auth import get_client, get_vault_crypto, reset_clients


@pytest.fixture(autouse=True)
def _fresh_clients():
    auth_module._client = None
    auth_module._provider_runtime = None
    auth_module._vault_crypto = None
    yield
    auth_module._client = None
    auth_module._provider_runtime = None
    auth_module._vault_crypto = None


def _runtime(**credentials):
    runtime = MagicMock()
    runtime.endpoint = "https://vault.example.invalid"
    runtime.credentials = MappingProxyType(credentials)
    runtime.selectors = MappingProxyType({})
    return runtime


def _no_delegation():
    return patch(
        "agent_utilities.mcp.delegated_auth.is_delegation_enabled", return_value=False
    )


def test_get_client_passes_referenced_credentials():
    runtime = _runtime(CLIENT_ID="user.1", CLIENT_SECRET="s", ADMIN_TOKEN="a")
    with (
        patch(
            "vaultwarden_mcp.auth.resolve_provider_runtime_profile",
            return_value=runtime,
        ),
        _no_delegation(),
        patch("vaultwarden_mcp.auth.VaultwardenApi") as client_cls,
    ):
        get_client()
    kwargs = client_cls.call_args.kwargs
    assert kwargs["base_url"] == runtime.endpoint
    assert kwargs["credentials"].client_id == "user.1"
    assert kwargs["credentials"].admin_token == "a"


def test_get_client_auth_error_closes_the_runtime():
    runtime = _runtime(CLIENT_ID="user.1")
    with (
        patch(
            "vaultwarden_mcp.auth.resolve_provider_runtime_profile",
            return_value=runtime,
        ),
        _no_delegation(),
        patch("vaultwarden_mcp.auth.VaultwardenApi", side_effect=Exception("boom")),
        pytest.raises(RuntimeError, match="AUTHENTICATION ERROR"),
    ):
        get_client()
    runtime.close.assert_called_once()


def test_missing_endpoint_is_rejected():
    runtime = _runtime()
    runtime.endpoint = None
    with (
        patch(
            "vaultwarden_mcp.auth.resolve_provider_runtime_profile",
            return_value=runtime,
        ),
        pytest.raises(RuntimeError, match="endpoint"),
    ):
        get_client()


def test_native_backend_requires_a_master_password():
    runtime = _runtime(CLIENT_ID="user.1", CLIENT_SECRET="s")
    with (
        patch(
            "vaultwarden_mcp.auth.resolve_provider_runtime_profile",
            return_value=runtime,
        ),
        _no_delegation(),
        patch("vaultwarden_mcp.auth.VaultwardenApi"),
        pytest.raises(ValueError, match="master_password"),
    ):
        get_vault_crypto()


def test_unknown_backend_selector_is_rejected():
    runtime = _runtime(MASTER_PASSWORD="pw")
    runtime.selectors = MappingProxyType({"CRYPTO_BACKEND": "mystery"})
    with (
        patch(
            "vaultwarden_mcp.auth.resolve_provider_runtime_profile",
            return_value=runtime,
        ),
        _no_delegation(),
        patch("vaultwarden_mcp.auth.VaultwardenApi"),
        pytest.raises(RuntimeError, match="CRYPTO_BACKEND"),
    ):
        get_vault_crypto()


def test_reset_locks_and_closes():
    crypto = MagicMock()
    runtime = MagicMock()
    auth_module._vault_crypto = crypto
    auth_module._provider_runtime = runtime
    reset_clients()
    crypto.lock.assert_called_once()
    runtime.close.assert_called_once()
