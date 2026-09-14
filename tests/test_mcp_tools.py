import sys
import types
from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP

from vaultwarden_mcp.mcp.mcp_accounts import register_accounts_tools
from vaultwarden_mcp.mcp.mcp_admin import register_admin_tools
from vaultwarden_mcp.mcp.mcp_ciphers import register_ciphers_tools
from vaultwarden_mcp.mcp.mcp_folders import register_folders_tools
from vaultwarden_mcp.mcp.mcp_maintenance import register_maintenance_tools
from vaultwarden_mcp.mcp.mcp_organizations import register_organizations_tools
from vaultwarden_mcp.mcp.mcp_sends import register_sends_tools


async def _tool_fn(register_fn, tool_name: str):
    """Return the tool's raw coroutine, called with ``ctx`` defaulted to None.

    Calling ``tool.fn`` directly bypasses FastMCP's argument resolution, so an
    omitted keyword keeps its literal ``Field(...)`` default (a ``FieldInfo``)
    rather than the ``None``/``Context`` FastMCP would inject at request time.
    """
    mcp = FastMCP("test")
    register_fn(mcp)
    tool = await mcp.get_tool(tool_name)
    assert tool is not None, f"{tool_name} did not register"
    raw = tool.fn

    async def call(**kwargs):
        kwargs.setdefault("ctx", None)
        return await raw(**kwargs)

    return call


def _client() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# accounts / two_factor / emergency_access / events — route dispatch
# ---------------------------------------------------------------------------


@pytest.mark.concept("VW-ECO.mcp.account-operations")
class TestAccounts:
    async def test_list_actions_discovery(self):
        fn = await _tool_fn(register_accounts_tools, "vaultwarden_accounts")
        result = await fn(action="list_actions", params_json="{}", client=_client())
        assert result["service"] == "vaultwarden-mcp"
        assert "profile" in result["actions"]

    async def test_unknown_action_raises(self):
        fn = await _tool_fn(register_accounts_tools, "vaultwarden_accounts")
        with pytest.raises(ValueError, match="Unknown action"):
            await fn(action="not_a_real_action", params_json="{}", client=_client())

    async def test_invalid_params_json(self):
        fn = await _tool_fn(register_accounts_tools, "vaultwarden_accounts")
        result = await fn(action="profile", params_json="{not json", client=_client())
        assert "error" in result

    async def test_route_dispatch_with_params(self):
        fn = await _tool_fn(register_accounts_tools, "vaultwarden_accounts")
        client = _client()
        client.call_operation.return_value = {"id": "device-1"}
        result = await fn(
            action="get_device",
            params_json='{"device_id": "device-1"}',
            client=client,
        )
        assert result == {"id": "device-1"}
        client.call_operation.assert_called_once_with(
            "get_device", device_id="device-1"
        )


# ---------------------------------------------------------------------------
# organizations / public / misc, sends — route dispatch
# ---------------------------------------------------------------------------


@pytest.mark.concept("VW-ECO.mcp.organization-operations")
async def test_organizations_route_dispatch():
    fn = await _tool_fn(register_organizations_tools, "vaultwarden_organizations")
    client = _client()
    client.call_operation.return_value = {"id": "org-1"}
    result = await fn(
        action="get_organization", params_json='{"org_id": "org-1"}', client=client
    )
    assert result == {"id": "org-1"}
    client.call_operation.assert_called_once_with("get_organization", org_id="org-1")


@pytest.mark.concept("VW-ECO.mcp.send-operations")
async def test_sends_destructive_gate():
    fn = await _tool_fn(register_sends_tools, "vaultwarden_sends")
    client = _client()

    refused = await fn(
        action="delete_send", params_json='{"send_id": "s1"}', client=client
    )
    assert refused["confirm_required"] is True
    client.call_operation.assert_not_called()

    client.call_operation.return_value = {"status": 200}
    confirmed = await fn(
        action="delete_send",
        params_json='{"send_id": "s1", "confirm": true}',
        client=client,
    )
    assert confirmed == {"status": 200}
    client.call_operation.assert_called_once_with("delete_send", send_id="s1")


