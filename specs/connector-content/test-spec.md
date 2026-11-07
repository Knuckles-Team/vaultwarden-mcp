# CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py::test_default_content_surfaces` (planned) | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |

## Negative and boundary cases

Each proving test above includes the refusal or error case that its row names. A vendor outage or an unauthorised call must return the SDK typed error.

## Quality and release proof

Run `uv run pytest tests` and `pre-commit run --all-files` from the repository root. A planned test is added by the code change that lands the row.

## Adoption of scion-sdk 0.10.0 (`CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT-R002`)

| Requirement | Test | Observation |
|---|---|---|
| `CONN-VAULTWARDEN-MCP-CONNECTOR-CONTENT-R002` | `tests/test_scion_sdk_0_10_imports.py::test_every_scion_sdk_import_resolves_on_the_pinned_release` | Every `scion_sdk` import resolves on the pinned release; a removed path fails the test. |
