# CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `vaultwarden-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `vaultwarden_mcp` from it.
