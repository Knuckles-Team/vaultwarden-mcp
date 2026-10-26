---
name: vaultwarden-mcp-development
skill_type: skill
description: >-
  Develop, test, and release the Vaultwarden MCP connector while preserving its
  typed route catalog, authentication modes, metadata-only graph projection,
  crypto backends, packaged content, and shared delivery gates.
license: MIT
tags: [vaultwarden, bitwarden, connector, development, testing, packaging, pages, specs]
metadata:
  author: Project Maintainers
  version: '0.1.0'
---

# vaultwarden-mcp development

This skill is the repository contract for the Vaultwarden connector. The
package owns the generated route catalog, HTTP transport, authentication,
action-routed MCP tools, crypto backends, vault deduplication, metadata-only
source projection, packaged skills, and ontology. Shared transport helpers,
connector validation, release rendering, and delivery gates belong to
`agent-connector-sdk` and `pipelines`.

## Repository map

- `vaultwarden_mcp/api/` owns the route catalog, operation manifest, and typed
  HTTP client operations.
- `vaultwarden_mcp/auth.py` resolves the three explicit auth modes and their
  credential references without logging values.
- `vaultwarden_mcp/mcp/` owns the action-routed system, account, cipher,
  folder, organization, send, admin, maintenance, and metadata surfaces.
- `vaultwarden_mcp/crypto/` implements the shared `VaultCrypto` contract for
  the native and Bitwarden CLI backends.
- `vaultwarden_mcp/vault/` owns duplicate planning and the confirmed soft-remove
  operation; permanent purge routes stay outside the bulk action.
- `vaultwarden_mcp/kg_ingest.py` and `ontology/` expose the certified
  `vaultwarden.metadata-entities/v1` metadata-only projection.
- `vaultwarden_mcp/skills/`, `prompts/`, and connector resources are packaged
  content; `tests/` contains the focused contract checks.

## Rapid delivery: the 5-minute contract

Specs are already designed. Deliver one small, reviewable slice at a time.

- Find the owning row with `git grep -n "<term>" -- specs` before changing
  behavior. Extend an existing spec before writing a new requirement.
- Trace a changed operation from its route and auth mode through the typed
  client, action dispatcher, response model, and source mapping. Reuse the
  existing catalog and MCP seams instead of adding a second route path.
- Keep changes inside this connector. SDK transports, Arbora admission, MCP
  multiplexing, and graph persistence belong in their owning repositories.
- Preserve credential aliases `CLIENT_ID`, `CLIENT_SECRET`, `MASTER_PASSWORD`,
  and `ADMIN_TOKEN`. Never print provider responses, vault contents, tokens,
  key material, or decrypted fields in tests or logs.
- Keep graph ingestion metadata-only: identifiers, type codes, lifecycle dates,
  counts, and relationship targets are allowed; user-entered vault content is
  not.
- Use `PUT /api/ciphers/delete` only for confirmed soft remove. Permanent
  remove routes require a separate, explicit product contract.
- Generated `specs/*/status.json` files come from `pipelines-hook spec-status`;
  never hand-edit delivery state. Use an explicit `Spec:` trailer or
  `Spec: none (<reason>)` in the final commit paragraph.
- Stage only reviewed paths, including packaged skill content under the
  existing `vaultwarden_mcp` package-data globs.

## Setup and gates

Use the locked project environment when it is already available:

```bash
uv sync --locked
uvx pre-commit run --all-files
```

For focused feedback, run the smallest existing tests for the changed seam:

```bash
uv run --frozen pytest -q tests/test_api_wrapper.py
uv run --frozen pytest -q tests/test_mcp_tools.py
uv run --frozen pytest -q tests/test_kg_ingest.py
uv run --frozen pytest -q tests/test_crypto_vectors.py
uv run --frozen pytest -q tests/test_vaultwarden_mcp_validation.py
```

The canonical pre-commit configuration delegates connector-standard, secrets,
spec (standard, decomposition, generated status, and trailers), tests-fast,
and dependency-readiness to `Knuckles-Team/pipelines` at `rev: main`. Keep
those shared hooks; do not copy their implementation here or bypass a failure.

## Spec delivery and Pages

`.github/workflows/pages.yml` calls
`Knuckles-Team/pipelines/.github/workflows/pages_pipeline.yml@main` with
`content_source: docs`, `spec_dashboard_enabled: true`, and
`.github/spec-dashboard.json`. The version-1 dashboard reads only
`specs/*/status.json`. Keep the push paths for docs, specs, the dashboard
configuration, and this caller so a source change publishes the page.

A local YAML check proves wiring only. Delivery proof requires a successful
hosted Pages run whose source revision equals the candidate merge SHA and the
public `/spec-delivery/` page and snapshot serving that revision.

## Packaging and release

The existing package-data declaration includes `skills/**`, prompts, ontology,
and connector resources. A packaged skill or resource change therefore gets a
normal patch bump in `pyproject.toml` and a matching `uv.lock` update. Verify
that the wheel contains this development skill before publication. The central
Python workflow publishes the wheel first; the connector container workflow
then uses the canonical renderer. Do not add a synthetic extra or rewrite a
runtime image to satisfy a central check.

## Safety

Never commit `.env` files, credentials, provider responses, generated site
output, caches, or temporary command output. Work in a real Git worktree based
on current `origin/main`, preserve the existing auth, route, crypto, and
metadata contracts, and do not use `git stash`, `git add -A`, or `git add .`.
