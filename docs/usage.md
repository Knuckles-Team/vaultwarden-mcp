# Usage — API / CLI / MCP

`vaultwarden-mcp` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** you import, and as a **CLI**.

## Configuration

Configure `provider_configs.vaultwarden` in `AgentConfig` with an `endpoint_ref`, one
`tls_profile`/`tls_profile_ref`, `credential_refs` (upper-case `CLIENT_ID` /
`CLIENT_SECRET`, plus `MASTER_PASSWORD` for decrypted vault operations and
`ADMIN_TOKEN` for admin operations), and optionally
`selector_refs.CRYPTO_BACKEND` (`native` default, or `bw_cli`). Resolved values are
never written to configuration files — only references (`env://…`, `vault://…`,
`secret://…`).

## As a Python API

```python
from vaultwarden_mcp.auth import get_client, get_vault_crypto

client = get_client()          # resolves provider_configs.vaultwarden from AgentConfig

# Public, unauthenticated read:
print(client.server_version())

# A generated per-operation call, dispatched by route name:
profile = client.call_operation("profile")

# Or call the generated method directly:
profile = client.profile()

# Decrypted vault access (unlocks the selected crypto backend on demand):
vault = get_vault_crypto()
for item in vault.list_items():
    print(item["id"], item["type"], item["revisionDate"])
```

`call_operation(name, **params)` dispatches to any of the 281 generated operations in
`vaultwarden_mcp.api._routes.ROUTES` by name — the same dispatch the `verbose`
MCP tool surface and the action-routed domain tools use internally.

## As an MCP server

Once [deployed](deployment.md), the server registers eight action-routed tool domains
(`vaultwarden_system`, `vaultwarden_accounts`, `vaultwarden_ciphers`,
`vaultwarden_folders`, `vaultwarden_organizations`, `vaultwarden_sends`,
`vaultwarden_admin`, `vaultwarden_maintenance`). Each is independently togglable with a
`*TOOL` environment flag. Setting `MCP_TOOL_MODE=verbose` additionally registers one
fully-typed tool per API operation. Destructive tool actions require
`"confirm": true` in `params_json`.

## As a CLI

Configure `provider_configs.vaultwarden` with runtime-only endpoint and credential
references plus one TLS profile selector, then run `vaultwarden-mcp --transport stdio`.
