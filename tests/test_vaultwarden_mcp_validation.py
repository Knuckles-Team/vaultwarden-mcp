import pytest

from scion_sdk.connector import build_server

# Typed tools that are not generated from an API route.
TYPED_TOOL_NAMES = {
    "vaultwarden_ciphers_list_items",
    "vaultwarden_folders_create_folder",
    "vaultwarden_maintenance_plan_deduplication",
    "vaultwarden_metadata_snapshot",
}


@pytest.mark.concept("VW-ECO.mcp.system-operations")
def test_mcp_instance_registration(monkeypatch):
    """MCP server instantiates with its tool domains registered.

    CONCEPT:VW-ECO.mcp.system-operations
    """
    monkeypatch.setattr("sys.argv", ["vaultwarden-mcp"])
    _, mcp = build_server("vaultwarden_mcp", command_args=[])
    assert mcp is not None


@pytest.mark.concept("VW-ECO.mcp.tool-surface-registration")
async def test_tool_surface_registered_per_operation(monkeypatch):
    """The default surface registers one typed tool per operation, none action-routed.

    CONCEPT:VW-ECO.mcp.tool-surface-registration
    """
    monkeypatch.setattr("sys.argv", ["vaultwarden-mcp"])
    _, mcp = build_server("vaultwarden_mcp", command_args=[])
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    missing = TYPED_TOOL_NAMES - names
    assert not missing, f"missing tools: {missing}"
    for tool in tools:
        assert "action" not in tool.parameters.get("properties", {}), tool.name
        assert "params_json" not in tool.parameters.get("properties", {}), tool.name
    assert len(names) > len(TYPED_TOOL_NAMES)
