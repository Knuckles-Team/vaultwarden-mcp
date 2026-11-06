---
name: vaultwarden-server-administration
skill_type: skill
description: >-
  Administer the Vaultwarden server through vaultwarden-mcp using the admin token: users, diagnostics, configuration and database backup. Use for server upkeep.
license: MIT
tags: [vaultwarden, admin, server]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# Vaultwarden server administration

The admin tools need the instance admin token. Check status and diagnostics first.

## Rules

- Back up the database before deleting users or changing config.
- Never print the admin token.
- Disable before delete when a user may return.

## Task workflows

### administer-users

Invite, disable, enable, sign out and delete server users. Contract steps, in order:

1. `vaultwarden_invite_user`(; optional json_body, params, form)
2. `vaultwarden_get_users_json`(; optional json_body, params, form)
3. `vaultwarden_get_user_by_mail_json`(mail; optional json_body, params, form)
4. `vaultwarden_get_user_json`(user_id; optional json_body, params, form)
5. `vaultwarden_delete_user`(user_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
6. `vaultwarden_delete_sso_user`(user_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
7. `vaultwarden_deauth_user`(user_id; optional json_body, params, form)
8. `vaultwarden_disable_user`(user_id; optional json_body, params, form)
9. `vaultwarden_enable_user`(user_id; optional json_body, params, form)
10. `vaultwarden_remove_2fa`(user_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
11. `vaultwarden_resend_user_invite`(user_id; optional json_body, params, form)
12. `vaultwarden_update_membership_type`(; optional json_body, params, form)
13. `vaultwarden_update_revision_users`(; optional json_body, params, form)
14. `vaultwarden_admin_delete_organization`(org_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### administer-server

Read diagnostics, test mail, change server config and back up the database. Contract steps, in order:

1. `vaultwarden_test_smtp`(; optional json_body, params, form)
2. `vaultwarden_get_diagnostics_config`(; optional json_body, params, form)
3. `vaultwarden_get_diagnostics_http`(; optional code, json_body, params, form)
4. `vaultwarden_post_config`(; optional json_body, params, form)
5. `vaultwarden_delete_config`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
6. `vaultwarden_backup_db`(; optional json_body, params, form)

### manage-equivalent-domains

Read and change equivalent-domain settings. Contract steps, in order:

1. `vaultwarden_get_settings_domains`(; optional json_body, params, form)
2. `vaultwarden_post_settings_domains`(; optional json_body, params, form)
3. `vaultwarden_put_settings_domains`(; optional json_body, params, form)
