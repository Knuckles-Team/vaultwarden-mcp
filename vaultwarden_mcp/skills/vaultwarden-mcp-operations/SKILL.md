---
name: vaultwarden-mcp-operations
skill_type: skill
description: >-
  Read, file, trash, restore and share vault items, keep attachments and Sends tidy, rotate item passwords and snapshot vault metadata through the vaultwarden-mcp tools. Use for day-to-day vault work. For duplicate clean-up use vaultwarden-vault-deduplication.
license: MIT
tags: [vaultwarden, passwords, vault]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# Vaultwarden operations

The vault is end-to-end encrypted. The vaultwarden_ciphers_* and vaultwarden_folders_* tools decrypt locally with the vault key; the other tools carry the encrypted API objects.

## Rules

- Never copy decrypted content (names, usernames, passwords, notes, URIs) anywhere but to the requester.
- Trash before delete; purge only on explicit request.
- Destructive tools take confirm=true; pass it only after the person agrees.

## Task workflows

### read-vault-items

Read vault items and folders, decrypted or as stored. Contract steps, in order:

1. `vaultwarden_ciphers_list_items`(; optional include_trash)
2. `vaultwarden_ciphers_get_item`(item_id)
3. `vaultwarden_folders_list_folders`(no arguments)
4. `vaultwarden_sync`(; optional data, json_body, params, form)
5. `vaultwarden_get_ciphers`(; optional json_body, params, form)
6. `vaultwarden_get_cipher`(cipher_id; optional json_body, params, form)
7. `vaultwarden_get_cipher_details`(cipher_id; optional json_body, params, form)
8. `vaultwarden_get_folders`(; optional json_body, params, form)
9. `vaultwarden_get_folder`(folder_id; optional json_body, params, form)

### write-vault-items

Create and change vault items and folders. Contract steps, in order:

1. `vaultwarden_ciphers_create_item`(item)
2. `vaultwarden_ciphers_edit_item`(item_id, item)
3. `vaultwarden_folders_create_folder`(name)
4. `vaultwarden_ciphers_list_items`(; optional include_trash)
5. `vaultwarden_post_ciphers_create`(; optional json_body, params, form)
6. `vaultwarden_post_ciphers`(; optional json_body, params, form)
7. `vaultwarden_post_cipher`(cipher_id; optional json_body, params, form)
8. `vaultwarden_put_cipher`(cipher_id; optional json_body, params, form)
9. `vaultwarden_post_cipher_partial`(cipher_id; optional json_body, params, form)
10. `vaultwarden_put_cipher_partial`(cipher_id; optional json_body, params, form)
11. `vaultwarden_post_folders`(; optional json_body, params, form)
12. `vaultwarden_post_folder`(folder_id; optional json_body, params, form)
13. `vaultwarden_put_folder`(folder_id; optional json_body, params, form)
14. `vaultwarden_post_ciphers_import`(; optional json_body, params, form)
15. `vaultwarden_post_cipher_share`(cipher_id; optional json_body, params, form)
16. `vaultwarden_put_cipher_share`(cipher_id; optional json_body, params, form)
17. `vaultwarden_put_cipher_share_selected`(; optional json_body, params, form)
18. `vaultwarden_move_cipher_selected`(; optional json_body, params, form)
19. `vaultwarden_move_cipher_selected_put`(; optional json_body, params, form)

### trash-and-restore-vault-items

Move items to the trash, restore, archive and permanently delete them. Contract steps, in order:

