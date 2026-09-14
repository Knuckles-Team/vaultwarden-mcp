# vaultwarden-mcp

Vaultwarden (Bitwarden-compatible) **API client + Bitwarden CLI wrapper + MCP Server +
A2A Agent** for the agent-utilities ecosystem — a typed, action-routed connector.

!!! info "Official documentation"
    This site is the canonical reference for `vaultwarden-mcp`, maintained alongside
    every release.

[![PyPI](https://img.shields.io/pypi/v/vaultwarden-mcp)](https://pypi.org/project/vaultwarden-mcp/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/vaultwarden-mcp)](https://github.com/Knuckles-Team/vaultwarden-mcp/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/vaultwarden-mcp)

## Overview

`vaultwarden-mcp` wraps a Vaultwarden server's 281 API operations, and its
decrypted-vault layer, with typed, deterministic MCP tools and an optional Pydantic-AI
agent server.

The connector remains inactive until `provider_configs.vaultwarden` resolves a
runtime endpoint, credential reference, and TLS profile through `AgentConfig`.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run local transports or connect through an authenticated TLS ingress.
- :material-console: **[Usage](usage.md)** — the MCP tools, the Python client, and the CLI.
- :material-database-cog: **[Backing Platform](platform.md)** — deploy Vaultwarden itself with Docker.
- :material-sitemap: **[Overview](overview.md)** — the action-routed tool surface and architecture.
- :material-graph: **[Concepts](concepts.md)** — the CONCEPT ID registry.

</div>
