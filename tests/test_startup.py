import importlib

import pytest


@pytest.mark.concept("VW-OS.init.mcp-server-startup")
def test_mcp_server_module_importable():
    """MCP server module imports cleanly at startup. CONCEPT:VW-OS.init.mcp-server-startup"""
    assert importlib.import_module("vaultwarden_mcp.mcp_server") is not None
