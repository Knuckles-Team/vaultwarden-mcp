# Installation

`vaultwarden-mcp` is a standard Python package and a prebuilt container image.

## Requirements

- **Python 3.12–3.14**.
- A provider profile in `AgentConfig` containing endpoint, credential, and TLS references
  (see [Usage](usage.md#configuration)).
- A reachable Vaultwarden (or upstream Bitwarden-compatible) server. See
  [Backing Platform](platform.md) for a local recipe.

## From PyPI (recommended)

```bash
pip install vaultwarden-mcp
```

### Optional extras

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "vaultwarden-mcp[mcp]"` | MCP runtime + mandatory `epistemic-graph[full]` |
| `agent` | `pip install "vaultwarden-mcp[agent]"` | Current agent runtime + Logfire tracing |
| `all` | `pip install "vaultwarden-mcp[all]"` | Everything above |

### Console scripts

| Command | Description |
|---|---|
| `vaultwarden-mcp` | Launch the MCP server |
| `vaultwarden-agent` | Launch the A2A agent server |

### Optional: the Bitwarden CLI

Installing the `bw_cli` crypto backend (`selector_refs.CRYPTO_BACKEND=bw_cli`) requires a
Bitwarden CLI binary (`bw`) reachable on `PATH`; it is not a Python dependency and is not
installed by any extra above. The default `native` backend needs no external binary.

## From source

```bash
git clone https://github.com/Knuckles-Team/vaultwarden-mcp.git
cd vaultwarden-mcp
pip install -e ".[all]"
```

## Docker

```bash
IMAGE_REF='<registry>/vaultwarden-mcp@sha256:<digest>'
docker pull "$IMAGE_REF"
```

See [Deployment](deployment.md) for `docker run` / Compose usage. The repository's
`README.md` documents the `:mcp` vs `:agent` build targets for the multi-stage
`docker/Dockerfile`.
