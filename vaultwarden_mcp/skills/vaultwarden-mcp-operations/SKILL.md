---
name: vaultwarden-mcp-operations
skill_type: skill
description: >-
  Operate vaultwarden-mcp through its governed MCP and GraphOS capabilities, including
  vault item, folder, organization, send, account, and server administration plus vault
  maintenance such as deduplication. Use when a request requires this provider's read,
  change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Vaultwarden Mcp Operations

Use the provider's governed MCP tools through GraphOS delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current condensed tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Safety contract

- Never print, log, persist, or ingest vault contents: item names, usernames, passwords,
  notes, URIs, TOTP seeds, custom fields, attachments, or any key material.
- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions;
  prefer soft delete (trash) over permanent deletion.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.
