# Vaultwarden Mcp
## CLI or API | MCP | Agent

![PyPI - Version](https://img.shields.io/pypi/v/vaultwarden-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/vaultwarden-mcp)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/vaultwarden-mcp)
![GitHub forks](https://img.shields.io/github/forks/Knuckles-Team/vaultwarden-mcp)
![GitHub contributors](https://img.shields.io/github/contributors/Knuckles-Team/vaultwarden-mcp)
![PyPI - License](https://img.shields.io/pypi/l/vaultwarden-mcp)
![GitHub](https://img.shields.io/github/license/Knuckles-Team/vaultwarden-mcp)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/vaultwarden-mcp)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Knuckles-Team/vaultwarden-mcp)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/Knuckles-Team/vaultwarden-mcp)
![GitHub issues](https://img.shields.io/github/issues/Knuckles-Team/vaultwarden-mcp)
![GitHub top language](https://img.shields.io/github/languages/top/Knuckles-Team/vaultwarden-mcp)
![GitHub language count](https://img.shields.io/github/languages/count/Knuckles-Team/vaultwarden-mcp)
![GitHub repo size](https://img.shields.io/github/repo-size/Knuckles-Team/vaultwarden-mcp)
![GitHub repo file count (file type)](https://img.shields.io/github/directory-file-count/Knuckles-Team/vaultwarden-mcp)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/vaultwarden-mcp)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/vaultwarden-mcp)

*Version: 0.1.0*

> **Documentation** — Installation, deployment, and usage across the API, CLI, MCP,
> and A2A agent interfaces are maintained in the
> [official documentation](https://knuckles-team.github.io/vaultwarden-mcp/).

---

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Environment Variables](#environment-variables)
- [MCP Tools](#available-mcp-tools)
- [Documentation](#documentation)

## Overview

`vaultwarden-mcp` exposes a standardized interface to a Vaultwarden (Bitwarden-compatible)
server via the Model Context Protocol — 281 REST operations across 13 domains (accounts,
ciphers, folders, organizations, sends, two-factor, emergency access, events, admin,
identity, icons, misc, public), a decrypted-vault layer for item/folder read and edit, and
vault maintenance (deduplication, password rotation). It is built on the shared
[`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities) framework (auth, the
action router, telemetry, governance) for fleet consistency.

- **Action-routed MCP tools** — eight domain tools (`vaultwarden_system`,
  `vaultwarden_accounts`, `vaultwarden_ciphers`, `vaultwarden_folders`,
  `vaultwarden_organizations`, `vaultwarden_sends`, `vaultwarden_admin`,
  `vaultwarden_maintenance`) each route to many underlying operations via an `action`
  argument, keeping the tool surface small. Setting `MCP_TOOL_MODE=verbose` additionally
  registers one fully-typed tool per API operation from the generated operation manifest.
- **Three interfaces, one package** — use it as a Python **API client**, an **MCP server**
  (`stdio` / `streamable-http` / `sse`), or a Pydantic-AI **A2A agent**.
- **Destructive operations require `confirm: true`.** Bulk item removal is soft by
  default — see [Architecture](#architecture) for the delete-route trap.
- **Two crypto backends** — a pure-Python native implementation, or delegation to an
  installed Bitwarden CLI. See [Architecture](#architecture).
- **Metadata-only knowledge-graph ingestion** — a Wire-First `vaultwarden_maintenance`
  ingest action pushes identifiers, types, dates, counts, and relationships into the
  epistemic-graph Knowledge Graph as typed OWL nodes. Item names, usernames, passwords,
  notes, URIs, and every key stay out of the graph.
- **Per-tool toggles** — enable or disable each tool domain with environment switches.
- **Enterprise-ready** — OTEL/Langfuse telemetry and optional Eunomia access governance.

## Installation

### Install with `uvx` (no install — run on demand)

```bash
uvx --from "vaultwarden-mcp[mcp]" vaultwarden-mcp      # MCP server + full graph engine
uvx --from "vaultwarden-mcp[agent]" vaultwarden-agent  # MCP + A2A agent runtime
```

> Every supported install includes `epistemic-graph[full]`. The `[mcp]` extra adds
> the MCP serving stack; `[agent]` adds the current `agent-runtime` and telemetry.

### Install with `pip`

```bash
python -m pip install vaultwarden-mcp            # core (API client)
python -m pip install "vaultwarden-mcp[all]"     # + MCP server + A2A agent + telemetry
```

| Extra | Installs | Use when |
|-------|----------|----------|
| `vaultwarden-mcp[mcp]` | Connector-focused MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | You only run the **MCP server** (smallest install / image) |
| `vaultwarden-mcp[agent]` | Agent runtime (`agent-utilities[agent-runtime,logfire]` — model orchestration + `epistemic-graph[full]`) | You run the **integrated A2A agent** |
| `vaultwarden-mcp[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

### Console scripts

After installation the following entry points are available on your `PATH`:

| Command | Description |
|---------|-------------|
| `vaultwarden-mcp` | Launch the MCP server |
| `vaultwarden-agent` | Launch the A2A agent server |

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Local build tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `vaultwarden-mcp:mcp-local` | `--target mcp` | `vaultwarden-mcp[mcp]` — MCP serving runtime + `epistemic-graph[full]` | `vaultwarden-mcp` |
| `vaultwarden-mcp:agent-local` | `--target agent` (default) | `vaultwarden-mcp[agent]` — MCP + agent runtime + `epistemic-graph[full]` | `vaultwarden-agent` |

```bash
docker build --target mcp   -t vaultwarden-mcp:mcp-local docker/
docker build --target agent -t vaultwarden-mcp:agent-local docker/
```

## Usage

### As a Python API client

```python
from vaultwarden_mcp.auth import get_client, get_vault_crypto

client = get_client()               # resolves provider_configs.vaultwarden from AgentConfig
print(client.server_version())

vault = get_vault_crypto()          # unlocks the decrypted-vault backend on demand
for item in vault.list_items():
    print(item["id"], item["type"])
```

### As an MCP server (CLI)

```bash
# Local stdio (for IDEs)
vaultwarden-mcp

# Networked streamable-http
vaultwarden-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

### Calling an MCP tool

Tools are action-routed — pass an `action` plus a JSON `params_json` string:

```json
{
  "tool": "vaultwarden_system",
  "arguments": {
    "action": "version",
    "params_json": "{}"
  }
}
```

Destructive actions (bulk trash, permanent removal, disabling a user) additionally
require `"confirm": true` in `params_json`.

## Architecture

`vaultwarden_mcp/api/api_client_base.py` (`VaultwardenApiBase`) owns HTTP transport and
authentication: it never follows redirects, stays pinned to the configured origin, bounds
response size and time, and distinguishes three auth modes per request —

- `user` — a bearer token from the account's personal API key
  (`grant_type=client_credentials`), cached until shortly before expiry and renewed once
  on a `401`;
- `admin` — the `VW_ADMIN` session cookie issued after posting the instance admin token
  to `/admin`;
- `none` — public endpoints (`/alive`, `/api/version`, `/api/config`, prelogin).

`vaultwarden_mcp/api/_routes.py` is a committed, data-only catalog of all 281 Vaultwarden
1.37.3 API operations (accounts 39, ciphers 58, organizations 77, two-factor 26, admin 20,
emergency access 18, sends 14, folders 7, identity 6, misc 9, icons 2, events 4, public 1),
normalized from the server's own Rocket route attributes. `api/_operation_manifest.py`
derives a fully-typed parameter schema per operation from that catalog, consumed when
`MCP_TOOL_MODE=verbose` to synthesize one MCP tool per operation instead of a generic
`params_json` fallback.

**The soft-delete trap:** `PUT /api/ciphers/delete` moves items to trash (recoverable for
30 days) — this is the only bulk-delete route this package's tools ever call.
`POST /api/ciphers/delete` and `DELETE /api/ciphers` are **permanent** in Vaultwarden and
are deliberately not wired to any bulk-delete tool action.

**Decrypted vault access** (`vaultwarden_mcp/crypto/`) is a pluggable `VaultCrypto`
backend, selected by `selector_refs.CRYPTO_BACKEND`:

- `native` (default) — pure-Python key derivation (PBKDF2-SHA256 or Argon2id) and HKDF
  stretching (`crypto/keys.py`), AES-256-CBC + HMAC-SHA256 EncStrings with the MAC
  verified before any decryption, and RSA-OAEP unwrap of organization and per-item keys
  (`crypto/encstring.py`). Only strict type-2 EncStrings are decrypted; anything else
  passes through unchanged. Validated against Bitwarden's own published SDK test vectors.
- `bw_cli` — delegates key handling to an installed Bitwarden CLI (`bw`), driving a
  private, per-instance CLI data directory rather than the invoking user's real login
  state, with credentials passed only through the child process environment.

Both backends produce and accept records in the Bitwarden CLI JSON shape, so
`vaultwarden_mcp/vault/dedupe.py` (exact or loose duplicate matching, keep-newest
selection, bulk soft-delete apply) behaves identically regardless of backend.

`vaultwarden_mcp/kg_ingest.py` maps vault entities to typed OWL nodes
(`:VaultwardenItem` subclasses, `:VaultwardenFolder`, `:VaultwardenCollection`,
`:VaultwardenServer`) and relationships (`:vaultwardenInFolder`,
`:vaultwardenInOrganization`, `:vaultwardenInCollection`) through the required
`agent_utilities.knowledge_graph.memory.native_ingest` (Wire-First) primitive. Only
identifiers, type codes, lifecycle dates, counts, and relationships are accepted — every
item name, username, password, note, URI, TOTP seed, custom field, attachment, folder
name, collection name, send content, and key is rejected before it ever reaches the graph
(`vaultwarden_mcp/ontology/vaultwarden.ttl`).

## MCP

### Using as an MCP Server

The MCP Server can be run in `stdio` (local), `streamable-http` (networked), or
`sse` mode.

#### Runtime configuration

Keep `provider_configs.vaultwarden` endpoint, credential, selector, and TLS
references in `AgentConfig`; do not place resolved values in MCP client JSON. See
[Environment Variables](#environment-variables) for the shape of that profile.

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the connector-focused `[mcp]` extra.** Examples use `vaultwarden-mcp[mcp]` to add
> FastMCP / FastAPI through `agent-utilities[mcp]`; the required Agent Utilities core
> still carries `epistemic-graph[full]`. The `[agent-runtime]` extra additionally
> enables model orchestration.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "vaultwarden-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "vaultwarden-mcp[mcp]",
        "vaultwarden-mcp"
      ],
      "env": {
        "MCP_TOOL_MODE": "intent",
        "ACCOUNTSTOOL": "True",
        "ADMINTOOL": "True",
        "CIPHERSTOOL": "True",
        "FOLDERSTOOL": "True",
        "MAINTENANCETOOL": "True",
        "ORGANIZATIONSTOOL": "True",
        "SENDSTOOL": "True",
        "SYSTEMTOOL": "True"
      }
    }
  }
}
```

Runtime references require an alias-aware launcher such as GraphOS. Other
launchers must omit those entries and inject the resolved values through their
own runtime secret boundary.

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "vaultwarden-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "vaultwarden-mcp[mcp]",
        "vaultwarden-mcp",
        "--transport",
        "streamable-http",
        "--port",
        "8000"
      ],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "MCP_TOOL_MODE": "intent",
        "ACCOUNTSTOOL": "True",
        "ADMINTOOL": "True",
        "CIPHERSTOOL": "True",
        "FOLDERSTOOL": "True",
        "MAINTENANCETOOL": "True",
        "ORGANIZATIONSTOOL": "True",
        "SENDSTOOL": "True",
        "SYSTEMTOOL": "True"
      }
    }
  }
}
```

Alternatively, connect to a pre-deployed Streamable-HTTP instance by `url`:

```json
{
  "mcpServers": {
    "vaultwarden-mcp": {
      "url": "http://localhost:8000/vaultwarden-mcp/mcp"
    }
  }
}
```

Run a reviewed container image as a least-privilege stdio child (no
listener or published port):

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  -e MCP_TOOL_MODE=intent \
  -e ACCOUNTSTOOL=True \
  -e ADMINTOOL=True \
  -e CIPHERSTOOL=True \
  -e FOLDERSTOOL=True \
  -e MAINTENANCETOOL=True \
  -e ORGANIZATIONSTOOL=True \
  -e SENDSTOOL=True \
  -e SYSTEMTOOL=True \
  registry.example.invalid/vaultwarden-mcp@sha256:<digest> vaultwarden-mcp
```

For containerized network HTTP, supply an authenticated TLS ingress (or
direct server TLS), exact `MCP_ALLOWED_HOSTS`, and an exact trusted-proxy
CIDR policy through the operator-owned deployment profile. The generator
does not emit an unauthenticated non-loopback listener.

_Auto-generated from the code-read env surface (`MCP_TOOL_MODE` + package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`vaultwarden-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/vaultwarden-mcp/deployment/) has full,
copy-paste `mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS ingress.
  Keep the URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Knowledge-graph database (`epistemic-graph`)

Every image embeds the **epistemic-graph[full]** engine. For production — or to
share one knowledge graph across multiple
agents — run **epistemic-graph as its own database container** and point the agent at it.
Deployment recipes (single-node + Raft HA), connection config, and the full database
architecture (with diagrams) are in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).
Local engine autostart or an operator-configured remote engine is selected through AgentConfig.

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` |  |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | options: stdio, streamable-http, sse |
| `AUTH_TYPE` | `none` | network listeners outside loopback require configured authentication |
| `MCP_TOOL_MODE` | `intent` |  |
| `ENABLE_OTEL` | `False` |  |
| `EUNOMIA_TYPE` | `none` | options: none, embedded, remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `SYSTEMTOOL` | `True` |  |
| `ACCOUNTSTOOL` | `True` |  |
| `CIPHERSTOOL` | `True` |  |
| `FOLDERSTOOL` | `True` |  |
| `ORGANIZATIONSTOOL` | `True` |  |
| `SENDSTOOL` | `True` |  |
| `ADMINTOOL` | `True` |  |
| `MAINTENANCETOOL` | `True` |  |
| `VAULTWARDEN_MCP_IMAGE` | — | e.g. registry.example.invalid/vaultwarden-mcp@sha256:<digest> |
| `VAULTWARDEN_AGENT_IMAGE` | — | e.g. registry.example.invalid/vaultwarden-mcp@sha256:<digest> |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | — | Operator-configured LLM provider for the agent |
| `MODEL_ID` | — | Operator-configured model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_18 package + 17 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->

The `provider_configs.vaultwarden` profile referenced above (see `vaultwarden_mcp/auth.py`)
carries reference-only configuration through `AgentConfig`:

| Field | Notes |
|-------|-------|
| `enabled` | Toggles the profile. |
| `endpoint_ref` | Must resolve to an HTTPS or loopback origin. |
| `tls_profile` / `tls_profile_ref` | Exactly one of the two — a named trust policy, e.g. `{"system_trust": true, "ca_bundle_path": "..."}`. |
| `credential_refs.CLIENT_ID` / `CLIENT_SECRET` | The account's personal API key (`client_credentials` grant). Upper-case aliases. |
| `credential_refs.MASTER_PASSWORD` | Only needed for decrypted vault operations (`vaultwarden_ciphers`, `vaultwarden_folders`, maintenance). |
| `credential_refs.ADMIN_TOKEN` | The plaintext instance admin token, only needed for `vaultwarden_admin`. |
| `selector_refs.CRYPTO_BACKEND` | `native` (default) or `bw_cli` — see [Architecture](#architecture). |

References are `env://NAME`, `vault://…`, or `secret://…`, resolved only at runtime — never
a literal value.

## Available MCP Tools

Each tool is **action-routed**: pass an `action` and a JSON `params_json` payload. Tool
domains can be toggled on or off with the listed environment variable. The table below is
**auto-generated from the live server** by the `mcp-readme-table` pre-commit hook
(`python -m agent_utilities.mcp.readme_tools`) — do not edit it by hand.

<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (`MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `vaultwarden_accounts` | `ACCOUNTSTOOL` | Operate the account profile, two-factor methods, emergency access, |
| `vaultwarden_admin` | `ADMINTOOL` | Administer the instance (users, config, diagnostics), plus |
| `vaultwarden_ciphers` | `CIPHERSTOOL` | Read and write vault items (ciphers). |
| `vaultwarden_folders` | `FOLDERSTOOL` | Read and write personal-vault folders. |
| `vaultwarden_maintenance` | `MAINTENANCETOOL` | Plan/apply vault deduplication, rotate item passwords, generate |
| `vaultwarden_organizations` | `ORGANIZATIONSTOOL` | Manage organizations, collections, members, groups, and policies, |
| `vaultwarden_sends` | `SENDSTOOL` | Create, list, update, and remove Bitwarden Sends (text or file). |
| `vaultwarden_system` | `SYSTEMTOOL` | Read Vaultwarden server liveness, version, and public configuration. |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>281 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `vaultwarden_accounts_post_api_key` | `ACCOUNTSTOOL` | Generate/rotate the personal API key (client_credentials login secret) |
| `vaultwarden_accounts_post_prelogin` | `ACCOUNTSTOOL` | Get KDF type/iterations for an email before login (also mounted at /identity/accounts/prelogin) |
| `vaultwarden_accounts_rotate_api_key` | `ACCOUNTSTOOL` | Rotate the personal API key |
| `vaultwarden_activate_authenticator` | `TWO_FACTORTOOL` | Enable TOTP 2FA by confirming a generated code |
| `vaultwarden_activate_authenticator_put` | `TWO_FACTORTOOL` | Enable TOTP 2FA (PUT alias) |
| `vaultwarden_activate_duo` | `TWO_FACTORTOOL` | Enable/update Duo (or Duo OIDC) 2FA |
| `vaultwarden_activate_duo_put` | `TWO_FACTORTOOL` | Enable/update Duo 2FA (PUT alias) |
| `vaultwarden_activate_webauthn` | `TWO_FACTORTOOL` | Register a new WebAuthn security key for 2FA |
| `vaultwarden_activate_webauthn_put` | `TWO_FACTORTOOL` | Register a WebAuthn key (PUT alias) |
| `vaultwarden_activate_yubikey` | `TWO_FACTORTOOL` | Enable YubiKey OTP 2FA |
| `vaultwarden_activate_yubikey_put` | `TWO_FACTORTOOL` | Enable YubiKey OTP 2FA (PUT alias) |
| `vaultwarden_admin_delete_organization` | `ADMINTOOL` | Permanently delete an organization and all its data |
| `vaultwarden_alive` | `MISCTOOL` | Liveness/health check (also verifies DB connectivity) |
| `vaultwarden_approve_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantor approves an in-progress request early (skips wait) |
| `vaultwarden_archive_cipher_put` | `CIPHERSTOOL` | Archive one cipher (hide from default view, distinct from trash) |
| `vaultwarden_archive_cipher_selected` | `CIPHERSTOOL` | Bulk archive ciphers |
| `vaultwarden_backup_db` | `ADMINTOOL` | Trigger an on-demand database backup (sqlite only) |
| `vaultwarden_bulk_confirm_invite` | `ORGANIZATIONSTOOL` | Bulk confirm accepted invites, delivering the org key to each new member |
| `vaultwarden_bulk_delete_groups` | `ORGANIZATIONSTOOL` | Bulk delete groups |
| `vaultwarden_bulk_delete_member` | `ORGANIZATIONSTOOL` | Bulk remove members from the org |
| `vaultwarden_bulk_delete_organization_collections` | `ORGANIZATIONSTOOL` | Bulk delete collections by id |
| `vaultwarden_bulk_public_keys` | `ORGANIZATIONSTOOL` | Bulk-fetch public keys for a list of user ids |
| `vaultwarden_bulk_reinvite_members` | `ORGANIZATIONSTOOL` | Bulk resend pending invites |
| `vaultwarden_bulk_restore_members` | `ORGANIZATIONSTOOL` | Bulk restore revoked members |
| `vaultwarden_bulk_revoke_members` | `ORGANIZATIONSTOOL` | Bulk revoke members |
| `vaultwarden_config` | `MISCTOOL` | Return server config/feature-flags/environment URLs used by clients on startup |
| `vaultwarden_confirm_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantor confirms the grantee, delivering the grantor’s vault key encrypted for the grantee |
| `vaultwarden_confirm_invite` | `ORGANIZATIONSTOOL` | Confirm one accepted invite |
| `vaultwarden_create_organization` | `ORGANIZATIONSTOOL` | Create a new organization |
| `vaultwarden_deauth_user` | `ADMINTOOL` | Force-logout a user (invalidate all sessions/security stamp) |
| `vaultwarden_delete_account` | `ACCOUNTSTOOL` | Delete own account (REST DELETE alias) |
| `vaultwarden_delete_attachment` | `CIPHERSTOOL` | Delete an attachment |
| `vaultwarden_delete_attachment_admin` | `CIPHERSTOOL` | Delete an attachment (admin path) |
| `vaultwarden_delete_attachment_post` | `CIPHERSTOOL` | Delete an attachment (POST alias) |
| `vaultwarden_delete_attachment_post_admin` | `CIPHERSTOOL` | Delete an attachment (admin path, POST alias) |
| `vaultwarden_delete_cipher` | `CIPHERSTOOL` | Permanently delete a cipher (REST DELETE) |
| `vaultwarden_delete_cipher_admin` | `CIPHERSTOOL` | Permanently delete via admin path (REST DELETE) |
| `vaultwarden_delete_cipher_post` | `CIPHERSTOOL` | Permanently delete a cipher (POST alias) |
| `vaultwarden_delete_cipher_post_admin` | `CIPHERSTOOL` | Permanently delete a cipher via admin path |
| `vaultwarden_delete_cipher_put` | `CIPHERSTOOL` | Soft-delete (move to trash) a cipher |
| `vaultwarden_delete_cipher_put_admin` | `CIPHERSTOOL` | Soft-delete via admin path |
| `vaultwarden_delete_cipher_selected` | `CIPHERSTOOL` | Bulk permanently delete ciphers by id list |
| `vaultwarden_delete_cipher_selected_admin` | `CIPHERSTOOL` | Bulk permanent delete via admin path |
| `vaultwarden_delete_cipher_selected_post` | `CIPHERSTOOL` | Bulk permanent delete (POST alias) |
| `vaultwarden_delete_cipher_selected_post_admin` | `CIPHERSTOOL` | Bulk permanent delete via admin path (POST alias) |
| `vaultwarden_delete_cipher_selected_put` | `CIPHERSTOOL` | Bulk soft-delete (move to trash) |
| `vaultwarden_delete_cipher_selected_put_admin` | `CIPHERSTOOL` | Bulk soft-delete via admin path |
| `vaultwarden_delete_config` | `ADMINTOOL` | Reset configuration overrides back to defaults |
| `vaultwarden_delete_emergency_access` | `EMERGENCY_ACCESSTOOL` | Delete/revoke an emergency-access relationship |
| `vaultwarden_delete_folder` | `FOLDERSTOOL` | Delete a folder |
| `vaultwarden_delete_folder_post` | `FOLDERSTOOL` | Delete a folder (POST alias) |
| `vaultwarden_delete_group` | `ORGANIZATIONSTOOL` | Delete a group |
| `vaultwarden_delete_member` | `ORGANIZATIONSTOOL` | Remove one member from the org |
| `vaultwarden_delete_organization_collection` | `ORGANIZATIONSTOOL` | Delete a collection |
| `vaultwarden_delete_send` | `SENDSTOOL` | Delete a Send |
| `vaultwarden_delete_sso_user` | `ADMINTOOL` | Unlink a user’s SSO identity (force back to password login) |
| `vaultwarden_delete_user` | `ADMINTOOL` | Permanently delete an instance user account |
| `vaultwarden_delete_webauthn` | `TWO_FACTORTOOL` | Remove a registered WebAuthn security key |
| `vaultwarden_disable_authenticator` | `TWO_FACTORTOOL` | Disable TOTP 2FA |
| `vaultwarden_disable_twofactor` | `TWO_FACTORTOOL` | Disable a specific 2FA provider |
| `vaultwarden_disable_twofactor_put` | `TWO_FACTORTOOL` | Disable a specific 2FA provider (PUT alias) |
| `vaultwarden_disable_user` | `ADMINTOOL` | Disable (lock) a user account instance-wide |
| `vaultwarden_download_send` | `SENDSTOOL` | Anonymous: download the actual (still-encrypted) Send file bytes |
| `vaultwarden_edit_member` | `ORGANIZATIONSTOOL` | Edit a member (POST alias) |
| `vaultwarden_email` | `TWO_FACTORTOOL` | Confirm email-2FA setup with the emailed code |
| `vaultwarden_emergency_access_accept_invite` | `EMERGENCY_ACCESSTOOL` | Grantee accepts a pending emergency-access invite |
| `vaultwarden_emergency_access_send_invite` | `EMERGENCY_ACCESSTOOL` | Grantor invites another user (by email) as emergency contact |
| `vaultwarden_enable_user` | `ADMINTOOL` | Re-enable a disabled user account |
| `vaultwarden_generate_authenticator` | `TWO_FACTORTOOL` | Generate a new TOTP secret + provisioning QR data |
| `vaultwarden_generate_webauthn_challenge` | `TWO_FACTORTOOL` | Generate a WebAuthn registration challenge |
| `vaultwarden_generate_yubikey` | `TWO_FACTORTOOL` | Get current YubiKey OTP 2FA configuration (masked) |
| `vaultwarden_get_all_devices` | `ACCOUNTSTOOL` | List current user devices |
| `vaultwarden_get_api_webauthn` | `MISCTOOL` | Stub empty passkey list (prevents client errors; Vaultwarden does not support WebAuthn passwordless login) |
| `vaultwarden_get_attachment` | `CIPHERSTOOL` | Get attachment metadata + a short-lived download URL |
| `vaultwarden_get_auth_request` | `ACCOUNTSTOOL` | Poll status of one auth request by id |
| `vaultwarden_get_auth_request_response` | `ACCOUNTSTOOL` | Anonymous poll for approval + encrypted key once approved |
| `vaultwarden_get_auth_requests` | `ACCOUNTSTOOL` | List all pending/approved auth requests for current user |
| `vaultwarden_get_auth_requests_pending` | `ACCOUNTSTOOL` | List only pending auth requests |
| `vaultwarden_get_auto_enroll_status` | `ORGANIZATIONSTOOL` | Check whether org auto-enrolls new members into password-reset admin recovery |
| `vaultwarden_get_billing_metadata` | `ORGANIZATIONSTOOL` | Get org billing metadata |
| `vaultwarden_get_billing_warnings` | `ORGANIZATIONSTOOL` | Get org billing warning banners |
| `vaultwarden_get_cipher` | `CIPHERSTOOL` | Get one cipher by id |
| `vaultwarden_get_cipher_admin` | `CIPHERSTOOL` | Get one cipher with admin-view fields (org admin bypassing normal access) |
| `vaultwarden_get_cipher_details` | `CIPHERSTOOL` | Get one cipher with full details incl. collection ids |
| `vaultwarden_get_cipher_events` | `EVENTSTOOL` | List audit-log events for one cipher |
| `vaultwarden_get_ciphers` | `CIPHERSTOOL` | List all ciphers owned by or shared with the user |
| `vaultwarden_get_collection_users` | `ORGANIZATIONSTOOL` | List users/groups with access to one collection |
| `vaultwarden_get_contacts` | `EMERGENCY_ACCESSTOOL` | List people the caller has granted emergency access to (as grantor) |
| `vaultwarden_get_device` | `ACCOUNTSTOOL` | Get one device by identifier |
| `vaultwarden_get_device_verification_settings` | `TWO_FACTORTOOL` | Get/return device-verification (new-device email) settings |
| `vaultwarden_get_diagnostics_config` | `ADMINTOOL` | Get sanitized server config as JSON for diagnostics |
| `vaultwarden_get_diagnostics_http` | `ADMINTOOL` | Diagnostic HTTP echo/status-code test endpoint |
| `vaultwarden_get_dummy_master_password_policy` | `ORGANIZATIONSTOOL` | Return an empty master-password-policy stub for a placeholder org id |
| `vaultwarden_get_duo` | `TWO_FACTORTOOL` | Get current Duo 2FA configuration (masked) |
| `vaultwarden_get_email` | `TWO_FACTORTOOL` | Check whether email 2FA is set up / request setup email |
| `vaultwarden_get_emergency_access` | `EMERGENCY_ACCESSTOOL` | Get one emergency-access record by id |
| `vaultwarden_get_folder` | `FOLDERSTOOL` | Get one folder by id |
| `vaultwarden_get_folders` | `FOLDERSTOOL` | List all folders |
| `vaultwarden_get_grantees` | `EMERGENCY_ACCESSTOOL` | List people who have granted the caller emergency access (as grantee) |
| `vaultwarden_get_group` | `ORGANIZATIONSTOOL` | Get one group |
| `vaultwarden_get_group_details` | `ORGANIZATIONSTOOL` | Get one group with members + collections |
| `vaultwarden_get_group_members` | `ORGANIZATIONSTOOL` | List members of a group |
| `vaultwarden_get_groups` | `ORGANIZATIONSTOOL` | List org groups (collections of members for access assignment) |
| `vaultwarden_get_groups_details` | `ORGANIZATIONSTOOL` | List groups with member/collection details |
| `vaultwarden_get_known_device` | `ACCOUNTSTOOL` | Check whether a device identifier is already known for an email |
| `vaultwarden_get_master_password_policy` | `ORGANIZATIONSTOOL` | Get the effective master-password-complexity policy for the org |
| `vaultwarden_get_members` | `ORGANIZATIONSTOOL` | List organization members ("users") |
| `vaultwarden_get_org_collection_detail` | `ORGANIZATIONSTOOL` | Get one collection’s details |
| `vaultwarden_get_org_collections` | `ORGANIZATIONSTOOL` | List all collections in an org |
| `vaultwarden_get_org_collections_details` | `ORGANIZATIONSTOOL` | List collections with per-collection access details |
| `vaultwarden_get_org_details` | `ORGANIZATIONSTOOL` | Get org-scoped cipher listing with per-cipher collection membership |
| `vaultwarden_get_org_domain_sso_verified` | `ORGANIZATIONSTOOL` | Check whether an org’s SSO domain claim is verified |
| `vaultwarden_get_org_events` | `EVENTSTOOL` | List audit-log events for an organization |
| `vaultwarden_get_org_export` | `ORGANIZATIONSTOOL` | Export all org cipher data (admin-triggered org vault export) |
| `vaultwarden_get_org_user_mini_details` | `ORGANIZATIONSTOOL` | List members with minimal fields (id/name/email) for UI pickers |
| `vaultwarden_get_organization` | `ORGANIZATIONSTOOL` | Get organization details |
| `vaultwarden_get_organization_keys` | `ORGANIZATIONSTOOL` | Get the org’s public key + (if authorized) encrypted private key |
| `vaultwarden_get_organization_public_key` | `ORGANIZATIONSTOOL` | Get the org’s public RSA key |
| `vaultwarden_get_plans` | `ORGANIZATIONSTOOL` | List available subscription plans |
| `vaultwarden_get_policy` | `ORGANIZATIONSTOOL` | Get one policy by type |
| `vaultwarden_get_public_keys` | `ACCOUNTSTOOL` | Get another user public RSA key by user id |
| `vaultwarden_get_recover` | `TWO_FACTORTOOL` | Get the 2FA recovery code (used if all 2FA devices are lost) |
| `vaultwarden_get_reset_password_details` | `ORGANIZATIONSTOOL` | Get the data needed to perform admin password reset for a member (their reset_password_key + KDF settings) |
| `vaultwarden_get_self_host_billing_metadata` | `ORGANIZATIONSTOOL` | Get self-host billing metadata |
| `vaultwarden_get_send` | `SENDSTOOL` | Get one of the caller’s own Sends by id |
| `vaultwarden_get_sends` | `SENDSTOOL` | List the caller’s own Sends |
| `vaultwarden_get_settings_domains` | `MISCTOOL` | Get the user’s configured equivalent-domains list (for autofill matching) |
| `vaultwarden_get_tasks` | `ACCOUNTSTOOL` | List pending security tasks (at-risk password / admin-assigned tasks) for the current device |
| `vaultwarden_get_twofactor` | `TWO_FACTORTOOL` | List enabled 2FA methods for the user |
| `vaultwarden_get_user` | `ORGANIZATIONSTOOL` | Get one member’s full details |
| `vaultwarden_get_user_by_mail_json` | `ADMINTOOL` | Look up one instance user by email |
| `vaultwarden_get_user_collections` | `ORGANIZATIONSTOOL` | List collections the current user has access to (across all orgs) |
| `vaultwarden_get_user_events` | `EVENTSTOOL` | List audit-log events for one org member |
| `vaultwarden_get_user_json` | `ADMINTOOL` | Get one instance user by id |
| `vaultwarden_get_users_json` | `ADMINTOOL` | List all instance users (JSON, for the admin table) |
| `vaultwarden_get_webauthn` | `TWO_FACTORTOOL` | List registered WebAuthn/FIDO2 2FA security keys |
| `vaultwarden_hibp_breach` | `MISCTOOL` | Proxy a Have I Been Pwned breach lookup for a username |
| `vaultwarden_icon_external` | `ICONSTOOL` | Fetch/cache a site favicon by hostname from the internet |
| `vaultwarden_icon_internal` | `ICONSTOOL` | Serve a favicon from local cache without external fetch (used when icon fetching is disabled) |
| `vaultwarden_identity_post_prelogin` | `IDENTITYTOOL` | Get a user’s KDF type/iterations/memory/parallelism by email before attempting login |
| `vaultwarden_identity_register` | `IDENTITYTOOL` | Register a new account (email, name, master-password hash, encrypted keys, KDF params) |
| `vaultwarden_initiate_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantee starts the takeover/view waiting period |
| `vaultwarden_invite_user` | `ADMINTOOL` | Create/invite a new instance user from the admin panel |
| `vaultwarden_ldap_import` | `PUBLICTOOL` | Bulk-provision/deprovision org members + groups from an external directory (SCIM/LDAP-style) |
| `vaultwarden_leave_organization` | `ORGANIZATIONSTOOL` | Current user leaves an organization |
| `vaultwarden_list_policies` | `ORGANIZATIONSTOOL` | List all policies configured for the org |
| `vaultwarden_list_policies_token` | `ORGANIZATIONSTOOL` | List policies visible to an not-yet-member using their invite token |
| `vaultwarden_move_cipher_selected` | `CIPHERSTOOL` | Bulk move ciphers into a folder (or remove from folder) |
| `vaultwarden_move_cipher_selected_put` | `CIPHERSTOOL` | Bulk move ciphers into a folder (PUT alias) |
| `vaultwarden_now` | `MISCTOOL` | Return current server time |
| `vaultwarden_organizations_accept_invite` | `ORGANIZATIONSTOOL` | Invited user accepts the org invite |
| `vaultwarden_organizations_delete_organization` | `ORGANIZATIONSTOOL` | Delete an organization |
| `vaultwarden_organizations_post_api_key` | `ORGANIZATIONSTOOL` | Generate/rotate the org’s API key (for client_credentials / public API access) |
| `vaultwarden_organizations_rotate_api_key` | `ORGANIZATIONSTOOL` | Rotate the org’s API key |
| `vaultwarden_organizations_send_invite` | `ORGANIZATIONSTOOL` | Invite a user to the organization by email |
| `vaultwarden_password_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantee completes takeover: uploads the grantor’s user key re-encrypted under a NEW master key/password chosen by the grantee |
| `vaultwarden_password_hint` | `ACCOUNTSTOOL` | Request password hint be emailed |
| `vaultwarden_policies_emergency_access` | `EMERGENCY_ACCESSTOOL` | Get org policies applicable to the emergency-access relationship |
| `vaultwarden_post_access` | `SENDSTOOL` | Anonymous: fetch a Send’s metadata by access id (for viewing/decrypting) |
| `vaultwarden_post_access_file` | `SENDSTOOL` | Anonymous: get a download URL for a Send file |
| `vaultwarden_post_access_file_legacy` | `SENDSTOOL` | Anonymous: legacy get-download-URL path |
| `vaultwarden_post_access_legacy` | `SENDSTOOL` | Anonymous: legacy path for fetching a Send by access id |
| `vaultwarden_post_attachment` | `CIPHERSTOOL` | Upload attachment (legacy single-phase) |
| `vaultwarden_post_attachment_admin` | `CIPHERSTOOL` | Upload attachment via admin path |
| `vaultwarden_post_attachment_share` | `CIPHERSTOOL` | Re-key an attachment when its cipher is shared to an org |
| `vaultwarden_post_attachment_v2` | `CIPHERSTOOL` | Begin attachment upload (v2): register metadata, get upload URL |
| `vaultwarden_post_attachment_v2_data` | `CIPHERSTOOL` | Upload the encrypted attachment bytes (v2 second phase) |
| `vaultwarden_post_auth_request` | `ACCOUNTSTOOL` | Create a new device "login with device" auth request |
| `vaultwarden_post_bulk_access_collections` | `ORGANIZATIONSTOOL` | Bulk-set which users/groups can access a set of collections |
| `vaultwarden_post_bulk_collections` | `ORGANIZATIONSTOOL` | Bulk-assign a set of ciphers to collections |
| `vaultwarden_post_cipher` | `CIPHERSTOOL` | Update a cipher |
| `vaultwarden_post_cipher_admin` | `CIPHERSTOOL` | Update a cipher via the admin path (POST alias) |
| `vaultwarden_post_cipher_partial` | `CIPHERSTOOL` | Partial update: only folder assignment / favorite flag (no re-encryption needed) |
| `vaultwarden_post_cipher_share` | `CIPHERSTOOL` | Move a personal cipher into an organization ("share") |
| `vaultwarden_post_ciphers` | `CIPHERSTOOL` | Create a cipher (personal or org, no collections in this call) |
| `vaultwarden_post_ciphers_admin` | `CIPHERSTOOL` | Create a cipher as an org admin on behalf of the org (unassigned/admin path) |
| `vaultwarden_post_ciphers_create` | `CIPHERSTOOL` | Create a cipher, optionally assigning collections in the same call |
| `vaultwarden_post_ciphers_import` | `CIPHERSTOOL` | Bulk import ciphers + folders in one call |
| `vaultwarden_post_clear_device_token` | `ACCOUNTSTOOL` | Clear a device push token (POST alias) |
| `vaultwarden_post_collections2_update` | `CIPHERSTOOL` | Set collections (v2, POST alias) |
| `vaultwarden_post_collections_admin` | `CIPHERSTOOL` | Set collections via admin path (POST alias) |
| `vaultwarden_post_collections_update` | `CIPHERSTOOL` | Set collections (legacy v1, POST alias) |
| `vaultwarden_post_config` | `ADMINTOOL` | Persist configuration overrides (the settings normally set via env vars) |
| `vaultwarden_post_delete_account` | `ACCOUNTSTOOL` | Delete own account (password/OTP confirmation in body) |
| `vaultwarden_post_delete_emergency_access` | `EMERGENCY_ACCESSTOOL` | Delete/revoke (POST alias) |
| `vaultwarden_post_delete_group` | `ORGANIZATIONSTOOL` | Delete a group (POST alias) |
| `vaultwarden_post_delete_group_member` | `ORGANIZATIONSTOOL` | Remove one member from a group |
| `vaultwarden_post_delete_organization` | `ORGANIZATIONSTOOL` | Delete an organization (POST alias) |
| `vaultwarden_post_delete_recover` | `ACCOUNTSTOOL` | Request account-deletion email (forgot-password-style deletion init) |
| `vaultwarden_post_delete_recover_token` | `ACCOUNTSTOOL` | Complete account deletion using emailed token |
| `vaultwarden_post_device_token` | `ACCOUNTSTOOL` | Set/update device push token |
| `vaultwarden_post_email` | `ACCOUNTSTOOL` | Confirm email change with token + new encrypted keys |
| `vaultwarden_post_email_token` | `ACCOUNTSTOOL` | Request email-change verification token (send code to new address) |
| `vaultwarden_post_emergency_access` | `EMERGENCY_ACCESSTOOL` | Update an emergency-access grant (POST alias) |
| `vaultwarden_post_events_collect` | `EVENTSTOOL` | Client-side telemetry/event ingestion endpoint used by web-vault to batch-report UI events |
| `vaultwarden_post_folder` | `FOLDERSTOOL` | Rename a folder (POST alias) |
| `vaultwarden_post_folders` | `FOLDERSTOOL` | Create a folder |
| `vaultwarden_post_group` | `ORGANIZATIONSTOOL` | Update a group (POST alias, id in path) |
| `vaultwarden_post_groups` | `ORGANIZATIONSTOOL` | Create a group |
| `vaultwarden_post_kdf` | `ACCOUNTSTOOL` | Change KDF algorithm/parameters (PBKDF2↔Argon2id, iterations, memory, parallelism) |
| `vaultwarden_post_keys` | `ACCOUNTSTOOL` | Upload/set the user RSA keypair (encrypted private key + public key) |
| `vaultwarden_post_org_import` | `ORGANIZATIONSTOOL` | Bulk import ciphers directly into an organization (personal-vault-style import scoped to an org) |
| `vaultwarden_post_org_keys` | `ORGANIZATIONSTOOL` | Upload the organization’s RSA keypair at org-creation time |
| `vaultwarden_post_organization` | `ORGANIZATIONSTOOL` | Update organization settings (POST alias) |
| `vaultwarden_post_organization_collection_delete` | `ORGANIZATIONSTOOL` | Delete a collection (POST alias) |
| `vaultwarden_post_organization_collection_update` | `ORGANIZATIONSTOOL` | Update a collection (POST alias) |
| `vaultwarden_post_organization_collections` | `ORGANIZATIONSTOOL` | Create a collection |
| `vaultwarden_post_password` | `ACCOUNTSTOOL` | Change master password |
| `vaultwarden_post_profile` | `ACCOUNTSTOOL` | Update profile fields (legacy POST alias of PUT) |
| `vaultwarden_post_rotatekey` | `ACCOUNTSTOOL` | Full account key rotation: re-encrypt user key, private key, and every cipher/folder/send key |
| `vaultwarden_post_send` | `SENDSTOOL` | Create a text-type (or metadata-only) Send |
| `vaultwarden_post_send_file` | `SENDSTOOL` | Create a file-type Send (legacy single-phase upload) |
| `vaultwarden_post_send_file_v2` | `SENDSTOOL` | Begin a file-type Send (v2): register metadata, get upload URL |
| `vaultwarden_post_send_file_v2_data` | `SENDSTOOL` | Upload the encrypted Send file bytes (v2 second phase) |
| `vaultwarden_post_set_password` | `ACCOUNTSTOOL` | Set initial master password (post-SSO/key-connector account provisioning) |
| `vaultwarden_post_settings_domains` | `MISCTOOL` | Set equivalent-domains list |
| `vaultwarden_post_sstamp` | `ACCOUNTSTOOL` | Rotate security stamp (invalidates all other sessions/JWTs) |
| `vaultwarden_post_verify_email` | `ACCOUNTSTOOL` | Request email verification (resend verify link) for current email |
| `vaultwarden_post_verify_email_token` | `ACCOUNTSTOOL` | Verify current email address ownership via emailed token |
| `vaultwarden_prelogin_password` | `IDENTITYTOOL` | Variant prelogin returning the newer MasterPasswordUnlockData shape |
| `vaultwarden_prevalidate` | `IDENTITYTOOL` | Pre-validate an SSO organization identifier before redirecting to the IdP |
| `vaultwarden_profile` | `ACCOUNTSTOOL` | Get own user profile (email, name, org memberships, premium status) |
| `vaultwarden_purge_org_vault` | `CIPHERSTOOL` | Irreversibly delete ALL ciphers in an organization |
| `vaultwarden_purge_personal_vault` | `CIPHERSTOOL` | Irreversibly delete ALL of the caller’s personal ciphers (and folders) |
| `vaultwarden_put_auth_request` | `ACCOUNTSTOOL` | Approve/deny an auth request from an already-approved device |
| `vaultwarden_put_avatar` | `ACCOUNTSTOOL` | Set avatar color |
| `vaultwarden_put_cipher` | `CIPHERSTOOL` | Update a cipher (PUT alias) |
| `vaultwarden_put_cipher_admin` | `CIPHERSTOOL` | Update a cipher via the admin path |
| `vaultwarden_put_cipher_partial` | `CIPHERSTOOL` | Partial update (PUT alias) |
| `vaultwarden_put_cipher_share` | `CIPHERSTOOL` | Share a cipher (PUT alias) |
| `vaultwarden_put_cipher_share_selected` | `CIPHERSTOOL` | Bulk share multiple ciphers to an org |
| `vaultwarden_put_clear_device_token` | `ACCOUNTSTOOL` | Clear a device push token (public, used by push relay callbacks) |
| `vaultwarden_put_collections2_update` | `CIPHERSTOOL` | Set the collections a cipher belongs to (v2, returns updated cipher) |
| `vaultwarden_put_collections_admin` | `CIPHERSTOOL` | Set collections via admin path |
| `vaultwarden_put_collections_update` | `CIPHERSTOOL` | Set the collections a cipher belongs to (legacy v1) |
| `vaultwarden_put_device_token` | `ACCOUNTSTOOL` | Set/update device push token (PUT alias) |
| `vaultwarden_put_emergency_access` | `EMERGENCY_ACCESSTOOL` | Update wait-time/type of an emergency-access grant |
| `vaultwarden_put_folder` | `FOLDERSTOOL` | Rename a folder |
| `vaultwarden_put_group` | `ORGANIZATIONSTOOL` | Update a group |
| `vaultwarden_put_group_members` | `ORGANIZATIONSTOOL` | Set which members belong to a group |
| `vaultwarden_put_member` | `ORGANIZATIONSTOOL` | Edit a member (role, collection access, groups) |
| `vaultwarden_put_organization` | `ORGANIZATIONSTOOL` | Update organization settings (name, billing email, etc.) |
| `vaultwarden_put_organization_collection_update` | `ORGANIZATIONSTOOL` | Update a collection (rename, reassign users/groups) |
| `vaultwarden_put_policy` | `ORGANIZATIONSTOOL` | Update one policy by type |
| `vaultwarden_put_policy_vnext` | `ORGANIZATIONSTOOL` | Update one policy by type (newer response shape) |
| `vaultwarden_put_profile` | `ACCOUNTSTOOL` | Update profile fields (name, avatar color) |
| `vaultwarden_put_recover_account` | `ORGANIZATIONSTOOL` | Admin completes account-recovery: submits a brand-new master key for a member using the org-held reset_password_key |
| `vaultwarden_put_remove_password` | `SENDSTOOL` | Remove the password requirement from a Send |
| `vaultwarden_put_reset_password` | `ORGANIZATIONSTOOL` | Alias/step of admin-initiated password reset |
| `vaultwarden_put_reset_password_enrollment` | `ORGANIZATIONSTOOL` | Member opts in/out of admin password-reset recovery |
| `vaultwarden_put_send` | `SENDSTOOL` | Update a Send (name/notes/text/expiry/password/max access count) |
| `vaultwarden_put_settings_domains` | `MISCTOOL` | Set equivalent-domains list (PUT alias) |
| `vaultwarden_register_finish` | `IDENTITYTOOL` | Finish registration after email verification (submits the same keyset payload as identity_register) |
| `vaultwarden_register_verification_email` | `IDENTITYTOOL` | Send the registration email-verification code |
| `vaultwarden_reinvite_member` | `ORGANIZATIONSTOOL` | Resend one pending invite |
| `vaultwarden_reject_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantor rejects/cancels an in-progress request |
| `vaultwarden_remove_2fa` | `ADMINTOOL` | Strip all 2FA methods from a user (admin recovery action) |
| `vaultwarden_request_otp` | `TWO_FACTORTOOL` | Request an OTP (emailed) to re-verify identity before a sensitive action |
| `vaultwarden_resend_invite` | `EMERGENCY_ACCESSTOOL` | Grantor resends a pending emergency-access invite |
| `vaultwarden_resend_user_invite` | `ADMINTOOL` | Resend a pending registration invite email |
| `vaultwarden_restore_cipher_put` | `CIPHERSTOOL` | Restore one cipher from trash |
| `vaultwarden_restore_cipher_put_admin` | `CIPHERSTOOL` | Restore one cipher from trash via admin path |
| `vaultwarden_restore_cipher_selected` | `CIPHERSTOOL` | Bulk restore from trash |
| `vaultwarden_restore_cipher_selected_admin` | `CIPHERSTOOL` | Bulk restore from trash via admin path |
| `vaultwarden_restore_member` | `ORGANIZATIONSTOOL` | Restore a revoked member |
| `vaultwarden_restore_member_vnext` | `ORGANIZATIONSTOOL` | Restore a revoked member (newer response shape) |
| `vaultwarden_revision_date` | `ACCOUNTSTOOL` | Get last vault revision timestamp (used by clients to decide whether to sync) |
| `vaultwarden_revoke_member` | `ORGANIZATIONSTOOL` | Revoke one member’s access without removing them (keeps external_id/history) |
| `vaultwarden_send_email` | `TWO_FACTORTOOL` | Send/resend the email-2FA setup verification code |
| `vaultwarden_send_email_login` | `TWO_FACTORTOOL` | Send the 2FA email code during login (pre-auth, device-scoped) |
| `vaultwarden_sync` | `CIPHERSTOOL` | Full vault sync: ciphers, folders, collections, sends, org/policy/domain metadata in one payload |
| `vaultwarden_takeover_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantee begins password takeover: server returns grantor’s KDF settings + encrypted key |
| `vaultwarden_test_smtp` | `ADMINTOOL` | Send a test email to verify SMTP configuration |
| `vaultwarden_unarchive_cipher_put` | `CIPHERSTOOL` | Unarchive one cipher |
| `vaultwarden_unarchive_cipher_selected` | `CIPHERSTOOL` | Bulk unarchive ciphers |
| `vaultwarden_update_membership_type` | `ADMINTOOL` | Change a user’s org role from the admin panel |
| `vaultwarden_update_revision_users` | `ADMINTOOL` | Force a client-sync revision bump for one/many users |
| `vaultwarden_verify_otp` | `TWO_FACTORTOOL` | Verify the OTP from request_otp |
| `vaultwarden_verify_password` | `ACCOUNTSTOOL` | Verify current master password hash (used before sensitive UI actions) |
| `vaultwarden_version` | `MISCTOOL` | Return server version string |
| `vaultwarden_view_emergency_access` | `EMERGENCY_ACCESSTOOL` | Grantee views the grantor’s vault (read-only) after approval/wait elapses |

</details>

_8 action-routed tool(s) · 281 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (**`intent` default** — the six verb-tools, granular set loaded on demand · `condensed` action-routed · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

The tool domains this package registers (final names, once every domain module lands):
`vaultwarden_system`, `vaultwarden_accounts`, `vaultwarden_ciphers`, `vaultwarden_folders`,
`vaultwarden_organizations`, `vaultwarden_sends`, `vaultwarden_admin`, and
`vaultwarden_maintenance`. Destructive operations require `"confirm": true`.

## Documentation

Full documentation is published to the GitHub Pages site and mirrored under `docs/`:

- [Documentation site](https://knuckles-team.github.io/vaultwarden-mcp/)
- [Overview](docs/overview.md)
- [Installation](docs/installation.md)
- [Usage](docs/usage.md)
- [Deployment](docs/deployment.md)
- [Platform](docs/platform.md)
- [Concept Registry](docs/concepts.md)

See `AGENTS.md` for domain-specific traps (the soft-vs-hard delete routes, the upper-case
credential alias rule, and the KG metadata-only boundary).

---

## Repository Owners

<img width="100%" height="180em" src="https://github-readme-stats.vercel.app/api?username=example&show_icons=true&hide_border=true&&count_private=true&include_all_commits=true" />

![GitHub followers](https://img.shields.io/github/followers/example)
![GitHub User's stars](https://img.shields.io/github/stars/example)

---

## Contribute

Contributions are welcome! Please ensure code quality by executing local checks before submitting pull requests:
- Format code using `ruff format .`
- Lint code using `ruff check .`
- Validate type-safety with `mypy .`
- Execute test suites using `pytest`


<!-- BEGIN agent-utilities-deployment (generated; do not edit between markers) -->

## Deploy with `agent-utilities-deployment`

Provision this package with the consolidated **`agent-utilities-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `vaultwarden-mcp` with agent-utilities-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "vaultwarden-mcp[mcp]"`, then run `vaultwarden-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `vaultwarden-mcp` |
| Immutable container | deploy `registry.example.invalid/vaultwarden-mcp@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-utilities-deployment -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, GraphOS delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
