# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-14

### Added
- Initial release: a Vaultwarden (Bitwarden-compatible) API client, Bitwarden CLI
  wrapper, and MCP server built on `agent-utilities`.
- A committed, data-only catalog of all 281 Vaultwarden 1.37.3 API operations across
  13 domains (`vaultwarden_mcp/api/_routes.py`), with a generated per-operation
  parameter manifest for the verbose MCP tool surface.
- Eight action-routed MCP tool domains: `vaultwarden_system`, `vaultwarden_accounts`,
  `vaultwarden_ciphers`, `vaultwarden_folders`, `vaultwarden_organizations`,
  `vaultwarden_sends`, `vaultwarden_admin`, and `vaultwarden_maintenance`, each
  independently togglable and requiring `confirm: true` for destructive actions.
- Two pluggable decrypted-vault crypto backends behind one `VaultCrypto` protocol:
  `native` (pure-Python Bitwarden key derivation, HKDF stretching, AES-256-CBC +
  HMAC-SHA256 EncStrings, RSA-OAEP organization/item key unwrap, validated against
  Bitwarden's own published SDK test vectors) and `bw_cli` (delegates to an installed
  Bitwarden CLI in a private per-instance data directory).
- Vault maintenance: exact/loose duplicate-item planning and bulk soft-delete
  application (`vaultwarden_mcp/vault/dedupe.py`), and password rotation.
- Metadata-only knowledge-graph ingestion (`vaultwarden_mcp/kg_ingest.py`) mapping
  items, folders, collections, and the server into typed OWL nodes
  (`vaultwarden_mcp/ontology/vaultwarden.ttl`) — vault contents are never ingested.
- Modular subfolders for API wrappers (`api/`) and action-routed MCP tools (`mcp/`).
- Material-theme mkdocs documentation site (7 standard pages).
- Full pre-commit quality gate and flat `tests/` structure.