# ---------------------------------------------------------------------------
# ciphers — decrypted CRUD, move_to_trash, destructive route gate
# ---------------------------------------------------------------------------


@pytest.mark.concept("VW-ECO.mcp.cipher-operations")
class TestCiphers:
    async def test_list_items(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        crypto = MagicMock()
        crypto.list_items.return_value = [{"id": "i1"}]
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_ciphers.get_vault_crypto", lambda: crypto
        )
        result = await fn(action="list_items", params_json="{}", client=_client())
        assert result == {"items": [{"id": "i1"}]}
        crypto.list_items.assert_called_once_with(include_trash=False)

    async def test_get_item_requires_item_id(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        result = await fn(action="get_item", params_json="{}", client=_client())
        assert "error" in result

    async def test_get_item(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        crypto = MagicMock()
        crypto.get_item.return_value = {"id": "i1", "name": "example"}
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_ciphers.get_vault_crypto", lambda: crypto
        )
        result = await fn(
            action="get_item", params_json='{"item_id": "i1"}', client=_client()
        )
        assert result == {"item": {"id": "i1", "name": "example"}}
        crypto.get_item.assert_called_once_with("i1")

    async def test_create_item(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        crypto = MagicMock()
        crypto.create_item.return_value = {"id": "i2"}
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_ciphers.get_vault_crypto", lambda: crypto
        )
        item = {"type": 1, "name": "n"}
        result = await fn(
            action="create_item",
            params_json='{"item": {"type": 1, "name": "n"}}',
            client=_client(),
        )
        assert result == {"item": {"id": "i2"}}
        crypto.create_item.assert_called_once_with(item)

    async def test_edit_item(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        crypto = MagicMock()
        crypto.edit_item.return_value = {"id": "i1", "name": "renamed"}
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_ciphers.get_vault_crypto", lambda: crypto
        )
        result = await fn(
            action="edit_item",
            params_json='{"item_id": "i1", "item": {"name": "renamed"}}',
            client=_client(),
        )
        assert result == {"item": {"id": "i1", "name": "renamed"}}
        crypto.edit_item.assert_called_once_with("i1", {"name": "renamed"})

    async def test_move_to_trash(self):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        client = _client()
        client.soft_delete_ciphers.return_value = {"status": 200}
        result = await fn(
            action="move_to_trash", params_json='{"ids": ["a", "b"]}', client=client
        )
        assert result == {"trashed": 2, "result": {"status": 200}}
        client.soft_delete_ciphers.assert_called_once_with(["a", "b"])

    async def test_move_to_trash_requires_ids(self):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        result = await fn(action="move_to_trash", params_json="{}", client=_client())
        assert "error" in result

    async def test_destructive_route_requires_confirm(self):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers")
        client = _client()

        refused = await fn(
            action="delete_cipher",
            params_json='{"cipher_id": "c1"}',
            client=client,
        )
        assert refused == {
            "confirm_required": True,
            "action": "delete_cipher",
            "message": refused["message"],
        }
        client.call_operation.assert_not_called()

        client.call_operation.return_value = {"status": 200}
        confirmed = await fn(
            action="delete_cipher",
            params_json='{"cipher_id": "c1", "confirm": true}',
            client=client,
        )
        assert confirmed == {"status": 200}
        client.call_operation.assert_called_once_with("delete_cipher", cipher_id="c1")


# ---------------------------------------------------------------------------
# folders — decrypted CRUD plus raw routes
# ---------------------------------------------------------------------------


@pytest.mark.concept("VW-ECO.mcp.folder-operations")
class TestFolders:
    async def test_list_folders(self, monkeypatch):
        fn = await _tool_fn(register_folders_tools, "vaultwarden_folders")
        crypto = MagicMock()
        crypto.list_folders.return_value = [{"id": "f1", "name": "Work"}]
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_folders.get_vault_crypto", lambda: crypto
        )
        result = await fn(action="list_folders", params_json="{}", client=_client())
        assert result == {"folders": [{"id": "f1", "name": "Work"}]}

    async def test_create_folder_requires_name(self):
        fn = await _tool_fn(register_folders_tools, "vaultwarden_folders")
        result = await fn(action="create_folder", params_json="{}", client=_client())
        assert "error" in result

    async def test_create_folder(self, monkeypatch):
        fn = await _tool_fn(register_folders_tools, "vaultwarden_folders")
        crypto = MagicMock()
        crypto.create_folder.return_value = {"id": "f2", "name": "New"}
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_folders.get_vault_crypto", lambda: crypto
        )
        result = await fn(
            action="create_folder", params_json='{"name": "New"}', client=_client()
        )
        assert result == {"folder": {"id": "f2", "name": "New"}}
        crypto.create_folder.assert_called_once_with("New")

    async def test_raw_route_dispatch(self):
        fn = await _tool_fn(register_folders_tools, "vaultwarden_folders")
        client = _client()
        client.call_operation.return_value = [{"id": "f1"}]
        result = await fn(action="get_folders", params_json="{}", client=client)
        assert result == [{"id": "f1"}]
        client.call_operation.assert_called_once_with("get_folders")


