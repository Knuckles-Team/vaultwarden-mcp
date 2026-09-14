# Deployment

This page covers running `vaultwarden-mcp` as long-lived servers.

> `vaultwarden-mcp` ships both an **MCP server** (console script `vaultwarden-mcp`) and an
> **A2A agent server** (console script `vaultwarden-agent`).

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`vaultwarden-mcp` exposes its MCP server (console script `vaultwarden-mcp`) four ways. Pick the
row that matches where the server runs relative to your MCP client, then copy the
matching `mcp_config.json` below.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container | `stdio` | reviewed Docker / Podman image on this host | `command` |
| 4 | Remote URL | `streamable-http` | operator-owned authenticated TLS ingress | `url` |

### 1. stdio (local subprocess)

```json
{
  "mcpServers": {
    "vaultwarden-mcp": {
      "command": "vaultwarden-mcp",
      "args": [],
      "env": {
        "MCP_TOOL_MODE": "intent"
      }
    }
  }
}
```

### 2. Streamable-HTTP (local process)

```bash
vaultwarden-mcp --transport streamable-http --host 127.0.0.1 --port 8000
curl -s http://loopback.invalid:8000/health        # {"status":"OK"}
```

Connect to the running process by URL:

```json
{
  "mcpServers": {
    "vaultwarden-mcp": { "url": "http://loopback.invalid:8000/mcp" }
  }
}
```

### 3. Local container

Launch a container directly from `mcp_config.json` (swap `docker` for `podman` for a
daemonless runtime):

```json
{
  "mcpServers": {
    "vaultwarden-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--read-only", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=256",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m",
        "-e", "TRANSPORT=stdio",
        "<registry>/vaultwarden-mcp@sha256:<digest>"
      ]
    }
  }
}
```

Supply the provider profile through the operator-owned AgentConfig mount or secret
projection. The image and this document contain no endpoint, credential, or trust material.

### 4. Remote URL (authenticated TLS ingress)

When the server is deployed remotely, connect through its operator-supplied
authenticated HTTPS ingress; no local process or image is required:

```json
{
  "mcpServers": {
    "vaultwarden-mcp": { "url": "https://service.example.invalid/mcp" }
  }
}
```

Configure outbound MCP identity and trust references in `AgentConfig`. The server
must use direct TLS or an explicitly trusted TLS-terminating ingress and an exact
`MCP_ALLOWED_HOSTS` policy; do not commit the endpoint, credentials, or trust paths.
<!-- END GENERATED: deployment-options -->

## Docker Compose

Set `VAULTWARDEN_MCP_IMAGE` (and `VAULTWARDEN_AGENT_IMAGE` for the agent stack),
`AUTH_TYPE`, and `AGENT_CONFIG_DIR` (see `.env.example`) before running either file —
both required references have no default:

```bash
docker compose -f docker/mcp.compose.yml up -d      # MCP server only
docker compose -f docker/agent.compose.yml up -d    # MCP + agent
```

## Run the A2A agent server

```bash
vaultwarden-agent --mcp-config mcp_config.json --web
```
