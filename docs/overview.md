# vaultwarden-mcp — Concept Overview

> **Category**: Integration | **Ecosystem Role**: MCP Server + A2A Agent
> Built on [`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities) — the unified AGI Harness.

## Description

Vaultwarden (Bitwarden-compatible) API client, Bitwarden CLI wrapper, and MCP Server +
A2A Agent for Agentic AI!

## Architecture

This project follows the standardized agent-package pattern:

- **Modular Design**: split into `api/` (HTTP transport, the 281-operation route
  catalog, and the generated verbose-tool parameter manifest), `crypto/` (pluggable
  decrypted-vault backends), `vault/` (deduplication), and `mcp/` (action-routed
  tool modules) for cleaner organization.
- **Dynamic Tool Registration**: eight action-routed dynamic tool tags — `system`,
  `accounts`, `ciphers`, `folders`, `organizations`, `sends`, `admin`, `maintenance` —
  strictly lowercase, each togglable with a `*TOOL` environment flag. Setting
  `MCP_TOOL_MODE=verbose` additionally exposes one fully-typed tool per API operation.
- **Two crypto backends behind one contract**: `native` (pure-Python Bitwarden key
  derivation and EncString handling) and `bw_cli` (delegates to an installed Bitwarden
  CLI), both implementing the same `VaultCrypto` protocol so higher-level operations —
  item read/write, deduplication — behave identically on either backend.
- **Metadata-only knowledge graph**: `kg_ingest.py` maps vault entities to typed OWL
  nodes without ever reading item names, usernames, passwords, notes, URIs, or keys.
- **A2A Agent Server**: a Pydantic-AI graph agent (console script `vaultwarden-agent`)
  that calls the MCP tool surface and exposes an AG-UI web interface.

## Concept Registry

This project implements or inherits the following ecosystem concepts. See
[Concepts](concepts.md) for the full, code-derived registry.

| Concept ID | Description | Source |
|:-----------|:------------|:-------|
| `VW-ECO.mcp.system-operations` | Action-routed system tag (liveness, version, config) | `vaultwarden-mcp` |
| `VW-OS.identity.provider-profile` | Reference-only `provider_configs.vaultwarden` profile, upper-case credential aliases | `vaultwarden-mcp` |
| `VW-OS.crypto.native-vault-crypto` | Pure-Python Bitwarden key derivation and EncString handling | `vaultwarden-mcp` |
| `VW-KG.ingest.metadata-only` | Vault contents never reach the knowledge graph | `vaultwarden-mcp` |
| `VW-ECO.vault.deduplication` | Exact/loose duplicate planning and bulk soft-delete apply | `vaultwarden-mcp` |
| `AU-KG.ontology.federation-provider-leg` | Ontology federation via the `agent_utilities.ontology_providers` entry point | `agent-utilities` (inherited) |
| `AU-KG.ingest.enterprise-source-extractor` | Native ingest primitive for enterprise-source connectors | `agent-utilities` (inherited) |
| `AU-ECO.mcp.tool-mode-standardization` | Shared `MCP_TOOL_MODE` (`intent`/`condensed`/`verbose`/`both`) surface | `agent-utilities` (inherited) |

> 📖 **Full Registry**: See [`agent-utilities/docs/overview.md`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/overview.md) for the complete 5-Pillar concept index.
