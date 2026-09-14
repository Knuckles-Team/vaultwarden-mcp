# AGENTS.md

> Claude Code loads this file via `CLAUDE.md` (`@AGENTS.md` import) — the two stay
> in sync. Edit **this** file, not `CLAUDE.md`.

## Tech Stack & Architecture
- Language/Version: Python 3.12–3.14
- Core Libraries: `agent-utilities`, `fastmcp`, `pydantic-ai`, `cryptography`, `argon2-cffi`
- Key principles: Functional patterns, Pydantic for data validation, asynchronous tool execution.
- Architecture:
    - `vaultwarden_mcp/api/`: HTTP transport (`api_client_base.py`), the 281-operation
      route catalog (`_routes.py`), and the generated verbose-tool parameter manifest
      (`_operation_manifest.py`).
    - `vaultwarden_mcp/mcp/`: Modular folder for action-routed dynamic MCP tool tags
      (`vaultwarden_system`, `vaultwarden_accounts`, `vaultwarden_ciphers`,
      `vaultwarden_folders`, `vaultwarden_organizations`, `vaultwarden_sends`,
      `vaultwarden_admin`, `vaultwarden_maintenance`).
    - `vaultwarden_mcp/crypto/`: Pluggable decrypted-vault backends (`native`, `bw_cli`)
      behind the `VaultCrypto` protocol in `crypto/base.py`.
    - `vaultwarden_mcp/vault/dedupe.py`: Pure planning + bulk-soft-delete apply for
      duplicate vault items.
    - `vaultwarden_mcp/kg_ingest.py`: Metadata-only knowledge-graph ingestion.
    - `vaultwarden_mcp/mcp_server.py`: Main MCP server entry point and tool registration.
    - `vaultwarden_mcp/agent_server.py`: Pydantic AI agent definition and logic.

### Architecture Diagram
```mermaid
graph TD
    User([User/A2A]) --> Server[A2A Server / FastAPI]
    Server --> Agent[Pydantic AI Agent]
    Agent --> Skills[Modular Skills]
    Agent --> MCP[MCP Server / FastMCP]
    MCP --> Client[API Client / Wrapper]
    Client --> ExternalAPI([Vaultwarden Server])
    MCP --> Crypto[VaultCrypto: native | bw_cli]
    Crypto --> ExternalAPI
```

### Workflow Diagram
```mermaid
sequenceDiagram
    participant U as User
    participant S as Server
    participant A as Agent
    participant T as MCP Tool
    participant API as Vaultwarden API

    U->>S: Request
    S->>A: Process Query
    A->>T: Invoke Tool
    T->>API: API Request
    API-->>T: API Response
    T-->>A: Tool Result
    A-->>S: Final Response
    S-->>U: Output
```

## Commands (run these exactly)
# Installation
pip install .[all]

# Quality & Linting (run from project root)
pre-commit run --all-files

# Execution Commands
# Run MCP Server
vaultwarden-mcp
# Run Agent
vaultwarden-agent

## Project Structure Quick Reference
- MCP Entry Point → `vaultwarden_mcp/mcp_server.py`
- Agent Entry Point → `vaultwarden_mcp/agent_server.py`
- Source Code → `vaultwarden_mcp/`
- API route catalog + transport → `vaultwarden_mcp/api/`
- MCP tool modules → `vaultwarden_mcp/mcp/`
- Decrypted-vault crypto backends → `vaultwarden_mcp/crypto/`
- Deduplication → `vaultwarden_mcp/vault/dedupe.py`
- Knowledge-graph ingestion → `vaultwarden_mcp/kg_ingest.py`
- Tests → `tests/`
- Documentation → `docs/` (published via mkdocs + GitHub Pages)

## Code Style & Conventions
**Always:**
- Use `agent-utilities` for common patterns (e.g., `create_mcp_server`, `create_agent_server`).
- Define input/output models using Pydantic.
- Include descriptive docstrings for all tools (they are used as tool descriptions for LLMs).
- Check for optional dependencies using `try/except ImportError`.

## Dos and Don'ts
**Do:**
- Run `pre-commit` before pushing changes.
- Use existing patterns from `agent-utilities`.
- Keep tools focused and idempotent where possible.
- Prefer soft delete (trash) over permanent deletion; require `confirm: true` for anything
  destructive.

