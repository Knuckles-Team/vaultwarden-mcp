# Concept Registry — vaultwarden-mcp

> **Prefix**: `VW` (OKF-CIS form `VW-<PILLAR>.<domain>.<concept>`)
> **Version**: 0.1.0
> **Bridge**: [`AU-ECO.mcp.tool-mode-standardization`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/overview.md) (shared MCP tool-mode surface)

This registry lists every OKF-CIS concept id this package defines or references. It is a
superset of the `CONCEPT:VW-…` markers actually present in `vaultwarden_mcp/**/*.py` —
`tests/test_concept_parity.py` asserts every marker found in code appears here.

---

## Project-Specific Concepts

| Concept ID | Name | Description |
|------------|------|--------------|
| `VW-ECO.mcp.system-operations` | System Operations | `vaultwarden_system` tool: server liveness, version, and public config. |
| `VW-ECO.mcp.account-operations` | Account Operations | `vaultwarden_accounts` tool: profile, two-factor, emergency access, and events. |
| `VW-ECO.mcp.cipher-operations` | Cipher Operations | `vaultwarden_ciphers` tool: decrypted item list/get/create/edit, move-to-trash, and raw cipher routes. |
| `VW-ECO.mcp.folder-operations` | Folder Operations | `vaultwarden_folders` tool: personal-vault folder CRUD. |
| `VW-ECO.mcp.organization-operations` | Organization Operations | `vaultwarden_organizations` tool: organizations, collections, members, and the public API. |
| `VW-ECO.mcp.send-operations` | Send Operations | `vaultwarden_sends` tool: Bitwarden Send create/list/remove. |
| `VW-ECO.mcp.admin-operations` | Admin Operations | `vaultwarden_admin` tool: instance admin panel, identity, and icons. |
| `VW-ECO.mcp.maintenance-operations` | Maintenance Operations | `vaultwarden_maintenance` tool: plan/apply deduplication, rotate/generate password, ingest metadata. |
| `VW-OS.identity.provider-profile` | Provider Profile | Reference-only `provider_configs.vaultwarden` (`endpoint_ref`, `tls_profile`/`tls_profile_ref`, upper-case `credential_refs` aliases `CLIENT_ID`/`CLIENT_SECRET`/`MASTER_PASSWORD`/`ADMIN_TOKEN`, `selector_refs.CRYPTO_BACKEND`). |
| `VW-OS.crypto.native-vault-crypto` | Native Vault Crypto | Pure-Python Bitwarden key derivation (PBKDF2-SHA256/Argon2id), HKDF stretching, AES-256-CBC + HMAC-SHA256 EncStrings, and RSA-OAEP key unwrap, validated against Bitwarden's published SDK test vectors. |
| `VW-OS.crypto.bw-cli-vault-crypto` | Bitwarden CLI Vault Crypto | Decrypted-vault backend delegating to an installed `bw` CLI in a private per-instance data directory. |
| `VW-KG.ingest.metadata-only` | Metadata-Only KG Ingest | Only identifiers, type codes, lifecycle dates, counts, and relationships ever reach the knowledge graph; vault contents (names, usernames, passwords, notes, URIs, keys) are never ingested. |
| `VW-ECO.vault.deduplication` | Vault Deduplication | Exact/loose duplicate-item planning, keep-newest selection, and bulk soft-delete apply (`vaultwarden_maintenance`). |
| `VW-OS.transport.soft-hard-delete-boundary` | Soft/Hard Delete Boundary | `PUT /api/ciphers/delete` (soft, trash) is the only bulk-delete route ever wired to a tool action; `POST /api/ciphers/delete` and `DELETE /api/ciphers` (permanent) are not. |

## Test & Governance Concepts

| Concept ID | Name | Description |
|------------|------|--------------|
| `VW-OS.governance.concept-registry` | Concept Registry Parity | This registry exists, registers the `VW-` prefix, and is a superset of every `CONCEPT:VW-*` marker found in `vaultwarden_mcp/**/*.py` (`tests/test_concept_parity.py`). |
| `VW-OS.init.package-public-api` | Package Public API | The top-level `vaultwarden_mcp` package exposes `__all__` and imports cleanly (`tests/test_init_dynamics.py`). |
| `VW-OS.init.mcp-server-startup` | MCP Server Startup | `vaultwarden_mcp.mcp_server` imports cleanly at startup (`tests/test_startup.py`). |
| `VW-OS.error.agent-problem-details` | Agent Problem Details | Errors render consistently as RFC-9457-style Problem Details across JSON, structured-markdown, and browser-HTML representations, with detail bounded and non-retryable denials never marked retryable (`tests/test_error_authority.py`). |

## Cross-Project References (from agent-utilities)

| Concept ID | Name | Origin |
|------------|------|--------|
| `AU-KG.ontology.federation-provider-leg` | Ontology Federation Provider Leg | agent-utilities — `agent_utilities.ontology_providers` entry point federates `vaultwarden_mcp/ontology/vaultwarden.ttl`. |
| `AU-KG.ingest.enterprise-source-extractor` | Enterprise Source Extractor | agent-utilities — the `native_ingest` (Wire-First) primitive `kg_ingest.py` writes through. |
| `AU-ECO.mcp.tool-mode-standardization` | MCP Tool-Mode Standardization | agent-utilities — the shared `MCP_TOOL_MODE` (`intent`/`condensed`/`verbose`/`both`) surface every connector inherits. |

> 📖 **Full Registry**: See [`agent-utilities/docs/concepts.md`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concepts.md) for the complete cross-ecosystem concept index.
