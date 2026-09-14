"""Native Python ``VaultCrypto`` backend.

Unlocks an account with its master password and the key material the server already
returns (``Key``, ``PrivateKey``, KDF settings, organization keys), then decrypts and
encrypts vault records in the Bitwarden CLI JSON shape. Only strict type-2 EncStrings are
decrypted; anything else is passed through unchanged. Failures name the item id, never
its contents.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Literal, Protocol

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from .base import VaultRecord
from .encstring import (
    CryptoError,
    SymmetricKey,
    decrypt_bytes,
    decrypt_rsa,
    encrypt_string,
    load_private_key,
)
from .keys import KdfParams, decrypt_user_key, derive_master_key

# ``2.<16-byte IV>|<ciphertext>|<32-byte MAC>`` — strict, so plain values like "2.5" pass.
_TYPE2_ENCSTRING = re.compile(
    r"^2\.[A-Za-z0-9+/]{22}==\|[A-Za-z0-9+/]+={0,2}\|[A-Za-z0-9+/]{43}=$"
)

_WRITABLE_FIELDS = (
    "type",
    "name",
    "notes",
    "favorite",
    "reprompt",
    "folderId",
    "organizationId",
    "fields",
    "login",
    "secureNote",
    "card",
    "identity",
    "sshKey",
    "passwordHistory",
)
_ENCRYPTED_SUBFIELDS = {
    "login": ("username", "password", "totp", "uri"),
    "card": ("cardholderName", "brand", "number", "expMonth", "expYear", "code"),
    "identity": (
        "title",
        "firstName",
        "middleName",
        "lastName",
        "address1",
        "address2",
        "address3",
        "city",
        "state",
        "postalCode",
        "country",
        "company",
        "email",
        "phone",
        "ssn",
        "username",
        "passportNumber",
        "licenseNumber",
    ),
    "sshKey": ("privateKey", "publicKey", "keyFingerprint"),
}


class VaultApi(Protocol):
    def token_response(self) -> dict[str, Any]: ...

    def sync_vault(self, *, exclude_domains: bool = True) -> dict[str, Any]: ...

    def request(
        self,
        method: str,
        path: str,
        *,
        auth: Literal["user", "admin", "none"] = "user",
        json_body: Any = None,
        form: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any: ...


def _is_encrypted(value: Any) -> bool:
    return isinstance(value, str) and bool(_TYPE2_ENCSTRING.match(value))


def _encrypt_optional(value: Any, key: SymmetricKey) -> Any:
    if isinstance(value, str) and value and not _is_encrypted(value):
        return encrypt_string(value, key)
    return value


class NativeVaultCrypto:
    """Item-level vault access with keys derived in-process."""

    name = "native"

    def __init__(self, api: VaultApi, *, master_password: str | None) -> None:
        if not master_password:
            raise CryptoError(
                "the native backend needs the master_password credential reference"
            )
        self._api = api
        self._password: str | None = master_password
        self._email: str | None = None
        self._user_key: SymmetricKey | None = None
        self._org_keys: dict[str, SymmetricKey] = {}

    # -- key hierarchy -------------------------------------------------------------------

    def _unlock(self) -> SymmetricKey:
        if self._user_key is not None:
            return self._user_key
        if self._password is None:
            raise CryptoError("vault is locked and its master password was discarded")
        token = self._api.token_response()
        profile = self._api.sync_vault().get("profile") or {}
        email = profile.get("email")
        protected_key = profile.get("key") or token.get("Key")
        if not isinstance(email, str) or not isinstance(protected_key, str):
            raise CryptoError("account profile is missing its email or user key")
        master_key = derive_master_key(
            self._password, email, KdfParams.from_response(token)
        )
        try:
            user_key = decrypt_user_key(protected_key, master_key)
        except CryptoError as exc:
            raise CryptoError("master password did not unlock the account") from exc
        private_key = self._private_key(profile, user_key)
        org_keys: dict[str, SymmetricKey] = {}
        for org in profile.get("organizations") or []:
            if org.get("id") and org.get("key") and private_key is not None:
                org_keys[org["id"]] = SymmetricKey.from_bytes(
                    decrypt_rsa(org["key"], private_key)
                )
        self._email, self._user_key, self._org_keys = email, user_key, org_keys
        return user_key

    @staticmethod
    def _private_key(
        profile: dict[str, Any], user_key: SymmetricKey
    ) -> RSAPrivateKey | None:
        protected = profile.get("privateKey")
        if not protected:
            return None
        return load_private_key(decrypt_bytes(protected, user_key))

    def _owner_key(self, organization_id: str | None) -> SymmetricKey:
        user_key = self._unlock()
        if not organization_id:
            return user_key
        try:
            return self._org_keys[organization_id]
        except KeyError as exc:
            raise CryptoError(
                f"no key for organization {organization_id}; is membership confirmed?"
            ) from exc

    def _item_key(self, cipher: dict[str, Any]) -> SymmetricKey:
        owner = self._owner_key(cipher.get("organizationId"))
        if cipher.get("key"):
            return SymmetricKey.from_bytes(decrypt_bytes(cipher["key"], owner))
        return owner

    # -- decryption ------------------------------------------------------------------------

    def _decrypt_value(self, value: Any, key: SymmetricKey) -> Any:
        if _is_encrypted(value):
            return decrypt_bytes(value, key).decode("utf-8")
        if isinstance(value, dict):
            return {
                k: self._decrypt_value(v, key) for k, v in value.items() if k != "key"
            }
        if isinstance(value, list):
            return [self._decrypt_value(v, key) for v in value]
        return value

    def decrypt_item(self, cipher: dict[str, Any]) -> VaultRecord:
        try:
            record = self._decrypt_value(cipher, self._item_key(cipher))
        except (CryptoError, UnicodeDecodeError) as exc:
            raise CryptoError(f"could not decrypt item {cipher.get('id')}") from exc
        record["object"] = "item"
        return record

    # -- VaultCrypto -------------------------------------------------------------------------

    def account_email(self) -> str:
        self._unlock()
        return self._email or ""

    def list_items(self, *, include_trash: bool = False) -> list[VaultRecord]:
        self._unlock()
        ciphers = self._api.sync_vault().get("ciphers") or []
        return [
            self.decrypt_item(c)
            for c in ciphers
            if include_trash or not c.get("deletedDate")
        ]

    def get_item(self, item_id: str) -> VaultRecord:
        return self.decrypt_item(self._api.request("GET", f"api/ciphers/{item_id}"))

    def _encrypt_item(
        self, item: VaultRecord, existing: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        body = {k: copy.deepcopy(item[k]) for k in _WRITABLE_FIELDS if k in item}
        key = self._owner_key(body.get("organizationId"))
        body["name"] = _encrypt_optional(body.get("name"), key)
        body["notes"] = _encrypt_optional(body.get("notes"), key)
        for section, names in _ENCRYPTED_SUBFIELDS.items():
            sub = body.get(section)
            if isinstance(sub, dict):
                for name in names:
                    sub[name] = _encrypt_optional(sub.get(name), key)
        login = body.get("login")
        if isinstance(login, dict):
            for uri in login.get("uris") or []:
                uri["uri"] = _encrypt_optional(uri.get("uri"), key)
            if login.get("fido2Credentials"):
                previous = ((existing or {}).get("login") or {}).get("fido2Credentials")
                if previous is None:
                    raise CryptoError(
                        "passkeys cannot be created by the native backend"
                    )
                login["fido2Credentials"] = previous
        for field in body.get("fields") or []:
            field["name"] = _encrypt_optional(field.get("name"), key)
            field["value"] = _encrypt_optional(field.get("value"), key)
        for entry in body.get("passwordHistory") or []:
            entry["password"] = _encrypt_optional(entry.get("password"), key)
        return body

    def create_item(self, item: VaultRecord) -> VaultRecord:
        body = self._encrypt_item(item)
        if body.get("organizationId"):
            created = self._api.request(
                "POST",
                "api/ciphers/create",
                json_body={
                    "cipher": body,
                    "collectionIds": item.get("collectionIds") or [],
                },
            )
        else:
            created = self._api.request("POST", "api/ciphers", json_body=body)
        return self.decrypt_item(created)

    def edit_item(self, item_id: str, item: VaultRecord) -> VaultRecord:
        existing = self._api.request("GET", f"api/ciphers/{item_id}")
        body = self._encrypt_item(item, existing)
        body["lastKnownRevisionDate"] = existing.get("revisionDate")
        updated = self._api.request("PUT", f"api/ciphers/{item_id}", json_body=body)
        return self.decrypt_item(updated)

    def list_folders(self) -> list[VaultRecord]:
        key = self._unlock()
        folders = self._api.sync_vault().get("folders") or []
        return [
            {
                "object": "folder",
                "id": f.get("id"),
                "name": self._decrypt_value(f.get("name"), key),
                "revisionDate": f.get("revisionDate"),
            }
            for f in folders
        ]

    def create_folder(self, name: str) -> VaultRecord:
        key = self._unlock()
        created = self._api.request(
            "POST", "api/folders", json_body={"name": encrypt_string(name, key)}
        )
        return {
            "object": "folder",
            "id": created.get("id"),
            "name": name,
            "revisionDate": created.get("revisionDate"),
        }

    def lock(self) -> None:
        self._password = None
        self._email = None
        self._user_key = None
        self._org_keys = {}