# ---------------------------------------------------------------------------
# admin — error surfacing when the admin token is rejected/missing
# ---------------------------------------------------------------------------


@pytest.mark.concept("VW-ECO.mcp.admin-operations")
async def test_admin_surfaces_api_error():
    from vaultwarden_mcp.api.api_client_base import VaultwardenApiError

    fn = await _tool_fn(register_admin_tools, "vaultwarden_admin")
    client = _client()
    client.call_operation.side_effect = VaultwardenApiError(
        401, "an admin token is required"
    )
    result = await fn(action="get_users_json", params_json="{}", client=client)
    assert result == {"error": "an admin token is required", "status": 401}


@pytest.mark.concept("VW-ECO.mcp.admin-operations")
async def test_admin_route_dispatch():
    fn = await _tool_fn(register_admin_tools, "vaultwarden_admin")
    client = _client()
    client.call_operation.return_value = [{"id": "u1"}]
    result = await fn(action="get_users_json", params_json="{}", client=client)
    assert result == [{"id": "u1"}]


# ---------------------------------------------------------------------------
# maintenance — dedupe plan/apply, rotate, generate, ingest
# ---------------------------------------------------------------------------


def _dup_items():
    return [
        {
            "id": "keep",
            "type": 1,
            "name": "Example",
            "revisionDate": "2026-01-02T00:00:00Z",
            "login": {"username": "alice", "password": "p", "uris": []},
        },
        {
            "id": "drop",
            "type": 1,
            "name": "Example",
            "revisionDate": "2026-01-01T00:00:00Z",
            "login": {"username": "alice", "password": "p", "uris": []},
        },
    ]


