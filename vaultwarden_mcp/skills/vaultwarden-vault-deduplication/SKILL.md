---
name: vaultwarden-vault-deduplication
skill_type: skill
description: >-
  Remove duplicate items from a Vaultwarden (Bitwarden-compatible) vault using vaultwarden-mcp. Use when a vault holds repeated imports or duplicate logins, or someone asks to clean up, merge, or de-duplicate vault entries.
domain: infrastructure
tags:
  - vaultwarden
  - bitwarden
  - password-manager
  - deduplication
requires:
  - vaultwarden-mcp
metadata:
  version: '0.2.0'
---

# Vaultwarden Vault Deduplication

Scope: Remove duplicate items from a Vaultwarden (Bitwarden-compatible) vault using vaultwarden-mcp. Finds items whose every field matches (name, username, password, URIs, notes, TOTP, custom fields), keeps the most recently edited copy, and moves the extra copies to trash in one bulk soft delete, restorable for 30 days. Use when a vault holds repeated imports or duplicate logins, or someone asks to clean up, merge, or de-duplicate vault entries.

Deduplicate one vault account with the `vaultwarden_maintenance_plan_deduplication` and
`vaultwarden_maintenance_apply_deduplication` tools.

## How it works

- `vaultwarden_maintenance_plan_deduplication` unlocks the account, compares decrypted items, and returns
  identifiers only: how many items were scanned, the duplicate groups, and which copy of
  each group is kept. Nothing changes.
- `vaultwarden_maintenance_apply_deduplication` (needs `confirm=true`) recomputes the plan and moves every extra copy to trash in
  bulk. It refuses plans built in loose mode.
- Exact matching is the default and the only mode that may be applied. Loose matching
  (`loose=true`) compares only name, username, and URIs; its groups can differ in
  password or notes, so report them for manual review.
- Organization items are skipped unless `include_org=true` and the account can edit them.
- The keeper is the most recently edited copy; attachments, passkeys, and password
  history only break exact ties.

## Steps
1. Plan with `vaultwarden_maintenance_plan_deduplication` (leave `loose` off). Verify the response lists scanned, duplicate groups and extra copies, with identifiers only.
2. Show the `vaultwarden_maintenance_plan_deduplication` summary to the person. Verify they approve before anything is applied.
3. Apply with `vaultwarden_maintenance_apply_deduplication` and `confirm=true`. Verify the response reports the extra copies moved to trash.
4. Run `vaultwarden_maintenance_plan_deduplication` again. Verify it reports zero duplicate groups.

## Failure recovery
| Failure | Cause | Recovery |
|---------|-------|----------|
| Apply refused | The plan was built in loose mode, or `confirm=true` was missing | Rebuild with `vaultwarden_maintenance_plan_deduplication` without `loose`, then apply with `confirm=true` |
| Zero groups found but duplicates visible | Items differ in a field, or are organization items | Report loose-mode groups for manual review, or pass `include_org=true` if the account can edit them |
| Wrong copy trashed | The keeper is the most recently edited copy | Restore the item from trash with `vaultwarden_restore_cipher_put` within 30 days |

## Rules

- Always show the plan summary (scanned, groups, extra copies) and get approval before
  applying.
- Never print item names, usernames, passwords, notes, or URIs; refer to items by id.
- After applying, run the plan again and confirm it reports zero duplicate groups.
- Trash is recoverable for 30 days; never purge trash as part of deduplication.
