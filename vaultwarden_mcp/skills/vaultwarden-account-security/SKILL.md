---
name: vaultwarden-account-security
skill_type: skill
description: >-
  Maintain the signed-in Vaultwarden account through vaultwarden-mcp: profile, master password and KDF, devices and API key, two-factor methods and emergency access. Use for account hardening. Never for another person's account.
license: MIT
tags: [vaultwarden, account, two-factor]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# Vaultwarden account security

These tools act on the signed-in account only.

## Rules

- Add a new two-factor method before removing an old one.
- Never print master passwords, recovery codes, API keys or device tokens.
- Deleting the account needs the person's explicit request and confirm=true.

## Task workflows

### manage-my-profile

Read and change the profile, keys and security stamp of the signed-in account. Contract steps, in order:

1. `vaultwarden_post_set_password`(; optional json_body, params, form)
2. `vaultwarden_profile`(; optional json_body, params, form)
3. `vaultwarden_put_profile`(; optional json_body, params, form)
4. `vaultwarden_post_profile`(; optional json_body, params, form)
5. `vaultwarden_put_avatar`(; optional json_body, params, form)
6. `vaultwarden_get_public_keys`(user_id; optional json_body, params, form)
7. `vaultwarden_post_keys`(; optional json_body, params, form)
8. `vaultwarden_post_sstamp`(; optional json_body, params, form)
9. `vaultwarden_revision_date`(; optional json_body, params, form)
10. `vaultwarden_password_hint`(; optional json_body, params, form)
11. `vaultwarden_accounts_post_prelogin`(; optional json_body, params, form)
12. `vaultwarden_verify_password`(; optional json_body, params, form)
13. `vaultwarden_get_tasks`(; optional json_body, params, form)

### change-account-credentials

Change the master password, KDF, email and rotate keys. Contract steps, in order:

1. `vaultwarden_post_password`(; optional json_body, params, form)
2. `vaultwarden_post_kdf`(; optional json_body, params, form)
3. `vaultwarden_post_rotatekey`(; optional json_body, params, form)
4. `vaultwarden_post_email_token`(; optional json_body, params, form)
5. `vaultwarden_post_email`(; optional json_body, params, form)
6. `vaultwarden_post_verify_email`(; optional json_body, params, form)
7. `vaultwarden_post_verify_email_token`(; optional json_body, params, form)

### manage-my-devices-and-api-key

List devices, device tokens, login-approval requests and the API key. Contract steps, in order:

1. `vaultwarden_accounts_post_api_key`(; optional json_body, params, form)
2. `vaultwarden_accounts_rotate_api_key`(; optional json_body, params, form)
3. `vaultwarden_get_known_device`(; optional json_body, params, form)
4. `vaultwarden_get_all_devices`(; optional json_body, params, form)
5. `vaultwarden_get_device`(device_id; optional json_body, params, form)
6. `vaultwarden_post_device_token`(device_id; optional json_body, params, form)
7. `vaultwarden_put_device_token`(device_id; optional json_body, params, form)
8. `vaultwarden_put_clear_device_token`(device_id; optional json_body, params, form)
9. `vaultwarden_post_clear_device_token`(device_id; optional json_body, params, form)
10. `vaultwarden_post_auth_request`(; optional json_body, params, form)
11. `vaultwarden_get_auth_request`(auth_request_id; optional json_body, params, form)
12. `vaultwarden_put_auth_request`(auth_request_id; optional json_body, params, form)
13. `vaultwarden_get_auth_request_response`(auth_request_id; optional code, json_body, params, form)
14. `vaultwarden_get_auth_requests`(; optional json_body, params, form)
15. `vaultwarden_get_auth_requests_pending`(; optional json_body, params, form)

### set-up-two-factor

Set up and activate an authenticator, Duo, email, WebAuthn or YubiKey factor. Contract steps, in order:

