import pytest

from vaultwarden_mcp.mcp_server import get_mcp_instance

EXPECTED_TOOL_NAMES = {
    "vaultwarden_system",
    "vaultwarden_accounts",
    "vaultwarden_ciphers",
    "vaultwarden_folders",
    "vaultwarden_organizations",
    "vaultwarden_sends",
    "vaultwarden_admin",
    "vaultwarden_maintenance",
}


@pytest.mark.concept("VW-ECO.mcp.system-operations")
def test_mcp_instance_registration(monkeypatch):
    """MCP server instantiates with its tool domains registered.

    CONCEPT:VW-ECO.mcp.system-operations
    """
    monkeypatch.setattr("sys.argv", ["vaultwarden-mcp"])
    mcp, args, middlewares = get_mcp_instance()
    assert mcp is not None


@pytest.mark.concept("VW-ECO.mcp.tool-surface-registration")
async def test_all_eight_intent_tools_registered(monkeypatch):
    """Every one of the eight intent tools registers under the default mode.

    CONCEPT:VW-ECO.mcp.tool-surface-registration
    """
    monkeypatch.setattr("sys.argv", ["vaultwarden-mcp"])
    mcp, _args, _middlewares = get_mcp_instance()
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    missing = EXPECTED_TOOL_NAMES - names
    assert not missing, f"missing tools: {missing}"
