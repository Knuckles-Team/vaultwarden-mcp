"""NativeVaultCrypto against a synthetic account built with the package's own primitives.

Interoperability with real Bitwarden data is covered by the known-answer vectors in
``test_crypto_vectors.py``; this module exercises the key hierarchy and record mapping.
"""

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from vaultwarden_mcp.crypto.base import VaultCrypto
from vaultwarden_mcp.crypto.encstring import (
    CryptoError,
    SymmetricKey,
    decrypt_string,
    encrypt_bytes,
    encrypt_rsa,
    encrypt_string,
)
from vaultwarden_mcp.crypto.keys import (
    KdfParams,
    KdfType,
    derive_master_key,
    stretch_master_key,
)
from vaultwarden_mcp.crypto.native import NativeVaultCrypto

PASSWORD = "correct horse battery staple"
EMAIL = "Owner@Example.com"
KDF = {"Kdf": 0, "KdfIterations": 5000, "KdfMemory": None, "KdfParallelism": None}


class FakeApi:
    def __init__(self):
        master_key = derive_master_key(
            PASSWORD, EMAIL, KdfParams(KdfType.PBKDF2_SHA256, 5000)
        )
        self.user_key = SymmetricKey.generate()
        self.org_key = SymmetricKey.generate()
        self.item_key = SymmetricKey.generate()
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pkcs8 = private.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        self.profile = {
            "email": EMAIL,
            "key": str(
                encrypt_bytes(self.user_key.to_bytes(), stretch_master_key(master_key))
            ),
            "privateKey": str(encrypt_bytes(pkcs8, self.user_key)),
            "organizations": [
                {
                    "id": "org-1",
                    "key": str(
                        encrypt_rsa(self.org_key.to_bytes(), private.public_key())
                    ),
                }
            ],
        }
        self.ciphers = {
            "personal": self._login("personal", self.user_key, password="hunter2"),
            "org": self._login("org", self.org_key, organizationId="org-1"),
            "keyed": self._login(
                "keyed",
                self.item_key,
                key=str(encrypt_bytes(self.item_key.to_bytes(), self.user_key)),
            ),
            "trashed": self._login(
                "trashed", self.user_key, deletedDate="2026-01-01T00:00:00Z"
            ),
        }
        self.folders = [
            {
                "id": "f1",
                "name": encrypt_string("Personal", self.user_key),
                "revisionDate": "r",
            }
        ]
        self.requests = []

    def _login(self, cid, enc_key, password="pw", **extra):
        cipher = {
            "id": cid,
            "type": 1,
            "name": encrypt_string(f"Item {cid}", enc_key),
            "notes": None,
            "revisionDate": "2026-02-02T00:00:00Z",
            "login": {
                "username": encrypt_string("user@example.com", enc_key),
                "password": encrypt_string(password, enc_key),
                "uris": [
                    {
                        "uri": encrypt_string("https://example.com", enc_key),
                        "match": None,
                    }
                ],
                "fido2Credentials": [],
            },
            "fields": [
                {
                    "name": encrypt_string("pin", enc_key),
                    "value": encrypt_string("1234", enc_key),
                    "type": 1,
                }
            ],
            "attachments": [
                {
                    "id": "a1",
                    "fileName": encrypt_string("f.txt", enc_key),
                    "key": "2.opaque",
                }
            ],
            "organizationId": None,
        }
        cipher.update(extra)
        return cipher

    def token_response(self):
        return {**KDF, "Key": self.profile["key"]}

    def sync_vault(self, *, exclude_domains=True):
        return {
            "profile": self.profile,
            "ciphers": list(self.ciphers.values()),
            "folders": self.folders,
        }

    def request(self, method, path, **kwargs):
        self.requests.append((method, path, kwargs))
        if method == "GET":
            return self.ciphers[path.rsplit("/", 1)[1]]
        if path == "api/folders":
            return {"id": "f2", "revisionDate": "r2"}
        body = kwargs["json_body"]
        return {**(body.get("cipher") or body), "id": "new", "revisionDate": "r3"}


@pytest.fixture
def api():
    return FakeApi()