1. `vaultwarden_ciphers_move_to_trash`(ids)
2. `vaultwarden_delete_cipher`(cipher_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
3. `vaultwarden_delete_cipher_admin`(cipher_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
4. `vaultwarden_delete_cipher_post`(cipher_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
5. `vaultwarden_delete_cipher_post_admin`(cipher_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
6. `vaultwarden_delete_cipher_put`(cipher_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
7. `vaultwarden_delete_cipher_put_admin`(cipher_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
8. `vaultwarden_delete_cipher_selected`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
9. `vaultwarden_delete_cipher_selected_admin`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
10. `vaultwarden_delete_cipher_selected_post`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
11. `vaultwarden_delete_cipher_selected_post_admin`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
12. `vaultwarden_delete_cipher_selected_put`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
13. `vaultwarden_delete_cipher_selected_put_admin`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
14. `vaultwarden_restore_cipher_put`(cipher_id; optional json_body, params, form)
15. `vaultwarden_restore_cipher_put_admin`(cipher_id; optional json_body, params, form)
16. `vaultwarden_restore_cipher_selected`(; optional json_body, params, form)
17. `vaultwarden_restore_cipher_selected_admin`(; optional json_body, params, form)
18. `vaultwarden_archive_cipher_put`(cipher_id; optional json_body, params, form)
19. `vaultwarden_archive_cipher_selected`(; optional json_body, params, form)
20. `vaultwarden_unarchive_cipher_put`(cipher_id; optional json_body, params, form)
21. `vaultwarden_unarchive_cipher_selected`(; optional json_body, params, form)
22. `vaultwarden_delete_folder`(folder_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
23. `vaultwarden_delete_folder_post`(folder_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
24. `vaultwarden_purge_personal_vault`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### manage-item-attachments

Upload, read and delete file attachments of an item. Contract steps, in order:

1. `vaultwarden_get_attachment`(cipher_id, attachment_id; optional json_body, params, form)
2. `vaultwarden_post_attachment`(cipher_id; optional json_body, params, form)
3. `vaultwarden_post_attachment_admin`(cipher_id; optional json_body, params, form)
4. `vaultwarden_post_attachment_share`(cipher_id, attachment_id; optional json_body, params, form)
5. `vaultwarden_post_attachment_v2`(cipher_id; optional json_body, params, form)
6. `vaultwarden_post_attachment_v2_data`(cipher_id, attachment_id; optional json_body, params, form)
7. `vaultwarden_delete_attachment`(cipher_id, attachment_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
8. `vaultwarden_delete_attachment_admin`(cipher_id, attachment_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
9. `vaultwarden_delete_attachment_post`(cipher_id, attachment_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
10. `vaultwarden_delete_attachment_post_admin`(cipher_id, attachment_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### place-items-in-collections

Assign items to organization collections. Contract steps, in order:

1. `vaultwarden_post_collections2_update`(cipher_id; optional json_body, params, form)
2. `vaultwarden_post_collections_update`(cipher_id; optional json_body, params, form)
3. `vaultwarden_put_collections2_update`(cipher_id; optional json_body, params, form)
4. `vaultwarden_put_collections_update`(cipher_id; optional json_body, params, form)
5. `vaultwarden_post_collections_admin`(cipher_id; optional json_body, params, form)
6. `vaultwarden_put_collections_admin`(cipher_id; optional json_body, params, form)
7. `vaultwarden_post_ciphers_admin`(; optional json_body, params, form)
8. `vaultwarden_get_cipher_admin`(cipher_id; optional json_body, params, form)
9. `vaultwarden_put_cipher_admin`(cipher_id; optional json_body, params, form)
10. `vaultwarden_post_cipher_admin`(cipher_id; optional json_body, params, form)

### rotate-an-item-password

Replace an item's password with a generated one. Contract steps, in order:

1. `vaultwarden_maintenance_generate_password`(; optional length, use_symbols)
2. `vaultwarden_ciphers_get_item`(item_id)
3. `vaultwarden_maintenance_rotate_password`(item_id; optional length, use_symbols, confirm) (destructive: pass confirm=true only after the person agrees)

### snapshot-vault-metadata

Serve the metadata-only projection of the vault for the knowledge graph. Contract steps, in order:

1. `vaultwarden_metadata_snapshot`(; optional mode, checkpoint)
2. `vaultwarden_metadata_backfeed`(no arguments)

### audit-vault-contents

Read events and exports to see who touched which items. Contract steps, in order:

1. `vaultwarden_get_org_events`(org_id; optional data, json_body, params, form)
2. `vaultwarden_get_cipher_events`(cipher_id; optional data, json_body, params, form)
3. `vaultwarden_get_user_events`(org_id, member_id; optional data, json_body, params, form)
4. `vaultwarden_post_events_collect`(; optional json_body, params, form)
5. `vaultwarden_get_org_export`(org_id; optional json_body, params, form)

### share-with-a-send

Create, read and remove a time-limited Send. Contract steps, in order:

1. `vaultwarden_get_sends`(; optional json_body, params, form)
2. `vaultwarden_get_send`(send_id; optional json_body, params, form)
3. `vaultwarden_post_send`(; optional json_body, params, form)
4. `vaultwarden_post_send_file`(; optional json_body, params, form)
5. `vaultwarden_post_send_file_v2`(; optional json_body, params, form)
6. `vaultwarden_post_send_file_v2_data`(send_id, file_id; optional json_body, params, form)
7. `vaultwarden_put_send`(send_id; optional json_body, params, form)
8. `vaultwarden_delete_send`(send_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
9. `vaultwarden_put_remove_password`(send_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### access-a-send

Open or download a Send as a recipient. Contract steps, in order:

1. `vaultwarden_post_access`(; optional json_body, params, form)
2. `vaultwarden_post_access_legacy`(access_id; optional json_body, params, form)
3. `vaultwarden_post_access_file`(file_id; optional json_body, params, form)
4. `vaultwarden_post_access_file_legacy`(send_id, file_id; optional json_body, params, form)
5. `vaultwarden_download_send`(send_id, file_id; optional t, json_body, params, form)

### check-server-status

Read server liveness, time, version and public config. Contract steps, in order:

1. `vaultwarden_hibp_breach`(; optional username, json_body, params, form)
2. `vaultwarden_alive`(; optional json_body, params, form)
3. `vaultwarden_now`(; optional json_body, params, form)
4. `vaultwarden_version`(; optional json_body, params, form)
5. `vaultwarden_config`(; optional json_body, params, form)