1. `vaultwarden_generate_authenticator`(; optional json_body, params, form)
2. `vaultwarden_activate_authenticator`(; optional json_body, params, form)
3. `vaultwarden_activate_authenticator_put`(; optional json_body, params, form)
4. `vaultwarden_get_duo`(; optional json_body, params, form)
5. `vaultwarden_activate_duo`(; optional json_body, params, form)
6. `vaultwarden_activate_duo_put`(; optional json_body, params, form)
7. `vaultwarden_send_email_login`(; optional json_body, params, form)
8. `vaultwarden_get_email`(; optional json_body, params, form)
9. `vaultwarden_send_email`(; optional json_body, params, form)
10. `vaultwarden_email`(; optional json_body, params, form)
11. `vaultwarden_get_twofactor`(; optional json_body, params, form)
12. `vaultwarden_get_recover`(; optional json_body, params, form)
13. `vaultwarden_get_device_verification_settings`(; optional json_body, params, form)
14. `vaultwarden_request_otp`(; optional json_body, params, form)
15. `vaultwarden_verify_otp`(; optional json_body, params, form)
16. `vaultwarden_get_webauthn`(; optional json_body, params, form)
17. `vaultwarden_generate_webauthn_challenge`(; optional json_body, params, form)
18. `vaultwarden_activate_webauthn`(; optional json_body, params, form)
19. `vaultwarden_activate_webauthn_put`(; optional json_body, params, form)
20. `vaultwarden_generate_yubikey`(; optional json_body, params, form)
21. `vaultwarden_activate_yubikey`(; optional json_body, params, form)
22. `vaultwarden_activate_yubikey_put`(; optional json_body, params, form)

### remove-two-factor

Disable a two-factor method. Contract steps, in order:

1. `vaultwarden_disable_authenticator`(; optional json_body, params, form)
2. `vaultwarden_disable_twofactor`(; optional json_body, params, form)
3. `vaultwarden_disable_twofactor_put`(; optional json_body, params, form)
4. `vaultwarden_delete_webauthn`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### grant-emergency-access

Invite, confirm and revoke emergency contacts. Contract steps, in order:

1. `vaultwarden_get_contacts`(; optional json_body, params, form)
2. `vaultwarden_get_grantees`(; optional json_body, params, form)
3. `vaultwarden_get_emergency_access`(emer_id; optional json_body, params, form)
4. `vaultwarden_put_emergency_access`(emer_id; optional json_body, params, form)
5. `vaultwarden_post_emergency_access`(emer_id; optional json_body, params, form)
6. `vaultwarden_delete_emergency_access`(emer_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
7. `vaultwarden_post_delete_emergency_access`(emer_id; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
8. `vaultwarden_emergency_access_send_invite`(; optional json_body, params, form)
9. `vaultwarden_resend_invite`(emer_id; optional json_body, params, form)
10. `vaultwarden_emergency_access_accept_invite`(emer_id; optional json_body, params, form)
11. `vaultwarden_confirm_emergency_access`(emer_id; optional json_body, params, form)

### use-emergency-access

Request, approve and take over a vault as an emergency contact. Contract steps, in order:

1. `vaultwarden_initiate_emergency_access`(emer_id; optional json_body, params, form)
2. `vaultwarden_approve_emergency_access`(emer_id; optional json_body, params, form)
3. `vaultwarden_reject_emergency_access`(emer_id; optional json_body, params, form)
4. `vaultwarden_view_emergency_access`(emer_id; optional json_body, params, form)
5. `vaultwarden_takeover_emergency_access`(emer_id; optional json_body, params, form)
6. `vaultwarden_password_emergency_access`(emer_id; optional json_body, params, form)
7. `vaultwarden_policies_emergency_access`(emer_id; optional json_body, params, form)

### delete-my-account

Delete the signed-in account. Contract steps, in order:

1. `vaultwarden_post_delete_recover`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
2. `vaultwarden_post_delete_recover_token`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
3. `vaultwarden_post_delete_account`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)
4. `vaultwarden_delete_account`(; optional json_body, params, form, confirm) (destructive: pass confirm=true only after the person agrees)

### register-and-prelogin

Run the identity prelogin and registration flow. Contract steps, in order:

1. `vaultwarden_identity_post_prelogin`(; optional json_body, params, form)
2. `vaultwarden_prelogin_password`(; optional json_body, params, form)
3. `vaultwarden_identity_register`(; optional json_body, params, form)
4. `vaultwarden_register_verification_email`(; optional json_body, params, form)
5. `vaultwarden_register_finish`(; optional json_body, params, form)
6. `vaultwarden_prevalidate`(; optional json_body, params, form)
