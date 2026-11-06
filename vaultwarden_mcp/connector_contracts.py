"""Tool-use contracts, surface links, data locations and business roles of vaultwarden-mcp.

The SDK serves this declaration as the connector's surface ontology and checks it
against the served tools, prompts and skills (SCION-CONNECTOR-CONTROL-R916).
"""

# ruff: noqa: E501
from __future__ import annotations

from scion_sdk.surface_contracts import (
    BusinessRole,
    DataLocation,
    Refusal,
    SurfaceLink,
    ToolStep,
    ToolUseContract,
)

CONTRACTS: tuple[ToolUseContract, ...] = (
    ToolUseContract(
        "read-vault-items",
        description="Read vault items and folders, decrypted or as stored",
        steps=(
            ToolStep(
                "vaultwarden_ciphers_list_items",
                params=("include_trash",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_ciphers_get_item",
                params=("item_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_folders_list_folders",
                params=(),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_sync",
                params=("data", "json_body", "params"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_ciphers",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_cipher",
                params=("cipher_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_cipher_details",
                params=("cipher_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_folders",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_folder",
                params=("folder_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
        ),
    ),
    ToolUseContract(
        "write-vault-items",
        description="Create and change vault items and folders",
        steps=(
            ToolStep(
                "vaultwarden_ciphers_create_item",
                params=("item",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_ciphers_edit_item",
                params=("item_id", "item"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_folders_create_folder",
                params=("name",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_ciphers_list_items",
                params=("include_trash",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_ciphers_create",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_ciphers",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_cipher",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_cipher",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_cipher_partial",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_cipher_partial",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_folders",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_folder",
                params=("folder_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_folder",
                params=("folder_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_ciphers_import",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_cipher_share",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_cipher_share",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_cipher_share_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_move_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_move_cipher_selected_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "trash-and-restore-vault-items",
        description="Move items to the trash, restore, archive and permanently delete them",
        steps=(
            ToolStep(
                "vaultwarden_ciphers_move_to_trash",
                params=("ids",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_post",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_post_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_put_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_post",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_post_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_put_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_put_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_selected_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_archive_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_archive_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_unarchive_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_unarchive_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_folder",
                params=("folder_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_folder_post",
                params=("folder_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_purge_personal_vault",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "manage-item-attachments",
        description="Upload, read and delete file attachments of an item",
        steps=(
            ToolStep(
                "vaultwarden_get_attachment",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_post_attachment",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_share",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_v2",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_v2_data",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_attachment",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_attachment_admin",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_attachment_post",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_attachment_post_admin",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "place-items-in-collections",
        description="Assign items to organization collections",
        steps=(
            ToolStep(
                "vaultwarden_post_collections2_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_collections_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_collections2_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_collections_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_collections_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_collections_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_ciphers_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_cipher_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_cipher_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_cipher_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "plan-vault-deduplication",
        description="Find duplicate items and report what a clean-up would trash",
        steps=(
            ToolStep(
                "vaultwarden_maintenance_plan_deduplication",
                params=("loose", "include_org"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "apply-vault-deduplication",
        description="Trash the duplicates of a strict plan",
        steps=(
            ToolStep(
                "vaultwarden_maintenance_plan_deduplication",
                params=("loose", "include_org"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_maintenance_apply_deduplication",
                params=("include_org", "confirm"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "rotate-an-item-password",
        description="Replace an item's password with a generated one",
        steps=(
            ToolStep(
                "vaultwarden_maintenance_generate_password",
                params=("length", "use_symbols"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_ciphers_get_item",
                params=("item_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_maintenance_rotate_password",
                params=("item_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "snapshot-vault-metadata",
        description="Serve the metadata-only projection of the vault for the knowledge graph",
        steps=(
            ToolStep(
                "vaultwarden_metadata_snapshot",
                params=("mode", "checkpoint"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_metadata_backfeed",
                params=(),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "audit-vault-contents",
        description="Read events and exports to see who touched which items",
        steps=(
            ToolStep(
                "vaultwarden_get_org_events",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_get_cipher_events",
                params=("cipher_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_user_events",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_events_collect",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_org_export",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
        ),
    ),
    ToolUseContract(
        "share-with-a-send",
        description="Create, read and remove a time-limited Send",
        steps=(
            ToolStep(
                "vaultwarden_get_sends",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_send",
                params=("send_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_send",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_send_file",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_send_file_v2",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_send_file_v2_data",
                params=("send_id", "file_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_send",
                params=("send_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_send",
                params=("send_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_put_remove_password",
                params=("send_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "access-a-send",
        description="Open or download a Send as a recipient",
        steps=(
            ToolStep(
                "vaultwarden_post_access",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_access_legacy",
                params=("access_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_access_file",
                params=("file_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_access_file_legacy",
                params=("send_id", "file_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_download_send",
                params=("send_id", "file_id"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "manage-my-profile",
        description="Read and change the profile, keys and security stamp of the signed-in account",
        steps=(
            ToolStep(
                "vaultwarden_post_set_password",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_profile",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_profile",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_profile",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_avatar",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_public_keys",
                params=("user_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_keys",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_sstamp",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_revision_date",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_password_hint",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_accounts_post_prelogin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_verify_password",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_tasks",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "change-account-credentials",
        description="Change the master password, KDF, email and rotate keys",
        steps=(
            ToolStep(
                "vaultwarden_post_password",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_kdf",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_rotatekey",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_email_token",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_email",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_verify_email",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_verify_email_token",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "manage-my-devices-and-api-key",
        description="List devices, device tokens, login-approval requests and the API key",
        steps=(
            ToolStep(
                "vaultwarden_accounts_post_api_key",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_accounts_rotate_api_key",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_known_device",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_all_devices",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_device",
                params=("device_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_device_token",
                params=("device_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_device_token",
                params=("device_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_clear_device_token",
                params=("device_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_clear_device_token",
                params=("device_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_auth_request",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_auth_request",
                params=("auth_request_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_auth_request",
                params=("auth_request_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_auth_request_response",
                params=("auth_request_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_auth_requests",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_auth_requests_pending",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "delete-my-account",
        description="Delete the signed-in account",
        steps=(
            ToolStep(
                "vaultwarden_post_delete_recover",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_delete_recover_token",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_delete_account",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_account",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "set-up-two-factor",
        description="Set up and activate an authenticator, Duo, email, WebAuthn or YubiKey factor",
        steps=(
            ToolStep(
                "vaultwarden_generate_authenticator",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_activate_authenticator",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_authenticator_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_duo",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_duo",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_duo_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_send_email_login",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_email",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_send_email",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_email",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_twofactor",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_recover",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_device_verification_settings",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_request_otp",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_verify_otp",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_webauthn",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_generate_webauthn_challenge",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_webauthn",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_webauthn_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_generate_yubikey",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_yubikey",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_activate_yubikey_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "remove-two-factor",
        description="Disable a two-factor method",
        steps=(
            ToolStep(
                "vaultwarden_disable_authenticator",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_disable_twofactor",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_disable_twofactor_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_webauthn",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "grant-emergency-access",
        description="Invite, confirm and revoke emergency contacts",
        steps=(
            ToolStep(
                "vaultwarden_get_contacts",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_grantees",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_post_delete_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_emergency_access_send_invite",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_resend_invite",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_emergency_access_accept_invite",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_confirm_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "use-emergency-access",
        description="Request, approve and take over a vault as an emergency contact",
        steps=(
            ToolStep(
                "vaultwarden_initiate_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_approve_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_reject_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_view_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_takeover_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_password_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_policies_emergency_access",
                params=("emer_id",),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "create-and-update-organization",
        description="Create, read, change and delete an organization",
        steps=(
            ToolStep(
                "vaultwarden_create_organization",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_organizations_delete_organization",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_delete_organization",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_organization",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_organization",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_organization",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_auto_enroll_status",
                params=("identifier",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_org_details",
                params=("data", "json_body", "params"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_org_domain_sso_verified",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_org_import",
                params=("query", "json_body", "params"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_plans",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_billing_metadata",
                params=("_org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_billing_warnings",
                params=("_org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_self_host_billing_metadata",
                params=("_org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_organizations_post_api_key",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_organizations_rotate_api_key",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "manage-organization-members",
        description="Invite, confirm, change, revoke, restore and remove members",
        steps=(
            ToolStep(
                "vaultwarden_leave_organization",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_members",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_org_keys",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_organizations_send_invite",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_bulk_reinvite_members",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_reinvite_member",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_organizations_accept_invite",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_bulk_confirm_invite",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_confirm_invite",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_org_user_mini_details",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_user",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_member",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_edit_member",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_bulk_delete_member",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_member",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_bulk_public_keys",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_revoke_member",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_bulk_revoke_members",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_member_vnext",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_member",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_bulk_restore_members",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_organization_public_key",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_organization_keys",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
        ),
    ),
    ToolUseContract(
        "manage-organization-groups",
        description="Create groups and set their members and access",
        steps=(
            ToolStep(
                "vaultwarden_get_groups",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_get_groups_details",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_group",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_groups",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_group",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_group_details",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_delete_group",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_group",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_bulk_delete_groups",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_group",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_group_members",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_group_members",
                params=("org_id", "group_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_delete_group_member",
                params=("org_id", "group_id", "member_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "manage-organization-collections",
        description="Create collections and set who can use them",
        steps=(
            ToolStep(
                "vaultwarden_get_user_collections",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_org_collections",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_org_collections_details",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_organization_collections",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_bulk_access_collections",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_organization_collection_update",
                params=("org_id", "col_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_organization_collection_update",
                params=("org_id", "col_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_organization_collection",
                params=("org_id", "col_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_post_organization_collection_delete",
                params=("org_id", "col_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_bulk_delete_organization_collections",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_org_collection_detail",
                params=("org_id", "col_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_collection_users",
                params=("org_id", "col_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_bulk_collections",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "set-organization-policies",
        description="Read and change organization policies",
        steps=(
            ToolStep(
                "vaultwarden_list_policies",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_list_policies_token",
                params=("org_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_dummy_master_password_policy",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_master_password_policy",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_policy",
                params=("org_id", "pol_type"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_policy",
                params=("org_id", "pol_type"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_policy_vnext",
                params=("org_id", "pol_type"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "recover-member-accounts",
        description="Enroll in and use password reset and account recovery",
        steps=(
            ToolStep(
                "vaultwarden_put_recover_account",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_put_reset_password",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_reset_password_details",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_put_reset_password_enrollment",
                params=("org_id", "user_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_org_export",
                params=("org_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
        ),
    ),
    ToolUseContract(
        "administer-users",
        description="Invite, disable, enable, sign out and delete server users",
        steps=(
            ToolStep(
                "vaultwarden_invite_user",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_users_json",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_user_by_mail_json",
                params=("mail",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_user_json",
                params=("user_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_delete_user",
                params=("user_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_sso_user",
                params=("user_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_deauth_user",
                params=("user_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_disable_user",
                params=("user_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_enable_user",
                params=("user_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_remove_2fa",
                params=("user_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_resend_user_invite",
                params=("user_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_update_membership_type",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_update_revision_users",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_admin_delete_organization",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "administer-server",
        description="Read diagnostics, test mail, change server config and back up the database",
        steps=(
            ToolStep(
                "vaultwarden_test_smtp",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_get_diagnostics_config",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_get_diagnostics_http",
                params=("code", "json_body", "params"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_config",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_config",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_backup_db",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "register-and-prelogin",
        description="Run the identity prelogin and registration flow",
        steps=(
            ToolStep(
                "vaultwarden_identity_post_prelogin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_prelogin_password",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_identity_register",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_register_verification_email",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_register_finish",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_prevalidate",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "check-server-status",
        description="Read server liveness, time, version and public config",
        steps=(
            ToolStep(
                "vaultwarden_hibp_breach",
                params=("username", "json_body", "params"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_alive",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_now",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_version",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_config",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "manage-equivalent-domains",
        description="Read and change equivalent-domain settings",
        steps=(
            ToolStep(
                "vaultwarden_get_settings_domains",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_post_settings_domains",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_settings_domains",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "misc-other-operations",
        description="Other server operations",
        steps=(
            ToolStep(
                "vaultwarden_get_api_webauthn",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "fetch-site-icons",
        description="Fetch the icon of a site",
        steps=(
            ToolStep(
                "vaultwarden_icon_external",
                params=("host",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_icon_internal",
                params=("host",),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "import-from-directory",
        description="Import users and groups from a directory",
        steps=(
            ToolStep(
                "vaultwarden_ldap_import",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "events-other-operations",
        description="Other event operations",
        steps=(
            ToolStep(
                "vaultwarden_get_org_events",
                params=("org_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_get_cipher_events",
                params=("cipher_id",),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_get_user_events",
                params=("org_id", "member_id"),
                result=("result",),
                refusals=(Refusal("not_found", "the named object does not exist"),),
            ),
            ToolStep(
                "vaultwarden_post_events_collect",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
    ToolUseContract(
        "other-operations",
        description="Operations not covered by a named workflow",
        steps=(
            ToolStep(
                "vaultwarden_archive_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "access_denied", "the credential lacks access to the system"
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_archive_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_delete_attachment",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_attachment_admin",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_attachment_post",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_attachment_post_admin",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_post",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_post_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_put_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_post",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_post_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_put",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_cipher_selected_put_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_folder",
                params=("folder_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_delete_folder_post",
                params=("folder_id",),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                    Refusal("not_found", "the named object does not exist"),
                ),
            ),
            ToolStep(
                "vaultwarden_post_attachment",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_share",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_v2",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_attachment_v2_data",
                params=("cipher_id", "attachment_id"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_collections2_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_post_collections_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_purge_org_vault",
                params=("organization", "json_body", "params"),
                result=("result",),
                refusals=(
                    Refusal(
                        "confirmation_required",
                        "the destructive call omits confirm=true",
                    ),
                ),
            ),
            ToolStep(
                "vaultwarden_put_collections2_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_put_collections_update",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_put_admin",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_restore_cipher_selected_admin",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_unarchive_cipher_put",
                params=("cipher_id",),
                result=("result",),
                refusals=(),
            ),
            ToolStep(
                "vaultwarden_unarchive_cipher_selected",
                params=("json_body", "params", "form"),
                result=("result",),
                refusals=(),
            ),
        ),
    ),
)

LINKS: tuple[SurfaceLink, ...] = (
    SurfaceLink(
        "read-vault-items",
        tools=(
            "vaultwarden_ciphers_list_items",
            "vaultwarden_ciphers_get_item",
            "vaultwarden_folders_list_folders",
            "vaultwarden_sync",
            "vaultwarden_get_ciphers",
            "vaultwarden_get_cipher",
            "vaultwarden_get_cipher_details",
            "vaultwarden_get_folders",
            "vaultwarden_get_folder",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations", "vaultwarden-vault-deduplication"),
    ),
    SurfaceLink(
        "write-vault-items",
        tools=(
            "vaultwarden_ciphers_create_item",
            "vaultwarden_ciphers_edit_item",
            "vaultwarden_folders_create_folder",
            "vaultwarden_ciphers_list_items",
            "vaultwarden_post_ciphers_create",
            "vaultwarden_post_ciphers",
            "vaultwarden_post_cipher",
            "vaultwarden_put_cipher",
            "vaultwarden_post_cipher_partial",
            "vaultwarden_put_cipher_partial",
            "vaultwarden_post_folders",
            "vaultwarden_post_folder",
            "vaultwarden_put_folder",
            "vaultwarden_post_ciphers_import",
            "vaultwarden_post_cipher_share",
            "vaultwarden_put_cipher_share",
            "vaultwarden_put_cipher_share_selected",
            "vaultwarden_move_cipher_selected",
            "vaultwarden_move_cipher_selected_put",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "trash-and-restore-vault-items",
        tools=(
            "vaultwarden_ciphers_move_to_trash",
            "vaultwarden_delete_cipher",
            "vaultwarden_delete_cipher_admin",
            "vaultwarden_delete_cipher_post",
            "vaultwarden_delete_cipher_post_admin",
            "vaultwarden_delete_cipher_put",
            "vaultwarden_delete_cipher_put_admin",
            "vaultwarden_delete_cipher_selected",
            "vaultwarden_delete_cipher_selected_admin",
            "vaultwarden_delete_cipher_selected_post",
            "vaultwarden_delete_cipher_selected_post_admin",
            "vaultwarden_delete_cipher_selected_put",
            "vaultwarden_delete_cipher_selected_put_admin",
            "vaultwarden_restore_cipher_put",
            "vaultwarden_restore_cipher_put_admin",
            "vaultwarden_restore_cipher_selected",
            "vaultwarden_restore_cipher_selected_admin",
            "vaultwarden_archive_cipher_put",
            "vaultwarden_archive_cipher_selected",
            "vaultwarden_unarchive_cipher_put",
            "vaultwarden_unarchive_cipher_selected",
            "vaultwarden_delete_folder",
            "vaultwarden_delete_folder_post",
            "vaultwarden_purge_personal_vault",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "manage-item-attachments",
        tools=(
            "vaultwarden_get_attachment",
            "vaultwarden_post_attachment",
            "vaultwarden_post_attachment_admin",
            "vaultwarden_post_attachment_share",
            "vaultwarden_post_attachment_v2",
            "vaultwarden_post_attachment_v2_data",
            "vaultwarden_delete_attachment",
            "vaultwarden_delete_attachment_admin",
            "vaultwarden_delete_attachment_post",
            "vaultwarden_delete_attachment_post_admin",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "place-items-in-collections",
        tools=(
            "vaultwarden_post_collections2_update",
            "vaultwarden_post_collections_update",
            "vaultwarden_put_collections2_update",
            "vaultwarden_put_collections_update",
            "vaultwarden_post_collections_admin",
            "vaultwarden_put_collections_admin",
            "vaultwarden_post_ciphers_admin",
            "vaultwarden_get_cipher_admin",
            "vaultwarden_put_cipher_admin",
            "vaultwarden_post_cipher_admin",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-vault-curator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "plan-vault-deduplication",
        tools=("vaultwarden_maintenance_plan_deduplication",),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-vault-deduplication",),
    ),
    SurfaceLink(
        "apply-vault-deduplication",
        tools=(
            "vaultwarden_maintenance_plan_deduplication",
            "vaultwarden_maintenance_apply_deduplication",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-vault-deduplication",),
    ),
    SurfaceLink(
        "rotate-an-item-password",
        tools=(
            "vaultwarden_maintenance_generate_password",
            "vaultwarden_ciphers_get_item",
            "vaultwarden_maintenance_rotate_password",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "snapshot-vault-metadata",
        tools=("vaultwarden_metadata_snapshot", "vaultwarden_metadata_backfeed"),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "audit-vault-contents",
        tools=(
            "vaultwarden_get_org_events",
            "vaultwarden_get_cipher_events",
            "vaultwarden_get_user_events",
            "vaultwarden_post_events_collect",
            "vaultwarden_get_org_export",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
            "vaultwarden-mcp-server-administrator",
        ),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "share-with-a-send",
        tools=(
            "vaultwarden_get_sends",
            "vaultwarden_get_send",
            "vaultwarden_post_send",
            "vaultwarden_post_send_file",
            "vaultwarden_post_send_file_v2",
            "vaultwarden_post_send_file_v2_data",
            "vaultwarden_put_send",
            "vaultwarden_delete_send",
            "vaultwarden_put_remove_password",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "access-a-send",
        tools=(
            "vaultwarden_post_access",
            "vaultwarden_post_access_legacy",
            "vaultwarden_post_access_file",
            "vaultwarden_post_access_file_legacy",
            "vaultwarden_download_send",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-vault-curator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "manage-my-profile",
        tools=(
            "vaultwarden_post_set_password",
            "vaultwarden_profile",
            "vaultwarden_put_profile",
            "vaultwarden_post_profile",
            "vaultwarden_put_avatar",
            "vaultwarden_get_public_keys",
            "vaultwarden_post_keys",
            "vaultwarden_post_sstamp",
            "vaultwarden_revision_date",
            "vaultwarden_password_hint",
            "vaultwarden_accounts_post_prelogin",
            "vaultwarden_verify_password",
            "vaultwarden_get_tasks",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "change-account-credentials",
        tools=(
            "vaultwarden_post_password",
            "vaultwarden_post_kdf",
            "vaultwarden_post_rotatekey",
            "vaultwarden_post_email_token",
            "vaultwarden_post_email",
            "vaultwarden_post_verify_email",
            "vaultwarden_post_verify_email_token",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "manage-my-devices-and-api-key",
        tools=(
            "vaultwarden_accounts_post_api_key",
            "vaultwarden_accounts_rotate_api_key",
            "vaultwarden_get_known_device",
            "vaultwarden_get_all_devices",
            "vaultwarden_get_device",
            "vaultwarden_post_device_token",
            "vaultwarden_put_device_token",
            "vaultwarden_put_clear_device_token",
            "vaultwarden_post_clear_device_token",
            "vaultwarden_post_auth_request",
            "vaultwarden_get_auth_request",
            "vaultwarden_put_auth_request",
            "vaultwarden_get_auth_request_response",
            "vaultwarden_get_auth_requests",
            "vaultwarden_get_auth_requests_pending",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "delete-my-account",
        tools=(
            "vaultwarden_post_delete_recover",
            "vaultwarden_post_delete_recover_token",
            "vaultwarden_post_delete_account",
            "vaultwarden_delete_account",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "set-up-two-factor",
        tools=(
            "vaultwarden_generate_authenticator",
            "vaultwarden_activate_authenticator",
            "vaultwarden_activate_authenticator_put",
            "vaultwarden_get_duo",
            "vaultwarden_activate_duo",
            "vaultwarden_activate_duo_put",
            "vaultwarden_send_email_login",
            "vaultwarden_get_email",
            "vaultwarden_send_email",
            "vaultwarden_email",
            "vaultwarden_get_twofactor",
            "vaultwarden_get_recover",
            "vaultwarden_get_device_verification_settings",
            "vaultwarden_request_otp",
            "vaultwarden_verify_otp",
            "vaultwarden_get_webauthn",
            "vaultwarden_generate_webauthn_challenge",
            "vaultwarden_activate_webauthn",
            "vaultwarden_activate_webauthn_put",
            "vaultwarden_generate_yubikey",
            "vaultwarden_activate_yubikey",
            "vaultwarden_activate_yubikey_put",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "remove-two-factor",
        tools=(
            "vaultwarden_disable_authenticator",
            "vaultwarden_disable_twofactor",
            "vaultwarden_disable_twofactor_put",
            "vaultwarden_delete_webauthn",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "grant-emergency-access",
        tools=(
            "vaultwarden_get_contacts",
            "vaultwarden_get_grantees",
            "vaultwarden_get_emergency_access",
            "vaultwarden_put_emergency_access",
            "vaultwarden_post_emergency_access",
            "vaultwarden_delete_emergency_access",
            "vaultwarden_post_delete_emergency_access",
            "vaultwarden_emergency_access_send_invite",
            "vaultwarden_resend_invite",
            "vaultwarden_emergency_access_accept_invite",
            "vaultwarden_confirm_emergency_access",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "use-emergency-access",
        tools=(
            "vaultwarden_initiate_emergency_access",
            "vaultwarden_approve_emergency_access",
            "vaultwarden_reject_emergency_access",
            "vaultwarden_view_emergency_access",
            "vaultwarden_takeover_emergency_access",
            "vaultwarden_password_emergency_access",
            "vaultwarden_policies_emergency_access",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "create-and-update-organization",
        tools=(
            "vaultwarden_create_organization",
            "vaultwarden_organizations_delete_organization",
            "vaultwarden_post_delete_organization",
            "vaultwarden_get_organization",
            "vaultwarden_put_organization",
            "vaultwarden_post_organization",
            "vaultwarden_get_auto_enroll_status",
            "vaultwarden_get_org_details",
            "vaultwarden_get_org_domain_sso_verified",
            "vaultwarden_post_org_import",
            "vaultwarden_get_plans",
            "vaultwarden_get_billing_metadata",
            "vaultwarden_get_billing_warnings",
            "vaultwarden_get_self_host_billing_metadata",
            "vaultwarden_organizations_post_api_key",
            "vaultwarden_organizations_rotate_api_key",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-organization-administration",),
    ),
    SurfaceLink(
        "manage-organization-members",
        tools=(
            "vaultwarden_leave_organization",
            "vaultwarden_get_members",
            "vaultwarden_post_org_keys",
            "vaultwarden_organizations_send_invite",
            "vaultwarden_bulk_reinvite_members",
            "vaultwarden_reinvite_member",
            "vaultwarden_organizations_accept_invite",
            "vaultwarden_bulk_confirm_invite",
            "vaultwarden_confirm_invite",
            "vaultwarden_get_org_user_mini_details",
            "vaultwarden_get_user",
            "vaultwarden_put_member",
            "vaultwarden_edit_member",
            "vaultwarden_bulk_delete_member",
            "vaultwarden_delete_member",
            "vaultwarden_bulk_public_keys",
            "vaultwarden_revoke_member",
            "vaultwarden_bulk_revoke_members",
            "vaultwarden_restore_member_vnext",
            "vaultwarden_restore_member",
            "vaultwarden_bulk_restore_members",
            "vaultwarden_get_organization_public_key",
            "vaultwarden_get_organization_keys",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-organization-administration",),
    ),
    SurfaceLink(
        "manage-organization-groups",
        tools=(
            "vaultwarden_get_groups",
            "vaultwarden_get_groups_details",
            "vaultwarden_post_group",
            "vaultwarden_post_groups",
            "vaultwarden_put_group",
            "vaultwarden_get_group_details",
            "vaultwarden_post_delete_group",
            "vaultwarden_delete_group",
            "vaultwarden_bulk_delete_groups",
            "vaultwarden_get_group",
            "vaultwarden_get_group_members",
            "vaultwarden_put_group_members",
            "vaultwarden_post_delete_group_member",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-organization-administration",),
    ),
    SurfaceLink(
        "manage-organization-collections",
        tools=(
            "vaultwarden_get_user_collections",
            "vaultwarden_get_org_collections",
            "vaultwarden_get_org_collections_details",
            "vaultwarden_post_organization_collections",
            "vaultwarden_post_bulk_access_collections",
            "vaultwarden_put_organization_collection_update",
            "vaultwarden_post_organization_collection_update",
            "vaultwarden_delete_organization_collection",
            "vaultwarden_post_organization_collection_delete",
            "vaultwarden_bulk_delete_organization_collections",
            "vaultwarden_get_org_collection_detail",
            "vaultwarden_get_collection_users",
            "vaultwarden_post_bulk_collections",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-organization-administration",),
    ),
    SurfaceLink(
        "set-organization-policies",
        tools=(
            "vaultwarden_list_policies",
            "vaultwarden_list_policies_token",
            "vaultwarden_get_dummy_master_password_policy",
            "vaultwarden_get_master_password_policy",
            "vaultwarden_get_policy",
            "vaultwarden_put_policy",
            "vaultwarden_put_policy_vnext",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-organization-administration",),
    ),
    SurfaceLink(
        "recover-member-accounts",
        tools=(
            "vaultwarden_put_recover_account",
            "vaultwarden_put_reset_password",
            "vaultwarden_get_reset_password_details",
            "vaultwarden_put_reset_password_enrollment",
            "vaultwarden_get_org_export",
        ),
        prompts=(
            "vaultwarden-mcp-operator",
            "vaultwarden-mcp-organization-administrator",
        ),
        skills=("vaultwarden-organization-administration",),
    ),
    SurfaceLink(
        "administer-users",
        tools=(
            "vaultwarden_invite_user",
            "vaultwarden_get_users_json",
            "vaultwarden_get_user_by_mail_json",
            "vaultwarden_get_user_json",
            "vaultwarden_delete_user",
            "vaultwarden_delete_sso_user",
            "vaultwarden_deauth_user",
            "vaultwarden_disable_user",
            "vaultwarden_enable_user",
            "vaultwarden_remove_2fa",
            "vaultwarden_resend_user_invite",
            "vaultwarden_update_membership_type",
            "vaultwarden_update_revision_users",
            "vaultwarden_admin_delete_organization",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-server-administrator"),
        skills=("vaultwarden-server-administration",),
    ),
    SurfaceLink(
        "administer-server",
        tools=(
            "vaultwarden_test_smtp",
            "vaultwarden_get_diagnostics_config",
            "vaultwarden_get_diagnostics_http",
            "vaultwarden_post_config",
            "vaultwarden_delete_config",
            "vaultwarden_backup_db",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-server-administrator"),
        skills=("vaultwarden-server-administration",),
    ),
    SurfaceLink(
        "register-and-prelogin",
        tools=(
            "vaultwarden_identity_post_prelogin",
            "vaultwarden_prelogin_password",
            "vaultwarden_identity_register",
            "vaultwarden_register_verification_email",
            "vaultwarden_register_finish",
            "vaultwarden_prevalidate",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-account-owner"),
        skills=("vaultwarden-account-security",),
    ),
    SurfaceLink(
        "check-server-status",
        tools=(
            "vaultwarden_hibp_breach",
            "vaultwarden_alive",
            "vaultwarden_now",
            "vaultwarden_version",
            "vaultwarden_config",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-server-administrator"),
        skills=("vaultwarden-mcp-operations",),
    ),
    SurfaceLink(
        "manage-equivalent-domains",
        tools=(
            "vaultwarden_get_settings_domains",
            "vaultwarden_post_settings_domains",
            "vaultwarden_put_settings_domains",
        ),
        prompts=("vaultwarden-mcp-operator", "vaultwarden-mcp-server-administrator"),
        skills=("vaultwarden-server-administration",),
    ),
    SurfaceLink(
        "misc-other-operations",
        tools=("vaultwarden_get_api_webauthn",),
        prompts=("vaultwarden-mcp-operator",),
        skills=(),
    ),
    SurfaceLink(
        "fetch-site-icons",
        tools=("vaultwarden_icon_external", "vaultwarden_icon_internal"),
        prompts=("vaultwarden-mcp-operator",),
        skills=(),
    ),
    SurfaceLink(
        "import-from-directory",
        tools=("vaultwarden_ldap_import",),
        prompts=("vaultwarden-mcp-operator",),
        skills=(),
    ),
    SurfaceLink(
        "events-other-operations",
        tools=(
            "vaultwarden_get_org_events",
            "vaultwarden_get_cipher_events",
            "vaultwarden_get_user_events",
            "vaultwarden_post_events_collect",
        ),
        prompts=("vaultwarden-mcp-operator",),
        skills=(),
    ),
    SurfaceLink(
        "other-operations",
        tools=(
            "vaultwarden_archive_cipher_put",
            "vaultwarden_archive_cipher_selected",
            "vaultwarden_delete_attachment",
            "vaultwarden_delete_attachment_admin",
            "vaultwarden_delete_attachment_post",
            "vaultwarden_delete_attachment_post_admin",
            "vaultwarden_delete_cipher",
            "vaultwarden_delete_cipher_admin",
            "vaultwarden_delete_cipher_post",
            "vaultwarden_delete_cipher_post_admin",
            "vaultwarden_delete_cipher_put",
            "vaultwarden_delete_cipher_put_admin",
            "vaultwarden_delete_cipher_selected",
            "vaultwarden_delete_cipher_selected_admin",
            "vaultwarden_delete_cipher_selected_post",
            "vaultwarden_delete_cipher_selected_post_admin",
            "vaultwarden_delete_cipher_selected_put",
            "vaultwarden_delete_cipher_selected_put_admin",
            "vaultwarden_delete_folder",
            "vaultwarden_delete_folder_post",
            "vaultwarden_post_attachment",
            "vaultwarden_post_attachment_admin",
            "vaultwarden_post_attachment_share",
            "vaultwarden_post_attachment_v2",
            "vaultwarden_post_attachment_v2_data",
            "vaultwarden_post_collections2_update",
            "vaultwarden_post_collections_update",
            "vaultwarden_purge_org_vault",
            "vaultwarden_put_collections2_update",
            "vaultwarden_put_collections_update",
            "vaultwarden_restore_cipher_put",
            "vaultwarden_restore_cipher_put_admin",
            "vaultwarden_restore_cipher_selected",
            "vaultwarden_restore_cipher_selected_admin",
            "vaultwarden_unarchive_cipher_put",
            "vaultwarden_unarchive_cipher_selected",
        ),
        prompts=("vaultwarden-mcp-operator",),
        skills=(),
    ),
)

LOCATIONS: tuple[DataLocation, ...] = (
    DataLocation(
        "vault-items",
        ("Credential",),
        "VAULTWARDEN_URL",
        "vaultwarden_ciphers_list_items",
        federation_key="item_id",
    ),
    DataLocation(
        "vault-folders",
        ("Collection",),
        "VAULTWARDEN_URL",
        "vaultwarden_folders_list_folders",
        federation_key="folder_id",
    ),
    DataLocation(
        "organizations",
        ("Organization", "IdentityGroup", "IdentityUser"),
        "VAULTWARDEN_URL",
        "vaultwarden_get_organization",
        federation_key="org_id",
    ),
    DataLocation(
        "server-admin",
        ("Server",),
        "VAULTWARDEN_URL",
        "vaultwarden_get_diagnostics_config",
        federation_key=None,
    ),
)

ROLES: tuple[BusinessRole, ...] = (
    BusinessRole(
        "vault-curator",
        tasks=(
            "read-vault-items",
            "write-vault-items",
            "trash-and-restore-vault-items",
            "manage-item-attachments",
            "place-items-in-collections",
            "plan-vault-deduplication",
            "apply-vault-deduplication",
            "rotate-an-item-password",
            "snapshot-vault-metadata",
            "share-with-a-send",
            "access-a-send",
        ),
    ),
    BusinessRole(
        "organization-administrator",
        tasks=(
            "create-and-update-organization",
            "manage-organization-members",
            "manage-organization-groups",
            "manage-organization-collections",
            "set-organization-policies",
            "recover-member-accounts",
            "place-items-in-collections",
            "audit-vault-contents",
        ),
    ),
    BusinessRole(
        "server-administrator",
        tasks=(
            "check-server-status",
            "administer-users",
            "administer-server",
            "manage-equivalent-domains",
            "audit-vault-contents",
        ),
    ),
    BusinessRole(
        "account-owner",
        tasks=(
            "manage-my-profile",
            "change-account-credentials",
            "manage-my-devices-and-api-key",
            "set-up-two-factor",
            "remove-two-factor",
            "grant-emergency-access",
            "use-emergency-access",
            "delete-my-account",
            "register-and-prelogin",
        ),
    ),
)
