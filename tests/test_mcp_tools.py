import json
from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP

from vaultwarden_mcp.mcp.mcp_ciphers import register_ciphers_tools
from vaultwarden_mcp.mcp.mcp_folders import register_folders_tools
from vaultwarden_mcp.mcp.mcp_maintenance import register_maintenance_tools


async def _tool_fn(register_fn, tool_name: str):
    """Return the tool's raw coroutine, called with ``ctx`` defaulted to None.

    Calling ``tool.fn`` directly bypasses FastMCP's argument resolution, so an
    omitted keyword keeps its literal ``Field(...)`` default; tests pass every
    argument they depend on.
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


def _patch_crypto(monkeypatch, module: str, crypto) -> None:
    monkeypatch.setattr(f"vaultwarden_mcp.mcp.{module}.get_vault_crypto", lambda: crypto)


@pytest.mark.concept("VW-ECO.mcp.cipher-operations")
class TestCiphers:
    async def test_list_items(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers_list_items")
        crypto = MagicMock()
        crypto.list_items.return_value = [{"id": "i1"}]
        _patch_crypto(monkeypatch, "mcp_ciphers", crypto)
        result = await fn(include_trash=False)
        assert result == {"items": [{"id": "i1"}]}
        crypto.list_items.assert_called_once_with(include_trash=False)

    async def test_get_item(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers_get_item")
        crypto = MagicMock()
        crypto.get_item.return_value = {"id": "i1", "name": "example"}
        _patch_crypto(monkeypatch, "mcp_ciphers", crypto)
        result = await fn(item_id="i1")
        assert result == {"item": {"id": "i1", "name": "example"}}
        crypto.get_item.assert_called_once_with("i1")

    async def test_create_item(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers_create_item")
        crypto = MagicMock()
        crypto.create_item.return_value = {"id": "i2"}
        _patch_crypto(monkeypatch, "mcp_ciphers", crypto)
        item = {"type": 1, "name": "n"}
        result = await fn(item=item)
        assert result == {"item": {"id": "i2"}}
        crypto.create_item.assert_called_once_with(item)

    async def test_edit_item(self, monkeypatch):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers_edit_item")
        crypto = MagicMock()
        crypto.edit_item.return_value = {"id": "i1", "name": "renamed"}
        _patch_crypto(monkeypatch, "mcp_ciphers", crypto)
        result = await fn(item_id="i1", item={"name": "renamed"})
        assert result == {"item": {"id": "i1", "name": "renamed"}}
        crypto.edit_item.assert_called_once_with("i1", {"name": "renamed"})

    async def test_move_to_trash(self):
        fn = await _tool_fn(register_ciphers_tools, "vaultwarden_ciphers_move_to_trash")
        client = _client()
        client.soft_delete_ciphers.return_value = {"status": 200}
        result = await fn(ids=["a", "b"], client=client)
        assert result == {"trashed": 2, "result": {"status": 200}}
        client.soft_delete_ciphers.assert_called_once_with(["a", "b"])


@pytest.mark.concept("VW-ECO.mcp.folder-operations")
class TestFolders:
    async def test_list_folders(self, monkeypatch):
        fn = await _tool_fn(register_folders_tools, "vaultwarden_folders_list_folders")
        crypto = MagicMock()
        crypto.list_folders.return_value = [{"id": "f1", "name": "Work"}]
        _patch_crypto(monkeypatch, "mcp_folders", crypto)
        assert await fn() == {"folders": [{"id": "f1", "name": "Work"}]}

    async def test_create_folder(self, monkeypatch):
        fn = await _tool_fn(register_folders_tools, "vaultwarden_folders_create_folder")
        crypto = MagicMock()
        crypto.create_folder.return_value = {"id": "f2", "name": "New"}
        _patch_crypto(monkeypatch, "mcp_folders", crypto)
        result = await fn(name="New")
        assert result == {"folder": {"id": "f2", "name": "New"}}
        crypto.create_folder.assert_called_once_with("New")


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


def _dup_crypto(monkeypatch):
    crypto = MagicMock()
    crypto.list_items.return_value = _dup_items()
    _patch_crypto(monkeypatch, "mcp_maintenance", crypto)
    return crypto


@pytest.mark.concept("VW-ECO.mcp.maintenance-operations")
class TestMaintenance:
    async def test_generate_password(self):
        fn = await _tool_fn(
            register_maintenance_tools, "vaultwarden_maintenance_generate_password"
        )
        result = await fn(length=24, use_symbols=True)
        assert len(result["password"]) == 24

    async def test_plan_deduplication_ids_only(self, monkeypatch):
        fn = await _tool_fn(
            register_maintenance_tools, "vaultwarden_maintenance_plan_deduplication"
        )
        _dup_crypto(monkeypatch)
        result = await fn(loose=False, include_org=False)
        assert result["duplicate_groups"] == 1
        assert result["extra_copies"] == 1
        blob = str(result)
        assert "Example" not in blob
        assert "alice" not in blob
        assert "keep" in blob and "drop" in blob

    async def test_apply_deduplication_requires_confirm(self, monkeypatch):
        fn = await _tool_fn(
            register_maintenance_tools, "vaultwarden_maintenance_apply_deduplication"
        )
        _dup_crypto(monkeypatch)
        client = _client()
        result = await fn(include_org=False, confirm=False, client=client)
        assert result["confirm_required"] is True
        client.soft_delete_ciphers.assert_not_called()

    async def test_apply_deduplication(self, monkeypatch):
        fn = await _tool_fn(
            register_maintenance_tools, "vaultwarden_maintenance_apply_deduplication"
        )
        _dup_crypto(monkeypatch)
        client = _client()
        client.soft_delete_ciphers.return_value = {"status": 200}
        result = await fn(include_org=False, confirm=True, client=client)
        assert result == {"trashed": 1, "duplicate_groups": 1}
        client.soft_delete_ciphers.assert_called_once_with(["drop"])

    async def test_rotate_password_requires_confirm(self, monkeypatch):
        fn = await _tool_fn(
            register_maintenance_tools, "vaultwarden_maintenance_rotate_password"
        )
        crypto = MagicMock()
        _patch_crypto(monkeypatch, "mcp_maintenance", crypto)
        result = await fn(item_id="i1", length=24, use_symbols=True, confirm=False)
        assert result["confirm_required"] is True
        crypto.get_item.assert_not_called()

    async def test_rotate_password(self, monkeypatch):
        fn = await _tool_fn(
            register_maintenance_tools, "vaultwarden_maintenance_rotate_password"
        )
        crypto = MagicMock()
        crypto.get_item.return_value = {
            "id": "i1",
            "type": 1,
            "login": {"username": "alice", "password": "old"},
            "passwordHistory": [],
        }
        _patch_crypto(monkeypatch, "mcp_maintenance", crypto)
        result = await fn(item_id="i1", length=24, use_symbols=True, confirm=True)
        assert result["item_id"] == "i1"
        assert result["rotated"] is True
        assert "password" not in result

    async def test_metadata_snapshot_serves_the_certified_projection(self):
        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_metadata_snapshot")
        client = _client()
        client.sync_vault.return_value = {
            "ciphers": [
                {
                    "id": "c1",
                    "type": 1,
                    "name": "must-not-cross",
                    "notes": "must-not-cross",
                    "revisionDate": "2026-09-14T00:00:00Z",
                    "login": {
                        "username": "must-not-cross",
                        "password": "must-not-cross",
                        "uris": [{"uri": "https://must-not-cross.invalid"}],
                    },
                    "folderId": "f1",
                    "organizationId": "org1",
                    "collectionIds": ["col1"],
                }
            ],
            "folders": [{"id": "f1", "name": "must-not-cross"}],
            "collections": [
                {"id": "col1", "organizationId": "org1", "name": "must-not-cross"}
            ],
        }
        client.server_config.return_value = {
            "gitHash": "abc",
            "environment": {"adminToken": "must-not-cross"},
        }
        client.server_version.return_value = "1.37.3"

        result = await fn(mode="delta", checkpoint="2026-09-13T00:00:00Z", client=client)

        assert result["contract"] == "vaultwarden.metadata-entities/v1"
        assert result["mode"] == "delta"
        assert result["entities"]
        assert result["relationships"]
        assert result["reconcile"] == {"authoritative": False, "live_ids": []}
        assert result["backfeed"] == {"supported": False, "mode": "read_only"}
        rendered = json.dumps(result)
        assert "must-not-cross" not in rendered
        for forbidden in ("name", "notes", "username", "password", "uris"):
            assert f'"{forbidden}"' not in rendered

    async def test_metadata_backfeed_refuses(self):
        from vaultwarden_mcp.kg_ingest import MetadataProjectionError

        fn = await _tool_fn(register_maintenance_tools, "vaultwarden_metadata_backfeed")
        with pytest.raises(MetadataProjectionError, match=r"unsupported.*read-only"):
            await fn()

    async def test_surface_has_no_action_routed_tool(self):
        mcp = FastMCP("test")
        register_maintenance_tools(mcp)
        register_ciphers_tools(mcp)
        register_folders_tools(mcp)
        for tool in await mcp.list_tools():
            assert "action" not in tool.parameters.get("properties", {})
            assert "params_json" not in tool.parameters.get("properties", {})