@pytest.mark.concept("VW-ECO.mcp.maintenance-operations")
class TestMaintenance:
    async def test_generate_password(self):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        result = await fn(
            action="generate_password", params_json="{}", client=_client()
        )
        assert len(result["password"]) == 24

    async def test_plan_deduplication_ids_only(self, monkeypatch):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        crypto = MagicMock()
        crypto.list_items.return_value = _dup_items()
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_maintenance.get_vault_crypto", lambda: crypto
        )
        result = await fn(
            action="plan_deduplication", params_json="{}", client=_client()
        )
        assert result["duplicate_groups"] == 1
        assert result["extra_copies"] == 1
        blob = str(result)
        assert "Example" not in blob
        assert "alice" not in blob
        assert "keep" in blob and "drop" in blob

    async def test_apply_deduplication_requires_confirm(self, monkeypatch):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        crypto = MagicMock()
        crypto.list_items.return_value = _dup_items()
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_maintenance.get_vault_crypto", lambda: crypto
        )
        client = _client()
        result = await fn(action="apply_deduplication", params_json="{}", client=client)
        assert result["confirm_required"] is True
        client.soft_delete_ciphers.assert_not_called()

    async def test_apply_deduplication_refuses_loose(self, monkeypatch):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        crypto = MagicMock()
        crypto.list_items.return_value = _dup_items()
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_maintenance.get_vault_crypto", lambda: crypto
        )
        client = _client()
        result = await fn(
            action="apply_deduplication",
            params_json='{"loose": true, "confirm": true}',
            client=client,
        )
        assert "error" in result
        client.soft_delete_ciphers.assert_not_called()

    async def test_apply_deduplication(self, monkeypatch):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        crypto = MagicMock()
        crypto.list_items.return_value = _dup_items()
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_maintenance.get_vault_crypto", lambda: crypto
        )
        client = _client()
        client.soft_delete_ciphers.return_value = {"status": 200}
        result = await fn(
            action="apply_deduplication",
            params_json='{"confirm": true}',
            client=client,
        )
        assert result == {"trashed": 1, "duplicate_groups": 1}
        client.soft_delete_ciphers.assert_called_once_with(["drop"])

    async def test_rotate_password_requires_confirm(self, monkeypatch):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        crypto = MagicMock()
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_maintenance.get_vault_crypto", lambda: crypto
        )
        result = await fn(
            action="rotate_password",
            params_json='{"item_id": "i1"}',
            client=_client(),
        )
        assert result["confirm_required"] is True
        crypto.get_item.assert_not_called()

    async def test_rotate_password_requires_item_id(self):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        result = await fn(action="rotate_password", params_json="{}", client=_client())
        assert "error" in result

    async def test_rotate_password(self, monkeypatch):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        crypto = MagicMock()
        crypto.get_item.return_value = {
            "id": "i1",
            "type": 1,
            "login": {"username": "alice", "password": "old"},
            "passwordHistory": [],
        }
        monkeypatch.setattr(
            "vaultwarden_mcp.mcp.mcp_maintenance.get_vault_crypto", lambda: crypto
        )
        result = await fn(
            action="rotate_password",
            params_json='{"item_id": "i1", "confirm": true}',
            client=_client(),
        )
        assert result["item_id"] == "i1"
        assert result["rotated"] is True
        assert "password" not in str(result).lower().replace("passwordHistory", "")
        assert "password" not in result

    async def test_ingest_metadata_calls_mappers(self, monkeypatch):
        fake_kg_ingest = types.ModuleType("vaultwarden_mcp.kg_ingest")
        fake_kg_ingest.ingest_items = MagicMock(return_value={"nodes": 1, "edges": 0})
        fake_kg_ingest.ingest_folders = MagicMock(return_value={"nodes": 1})
        fake_kg_ingest.ingest_collections = MagicMock(return_value={"nodes": 1})
        fake_kg_ingest.ingest_server = MagicMock(return_value={"nodes": 1})
        monkeypatch.setitem(sys.modules, "vaultwarden_mcp.kg_ingest", fake_kg_ingest)

        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        client = _client()
        client.sync_vault.return_value = {
            "ciphers": [{"id": "c1"}],
            "folders": [{"id": "f1"}],
            "collections": [{"id": "col1"}],
        }
        client.server_config.return_value = {"gitHash": "abc"}
        client.server_version.return_value = "1.37.3"

        result = await fn(action="ingest_metadata", params_json="{}", client=client)
        assert result["synced"] is True
        assert result["counts"] == {
            "items": 1,
            "folders": 1,
            "collections": 1,
            "server": 1,
        }
        fake_kg_ingest.ingest_items.assert_called_once_with([{"id": "c1"}])
        fake_kg_ingest.ingest_folders.assert_called_once_with(["f1"])
        fake_kg_ingest.ingest_collections.assert_called_once_with([{"id": "col1"}])
        fake_kg_ingest.ingest_server.assert_called_once_with(
            {"gitHash": "abc"}, server_version="1.37.3"
        )

    async def test_unknown_action(self):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_maintenance")
        with pytest.raises(ValueError, match="Unknown action"):
            await fn(action="not_real", params_json="{}", client=_client())
