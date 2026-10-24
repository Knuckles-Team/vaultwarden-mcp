import pytest

from agent_connector_sdk.connector import build_server

# Domains whose action-routed tool the SDK keeps whole (its actions cannot be enumerated).
ROUTED_TOOL_NAMES = {
    "vaultwarden_accounts",
    "vaultwarden_organizations",
    "vaultwarden_sends",
    "vaultwarden_admin",
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
    """The default surface registers per-operation tools plus the routed domain tools.

    CONCEPT:VW-ECO.mcp.tool-surface-registration
    """
    monkeypatch.setattr("sys.argv", ["vaultwarden-mcp"])
    _, mcp = build_server("vaultwarden_mcp", command_args=[])
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    missing = ROUTED_TOOL_NAMES - names
    assert not missing, f"missing tools: {missing}"
    assert any(
        n.startswith("vaultwarden_ciphers_") for n in names
    ), "ciphers split into per-operation tools"
    assert len(names) > len(ROUTED_TOOL_NAMES)
