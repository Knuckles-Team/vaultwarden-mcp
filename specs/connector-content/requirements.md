# CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `vaultwarden-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Caller chain: `vaultwarden-mcp` in `pyproject.toml` runs `scion_sdk.cli:serve`, which builds the server from the `scion_sdk.connector` entry point `vaultwarden_mcp:connector` (`vaultwarden_mcp/__init__.py:62`); the SDK `Connector` then lists the packaged skills, ontology and prompts. Shape: `pyproject.toml` entry point `vaultwarden-mcp` plus the `connector = Connector(.)` object in `vaultwarden_mcp/__init__.py`; the packaged `skills/`, `ontology/` and `prompts/` directories of `vaultwarden_mcp` are reused as is, with no connector-local registration code. Proving test (planned): `tests/test_default_content_surfaces.py::test_default_content_surfaces`. Proving test (planned): `tests/test_default_content_surfaces.py::test_default_content_surfaces`. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
