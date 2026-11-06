---
name: vaultwarden-organization-administration
skill_type: skill
description: >-
  Administer a Vaultwarden organization through vaultwarden-mcp: members, groups, collections, policies and account recovery. Use for access reviews and joiner-mover-leaver work.
license: MIT
tags: [vaultwarden, organization, access]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# Vaultwarden organization administration

Organization objects are addressed by org_id; list before you change.

## Rules

- Never remove or revoke the last owner.
- Bulk tools take an explicit id list only.
- Read the object back after each change.

## Task workflows

### create-and-update-organization

Create, read, change and delete an organization. Contract steps, in order:

1. `vaultwarden_create_organization`(; optional json_body, params, form)
2. `vaultwarden_organizations_delete_organization`(org_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
3. `vaultwarden_post_delete_organization`(org_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
4. `vaultwarden_get_organization`(org_id; optional json_body, params, form)
5. `vaultwarden_put_organization`(org_id; optional json_body, params, form)
6. `vaultwarden_post_organization`(org_id; optional json_body, params, form)
7. `vaultwarden_get_auto_enroll_status`(identifier; optional json_body, params, form)
8. `vaultwarden_get_org_details`(; optional data, json_body, params, form)
9. `vaultwarden_get_org_domain_sso_verified`(; optional json_body, params, form)
10. `vaultwarden_post_org_import`(; optional query, json_body, params, form)
11. `vaultwarden_get_plans`(; optional json_body, params, form)
12. `vaultwarden_get_billing_metadata`(_org_id; optional json_body, params, form)
13. `vaultwarden_get_billing_warnings`(_org_id; optional json_body, params, form)
14. `vaultwarden_get_self_host_billing_metadata`(_org_id; optional json_body, params, form)
15. `vaultwarden_organizations_post_api_key`(org_id; optional json_body, params, form)
16. `vaultwarden_organizations_rotate_api_key`(org_id; optional json_body, params, form)

### manage-organization-members

Invite, confirm, change, revoke, restore and remove members. Contract steps, in order:

1. `vaultwarden_leave_organization`(org_id; optional json_body, params, form)
2. `vaultwarden_get_members`(org_id; optional data, json_body, params, form)
3. `vaultwarden_post_org_keys`(org_id; optional json_body, params, form)
4. `vaultwarden_organizations_send_invite`(org_id; optional json_body, params, form)
5. `vaultwarden_bulk_reinvite_members`(org_id; optional json_body, params, form)
6. `vaultwarden_reinvite_member`(org_id, member_id; optional json_body, params, form)
7. `vaultwarden_organizations_accept_invite`(org_id, member_id; optional json_body, params, form)
8. `vaultwarden_bulk_confirm_invite`(org_id; optional json_body, params, form)
9. `vaultwarden_confirm_invite`(org_id, member_id; optional json_body, params, form)
10. `vaultwarden_get_org_user_mini_details`(org_id; optional json_body, params, form)
11. `vaultwarden_get_user`(org_id, member_id; optional data, json_body, params, form)
12. `vaultwarden_put_member`(org_id, member_id; optional json_body, params, form)
13. `vaultwarden_edit_member`(org_id, member_id; optional json_body, params, form)
14. `vaultwarden_bulk_delete_member`(org_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
15. `vaultwarden_delete_member`(org_id, member_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
16. `vaultwarden_bulk_public_keys`(org_id; optional json_body, params, form)
17. `vaultwarden_revoke_member`(org_id, member_id; optional json_body, params, form)
18. `vaultwarden_bulk_revoke_members`(org_id; optional json_body, params, form)
19. `vaultwarden_restore_member_vnext`(org_id, member_id; optional json_body, params, form)
20. `vaultwarden_restore_member`(org_id, member_id; optional json_body, params, form)
21. `vaultwarden_bulk_restore_members`(org_id; optional json_body, params, form)
22. `vaultwarden_get_organization_public_key`(org_id; optional json_body, params, form)
23. `vaultwarden_get_organization_keys`(org_id; optional json_body, params, form)

### manage-organization-groups

Create groups and set their members and access. Contract steps, in order:

1. `vaultwarden_get_groups`(org_id; optional json_body, params, form)
2. `vaultwarden_get_groups_details`(org_id; optional json_body, params, form)
3. `vaultwarden_post_group`(org_id, group_id; optional json_body, params, form)
4. `vaultwarden_post_groups`(org_id; optional json_body, params, form)
5. `vaultwarden_put_group`(org_id, group_id; optional json_body, params, form)
6. `vaultwarden_get_group_details`(org_id, group_id; optional json_body, params, form)
7. `vaultwarden_post_delete_group`(org_id, group_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
8. `vaultwarden_delete_group`(org_id, group_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
9. `vaultwarden_bulk_delete_groups`(org_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
10. `vaultwarden_get_group`(org_id, group_id; optional json_body, params, form)
11. `vaultwarden_get_group_members`(org_id, group_id; optional json_body, params, form)
12. `vaultwarden_put_group_members`(org_id, group_id; optional json_body, params, form)
13. `vaultwarden_post_delete_group_member`(org_id, group_id, member_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### manage-organization-collections

Create collections and set who can use them. Contract steps, in order:

1. `vaultwarden_get_user_collections`(; optional json_body, params, form)
2. `vaultwarden_get_org_collections`(org_id; optional json_body, params, form)
3. `vaultwarden_get_org_collections_details`(org_id; optional json_body, params, form)
4. `vaultwarden_post_organization_collections`(org_id; optional json_body, params, form)
5. `vaultwarden_post_bulk_access_collections`(org_id; optional json_body, params, form)
6. `vaultwarden_put_organization_collection_update`(org_id, col_id; optional json_body, params, form)
7. `vaultwarden_post_organization_collection_update`(org_id, col_id; optional json_body, params, form)
8. `vaultwarden_delete_organization_collection`(org_id, col_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
9. `vaultwarden_post_organization_collection_delete`(org_id, col_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
10. `vaultwarden_bulk_delete_organization_collections`(org_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
11. `vaultwarden_get_org_collection_detail`(org_id, col_id; optional json_body, params, form)
12. `vaultwarden_get_collection_users`(org_id, col_id; optional json_body, params, form)
13. `vaultwarden_post_bulk_collections`(; optional json_body, params, form)

### set-organization-policies

Read and change organization policies. Contract steps, in order:

1. `vaultwarden_list_policies`(org_id; optional json_body, params, form)
2. `vaultwarden_list_policies_token`(org_id; optional token, json_body, params, form)
3. `vaultwarden_get_dummy_master_password_policy`(; optional json_body, params, form)
4. `vaultwarden_get_master_password_policy`(org_id; optional json_body, params, form)
5. `vaultwarden_get_policy`(org_id, pol_type; optional json_body, params, form)
6. `vaultwarden_put_policy`(org_id, pol_type; optional json_body, params, form)
7. `vaultwarden_put_policy_vnext`(org_id, pol_type; optional json_body, params, form)

### recover-member-accounts

Enroll in and use password reset and account recovery. Contract steps, in order:

1. `vaultwarden_put_recover_account`(org_id, member_id; optional json_body, params, form)
2. `vaultwarden_put_reset_password`(org_id, member_id; optional json_body, params, form)
3. `vaultwarden_get_reset_password_details`(org_id, member_id; optional json_body, params, form)
4. `vaultwarden_put_reset_password_enrollment`(org_id, user_id; optional json_body, params, form)
5. `vaultwarden_get_org_export`(org_id; optional json_body, params, form)