**Don't:**
- Use `cd` commands in scripts; use absolute paths or relative to project root.
- Add new dependencies to `dependencies` in `pyproject.toml` without checking `optional-dependencies` first.
- Hardcode endpoints, credentials, or trust material; use AgentConfig runtime references.

## Safety & Boundaries
**Always do:**
- Run lint/test via `pre-commit`.
- Use `agent-utilities` base classes.

**Ask first:**
- Major refactors of `mcp_server.py` or `agent_server.py`.
- Deleting or renaming public tool functions.

**Never do:**
- Commit resolved provider values, certificate paths, or secrets.
- Modify `agent-utilities` or `universal-skills` files from within this package.
- Print, log, or ingest vault contents (item names, usernames, passwords, notes, URIs,
  TOTP seeds, custom fields, attachments, or any key material) — see
  [Domain notes](#domain-notes-vaultwardenbitwarden-specific) below.

## When Stuck
- Propose a plan first before making large changes.
- Check `agent-utilities` documentation for existing helpers.

## Domain notes (Vaultwarden/Bitwarden-specific)

Read this before touching `auth.py`, `api/api_client_base.py`, `crypto/`, or
`kg_ingest.py`.

- **Three auth modes, one client.** Every request declares `auth="user" | "admin" |
  "none"`. `user` mints a `client_credentials` bearer token from the account's personal
  API key and caches it until shortly before expiry; `admin` posts the instance admin
  token to `/admin` once and reuses the resulting `VW_ADMIN` session cookie; `none` is for
  public endpoints (`/alive`, `/api/version`, `/api/config`, prelogin). A request never
  silently escalates from one mode to another.
- **The soft-vs-hard delete trap.** In Vaultwarden, `PUT /api/ciphers/delete` is a
  **soft** delete — it moves items to trash, recoverable for 30 days. `POST
  /api/ciphers/delete` and `DELETE /api/ciphers` are **permanent**. Only the `PUT` route
  is ever wired to a bulk-delete tool action (`VaultwardenApiBase.soft_delete_ciphers`);
  do not add a shortcut to either permanent route without an explicit, separately
  confirmed "purge" action and unambiguous user intent.
- **Upper-case credential aliases.** `provider_configs.vaultwarden.credential_refs` uses
  fixed, upper-case aliases — `CLIENT_ID`, `CLIENT_SECRET`, `MASTER_PASSWORD`,
  `ADMIN_TOKEN` — because `AgentConfig` requires upper-case alias keys. Never introduce a
  lower-case or differently-named alias; every consumer (`auth.py`, both crypto backends)
  reads these exact keys.
- **KG ingestion is metadata-only, by construction, not by convention.** `kg_ingest.py`
  only ever builds nodes from identifiers, type codes, lifecycle dates, counts, and
  relationship targets (see `vaultwarden_mcp/ontology/vaultwarden.ttl`). When adding a new
  ingest mapping, whitelist fields explicitly (as the existing `_item_node`/`_item_edges`
  helpers do) — never pass a raw decrypted or encrypted record through. If a field could
  ever hold user-entered vault content, it does not belong in the graph.
- **Two crypto backends, one contract.** `native` (`crypto/native.py`, `crypto/keys.py`,
  `crypto/encstring.py`) is a pure-Python reimplementation of Bitwarden's key derivation
  and EncString handling, validated against the SDK's own published test vectors
  (`tests/test_crypto_vectors.py`); it verifies the EncString MAC before ever attempting
  decryption and only accepts strict type-2 EncStrings. `bw_cli` (`crypto/bw_cli.py`)
  delegates to an installed Bitwarden CLI in a private, per-instance
  `BITWARDENCLI_APPDATA_DIR` — never the invoking user's real `bw` login state — and
  passes secrets only through the child process environment, never argv. Both backends
  implement the same `VaultCrypto` protocol (`crypto/base.py`) and exchange records in the
  Bitwarden CLI JSON shape, so higher-level code (dedupe, MCP tools) is backend-agnostic.
- **Errors name ids, never contents.** `VaultwardenApiError` truncates and never embeds
  request bodies, tokens, or credentials; crypto failures name the item id, never its
  plaintext or ciphertext. Preserve that discipline in any new error path.

## ⛔ No Scratch or Temporary Files in Repository

**NEVER write any of the following to this repository:**
- Temporary test scripts (`test_*.py`, `debug_*.py` outside of `tests/`)
- Scratch scripts or experimental one-off files
- Log files (`.log`, `.txt` command output)
- Random text files with command output or debug dumps
- Any file that is NOT production source code, tests in `tests/`, or documentation

**Why:** These files expose private filesystem paths, credentials, and internal infrastructure details when pushed to GitHub publicly.

**Where to put scratch work instead:**
- Use `~/workspace/scratch/` for temporary scripts and experiments
- Use `~/workspace/reports/` for command output and reports
- Keep test scripts in the `tests/` directory following proper pytest conventions

## ⛔ Keep the Repository Root Pristine — No Scratch / Temp / Debug Files

**The repository ROOT must contain only canonical project files** (packaging,
config, docs, lockfiles). The only hidden directories allowed at root are
`.git/`, `.github/`, and `.specify/` (plus a local, git-ignored `.venv/`).

**NEVER write any of the following — anywhere in the repo, and ESPECIALLY at the root:**
- One-off / debug / migration scripts: `fix_*.py`, `migrate_*.py`, `refactor_*.py`,
  `replace_*.py`, `update_*.py`, `debug_*.py`, or `test_*.py` **at the root**
  (real tests live in `tests/` only).
- Databases / data dumps: `*.db`, `*.db-wal`, `*.sqlite*`, `*.corrupted`.
- Logs / command output: `*.log`, scratch `*.txt`, `*.orig`, `*.rej`, `*.bak`.
- Build artifacts: `*.tsbuildinfo`, compiled binaries, coverage files.
- AI agent scratch directories: `.agent/`, `.agents/`, `.agent_data/`, `.tmp/`,
  `.hypothesis/`, or any per-tool cache committed to git.
- Any file that is NOT production source, a test in `tests/`, documentation, or
  a recognized config/lockfile.

**Why:** scratch at the root leaks private paths/credentials, bloats the tree,
and erodes a pristine codebase.

**Where scratch goes instead:** `~/workspace/scratch/` (experiments),
`~/workspace/reports/` (command output); tests go in `tests/` (pytest).
Before finishing a task, run `git status` and confirm no stray root files were added.

## Working Discipline — think, simplify, stay surgical, verify

These four habits cut the most common LLM coding mistakes. For trivial tasks, use
judgment; the bias here is correctness over speed.

- **Think before coding.** State your assumptions explicitly. If a request has more than
  one reasonable reading, surface the options instead of silently picking one. If a
  simpler approach exists, say so and push back when warranted. When something is
  genuinely unclear, stop and name what's confusing — ask, don't guess.
- **Simplicity first.** Write the minimum code that solves the stated problem — no
  speculative features, no abstraction for single-use code, no configurability that
  wasn't requested, no error handling for impossible states. If you wrote 200 lines and
  it could be 50, rewrite it. (Name code from its purpose, never `wave0`/`phase2`/`v2`.)
- **Stay surgical.** Every changed line should trace directly to the task. Don't refactor,
  reformat, or "improve" working code adjacent to your change; match the existing style
  even where you'd do it differently. Remove only the imports/symbols your own change
  orphaned; if you spot unrelated dead code, mention it rather than deleting it inline.
  *Exception — the Quality Bar below:* lint/format/type errors the pre-commit gate flags
  get fixed regardless of who introduced them. In short: **surgical on behavior, clean on
  lint.**
- **Verify against a goal.** Turn the task into a checkable outcome before you start:
  "fix the bug" → "write a failing test that reproduces it, then make it pass"; "add
  validation" → "tests for the invalid inputs pass". For multi-step work, state the short
  plan and the check for each step, then loop until the checks pass.

## Quality Bar — Leave the Codebase Clean (REQUIRED)

After completing any code change, run the project's pre-commit suite and drive it
**fully green** before committing:

```bash
pre-commit run --all-files
```

Resolve **every** issue it reports — failures, lint errors, type errors, and
warnings — **including problems that pre-date your change and were not caused by
your edits**. The standing goal is a clean, working codebase with **no errors and
no warnings**. Do not silence checks (`# noqa`, `# type: ignore`, `SKIP=`,
`--no-verify`) to force green unless the exception is already documented in this
file as a known, unavoidable limitation. Only commit once `pre-commit run
--all-files` passes cleanly; if a check legitimately cannot pass, stop and explain
why rather than bypassing it.

## Working with Git Worktrees (multi-session)

Multiple agents/sessions work the configured package repos concurrently. **Do not
edit the canonical checkout** (`$AGENT_PACKAGES_ROOT/<repo>`) — a
background `repository-manager` sync can reset its working tree and discard
uncommitted edits. Take your own git worktree on your own branch instead:

```bash
# preferred — repository-manager MCP:
rm_worktree add <repo> <your-branch>      # path comes from repository-manager config

# raw-git fallback:
git -C "$AGENT_PACKAGES_ROOT/<repo>" checkout main
git -C "$AGENT_PACKAGES_ROOT/<repo>" worktree add   "$AGENT_WORKTREES_ROOT/<repo>/<branch>" -b <branch>
```

Work in the worktree and **commit often** (commits survive a working-tree reset).
Each session must use a **distinct branch** — git allows a branch in only one
worktree, which is what keeps concurrent sessions from colliding. Configure the
worktree root outside the repository-manager workspace scan.

**Finishing work in a worktree** — run this sequence before calling it done:
1. **Pre-commit green** — `pre-commit run --all-files`; resolve every issue per the
   Quality Bar above (including pre-existing), no `--no-verify`.
2. **Commit** in the worktree.
3. **Merge to main locally** — `rm_worktree merge <repo> <branch> --into main`
   (or `git merge --no-ff`). Push only when the user asks.
4. **Clean up** — remove the worktree and delete the merged branch:
   `rm_worktree remove <repo> <branch> --delete-branch`; `rm_worktree prune` clears
   stale entries. (Raw-git: `git worktree remove <path> && git branch -d <branch>`.)

<!-- BEGIN concept-coordination (generated) -->
## Concept-ID Coordination (multi-session)

Working in parallel with other sessions/worktrees? **Reserve a concept id before you write its `CONCEPT:` marker** so two sessions never collide:

```bash
agent-utilities --json concept reserve --ns VW-ECO.mcp.<domain>-operations   # or a package prefix, e.g. VW
```

Full protocol (ledger, merge=union, reconcile, MCP/REST): <https://knuckles-team.github.io/agent-utilities/concept_coordination/>
<!-- END concept-coordination (generated) -->

## Version & lockfile drift edict (keep the version mirrors AND the lock in sync)

The two most common release-breakers in this fleet are **version drift** (the version in
`pyproject.toml`/`.bumpversion.cfg` advancing while `README.md`, `docker/Dockerfile`, and the
module `__version__`s lag) and a **stale `uv.lock`** (shipping known-vulnerable transitive deps).
A version mismatch makes the next `bump-my-version` throw `VersionNotFoundException`; a stale lock
is what Dependabot flags. Rules:

1. **Never hand-edit a version string.** Change the version ONLY via
   `bump-my-version bump {patch|minor|major}` (a.k.a. `bump2version`), which rewrites every file
   registered in `.bumpversion.cfg` in one atomic, tagged commit. If you edited the version in
   `pyproject.toml` by hand, you created drift — revert and use the bumper.
2. **Every version-bearing file must be registered in `.bumpversion.cfg`** — at minimum
   `pyproject.toml` AND `README.md`, plus `docker/Dockerfile`, `a2a.json`, and both module
   `__version__`s (`mcp_server.py`, `agent_server.py`). Never add a file that embeds the
   version without a `[bumpversion:file:...]` entry for it.
3. **Re-lock on every dependency change.** After editing `pyproject.toml` deps/extras, run
   `uv lock` and commit `uv.lock` in the SAME change. The `uv-lock` pre-commit hook runs with
   `--locked` and fails on drift — never bypass it. The committed `uv.lock` is the
   Dependabot/security surface.
4. **Patch CVEs with a version floor at the source, then re-lock.** `uv` resolves one version
   graph-wide, so a lower-bound in the extra that pulls a dependency raises it for the whole lock.

## Known, unavoidable limitations

- `vaultwarden_mcp/crypto/encstring.py` carries one `# nosec B303`. Bitwarden's
  EncString type 4 (`Rsa2048_OaepSha1_B64`) is RSA-OAEP with SHA-1, and organization keys
  on real servers are still wrapped that way, so unwrapping them requires SHA-1 inside
  OAEP. The package never produces new SHA-1 wraps unless a caller explicitly asks for
  type 4, and SHA-1 is not used as a standalone digest anywhere.
