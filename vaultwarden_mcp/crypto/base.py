"""Backend-neutral contract for reading and writing decrypted vault data.

Vaultwarden stores every item name, password, note, and key encrypted on the client, so
any operation that reads or writes those fields needs the account's keys. A
``VaultCrypto`` backend owns that key material and exposes the vault at the item level.
Decrypted records use the Bitwarden CLI JSON shape (``id``, ``type``, ``name``,
``login.username``, ``revisionDate``…), so higher-level operations such as deduplication
behave identically on every backend.

Backends:

* ``native`` (default) — pure Python key derivation and EncString handling.
* ``bw_cli`` — delegates to an installed Bitwarden CLI.

Operations that act only on identifiers (bulk soft delete, move to folder, purge, admin
user management) never need a backend; they use the API client directly.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

VaultRecord = dict[str, Any]


@runtime_checkable
class VaultCrypto(Protocol):
    """Item-level access to one unlocked vault account."""

    name: str

    def account_email(self) -> str:
        """Return the email of the unlocked account."""
        ...

    def list_items(self, *, include_trash: bool = False) -> list[VaultRecord]:
        """Return every decrypted item the account can read."""
        ...

    def get_item(self, item_id: str) -> VaultRecord:
        """Return one decrypted item."""
        ...

    def create_item(self, item: VaultRecord) -> VaultRecord:
        """Encrypt and create an item; return the stored, decrypted record."""
        ...

    def edit_item(self, item_id: str, item: VaultRecord) -> VaultRecord:
        """Encrypt and replace an item; return the stored, decrypted record."""
        ...

    def list_folders(self) -> list[VaultRecord]:
        """Return decrypted folders (``id``, ``name``)."""
        ...

    def create_folder(self, name: str) -> VaultRecord:
        """Encrypt and create a folder."""
        ...

    def lock(self) -> None:
        """Discard all key material held by the backend."""
        ...