def test_backend_satisfies_the_protocol(api):
    assert isinstance(NativeVaultCrypto(api, master_password=PASSWORD), VaultCrypto)


def test_lists_decrypted_personal_org_and_item_key_records(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    items = {i["id"]: i for i in crypto.list_items()}
    assert set(items) == {"personal", "org", "keyed"}
    assert items["personal"]["login"]["password"] == "hunter2"
    assert items["org"]["name"] == "Item org"
    assert items["keyed"]["login"]["uris"][0]["uri"] == "https://example.com"
    assert items["personal"]["fields"][0] == {"name": "pin", "value": "1234", "type": 1}
    assert items["personal"]["object"] == "item"
    assert "key" not in items["keyed"]
    assert "key" not in items["personal"]["attachments"][0]
    assert crypto.account_email() == EMAIL


def test_include_trash(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    assert len(crypto.list_items(include_trash=True)) == 4


def test_wrong_master_password_fails_closed(api):
    with pytest.raises(CryptoError, match="did not unlock"):
        NativeVaultCrypto(api, master_password="wrong").list_items()


def test_missing_master_password_is_rejected(api):
    with pytest.raises(CryptoError):
        NativeVaultCrypto(api, master_password=None)


def test_create_encrypts_every_secret_field(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    record = {
        "type": 1,
        "name": "New",
        "notes": "private note",
        "login": {
            "username": "u",
            "password": "p",
            "uris": [{"uri": "https://n.example"}],
        },
        "fields": [{"name": "k", "value": "v", "type": 0}],
    }
    created = crypto.create_item(record)
    body = api.requests[-1][2]["json_body"]
    for value in (
        body["name"],
        body["notes"],
        body["login"]["password"],
        body["login"]["uris"][0]["uri"],
        body["fields"][0]["value"],
    ):
        assert value.startswith("2.")
    assert decrypt_string(body["login"]["password"], api.user_key) == "p"
    assert created["login"]["password"] == "p"


def test_org_items_are_created_with_collections_and_the_org_key(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    crypto.create_item(
        {
            "type": 2,
            "name": "Shared",
            "organizationId": "org-1",
            "collectionIds": ["c1"],
            "secureNote": {"type": 0},
        }
    )
    method, path, kwargs = api.requests[-1]
    assert path == "api/ciphers/create"
    assert kwargs["json_body"]["collectionIds"] == ["c1"]
    assert (
        decrypt_string(kwargs["json_body"]["cipher"]["name"], api.org_key) == "Shared"
    )


def test_edit_sends_last_known_revision_and_keeps_existing_passkeys(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    api.ciphers["personal"]["login"]["fido2Credentials"] = [{"credentialId": "2.enc"}]
    item = crypto.get_item("personal")
    item["login"]["password"] = "rotated"
    item["login"]["fido2Credentials"] = [{"credentialId": "decrypted"}]
    crypto.edit_item("personal", item)
    body = api.requests[-1][2]["json_body"]
    assert body["lastKnownRevisionDate"] == "2026-02-02T00:00:00Z"
    assert body["login"]["fido2Credentials"] == [{"credentialId": "2.enc"}]
    assert decrypt_string(body["login"]["password"], api.user_key) == "rotated"


def test_creating_passkeys_is_refused(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    with pytest.raises(CryptoError, match="passkeys"):
        crypto.create_item(
            {"type": 1, "name": "x", "login": {"fido2Credentials": [{"a": 1}]}}
        )


def test_folders(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    assert crypto.list_folders()[0]["name"] == "Personal"
    assert crypto.create_folder("Work")["name"] == "Work"
    assert (
        decrypt_string(api.requests[-1][2]["json_body"]["name"], api.user_key) == "Work"
    )


def test_lock_discards_keys_and_password(api):
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    crypto.list_items()
    crypto.lock()
    with pytest.raises(CryptoError, match="locked"):
        crypto.list_items()


def test_undecryptable_items_are_reported_by_id_only(api):
    api.ciphers["personal"]["name"] = encrypt_string("secret", SymmetricKey.generate())
    crypto = NativeVaultCrypto(api, master_password=PASSWORD)
    with pytest.raises(CryptoError) as exc_info:
        crypto.list_items()
    assert "personal" in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
