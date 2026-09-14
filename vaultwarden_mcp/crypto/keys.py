"""Bitwarden account key derivation.

Mirrors ``bitwarden/sdk-internal`` ``bitwarden-crypto`` (``keys/kdf.rs``,
``keys/master_key.rs``, ``keys/utils.rs``, ``keys/shareable_key.rs``):

* master key = PBKDF2-SHA256 or Argon2id over the password, salted with the trimmed,
  lowercased email (Argon2id receives SHA-256 of that salt);
* master password hash = PBKDF2-HMAC-SHA256(master key, password, 1 or 2 rounds);
* stretched master key = HKDF-Expand(master key, "enc") || HKDF-Expand(master key, "mac");
* shareable (Send) key = HKDF-Expand(HMAC-SHA256("bitwarden-" + name, secret), info, 64).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand

from .encstring import (
    CryptoError,
    EncryptionType,
    EncString,
    SymmetricKey,
    decrypt_bytes,
)

PBKDF2_MIN_ITERATIONS = 5_000
ARGON2_MIN_ITERATIONS = 2
ARGON2_MIN_MEMORY_MIB = 16
ARGON2_MIN_PARALLELISM = 1


class KdfType(IntEnum):
    PBKDF2_SHA256 = 0
    ARGON2ID = 1


class HashPurpose(IntEnum):
    SERVER_AUTHORIZATION = 1
    LOCAL_AUTHORIZATION = 2


@dataclass(frozen=True)
class KdfParams:
    kind: KdfType
    iterations: int
    memory_mib: int | None = None
    parallelism: int | None = None

    def __post_init__(self) -> None:
        if self.kind == KdfType.PBKDF2_SHA256:
            if self.iterations < PBKDF2_MIN_ITERATIONS:
                raise CryptoError("PBKDF2 iterations below the Bitwarden minimum")
            return
        if (
            self.iterations < ARGON2_MIN_ITERATIONS
            or (self.memory_mib or 0) < ARGON2_MIN_MEMORY_MIB
            or (self.parallelism or 0) < ARGON2_MIN_PARALLELISM
        ):
            raise CryptoError("Argon2id parameters below the Bitwarden minimum")

    @classmethod
    def from_response(cls, payload: dict[str, Any]) -> KdfParams:
        """Read KDF settings from a prelogin, token, or profile response (any casing)."""
        folded = {str(k).lower(): v for k, v in payload.items()}
        try:
            kind = KdfType(int(folded["kdf"]))
            iterations = int(folded["kdfiterations"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CryptoError("response does not carry KDF settings") from exc
        memory = folded.get("kdfmemory")
        parallelism = folded.get("kdfparallelism")
        return cls(
            kind,
            iterations,
            int(memory) if memory is not None else None,
            int(parallelism) if parallelism is not None else None,
        )


def derive_master_key(password: str, email: str, kdf: KdfParams) -> bytes:
    """Derive the 32-byte master key."""
    secret = password.encode("utf-8")
    salt = email.strip().lower().encode("utf-8")
    if kdf.kind == KdfType.PBKDF2_SHA256:
        return hashlib.pbkdf2_hmac("sha256", secret, salt, kdf.iterations, dklen=32)
    return hash_secret_raw(
        secret,
        hashlib.sha256(salt).digest(),
        time_cost=kdf.iterations,
        memory_cost=(kdf.memory_mib or 0) * 1024,
        parallelism=kdf.parallelism or 1,
        hash_len=32,
        type=Type.ID,
        version=19,
    )


def master_password_hash(
    master_key: bytes,
    password: str,
    purpose: HashPurpose = HashPurpose.SERVER_AUTHORIZATION,
) -> str:
    """The base64 hash sent to the server (purpose 1) or kept for local checks (2)."""
    digest = hashlib.pbkdf2_hmac(
        "sha256", master_key, password.encode("utf-8"), int(purpose), dklen=32
    )
    return base64.b64encode(digest).decode("ascii")


def _hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    return HKDFExpand(algorithm=hashes.SHA256(), length=length, info=info).derive(prk)


def stretch_master_key(master_key: bytes) -> SymmetricKey:
    if len(master_key) != 32:
        raise CryptoError("master key must be 32 bytes")
    return SymmetricKey(
        _hkdf_expand(master_key, b"enc", 32), _hkdf_expand(master_key, b"mac", 32)
    )


def decrypt_user_key(protected_key: str, master_key: bytes) -> SymmetricKey:
    """Unwrap the account's user key from the ``Key`` field.

    Current accounts wrap it as type 2 under the stretched master key; very old accounts
    use type 0 under the raw master key.
    """
    enc = EncString.parse(protected_key)
    if enc.enc_type == EncryptionType.AES_CBC256_HMAC_SHA256_B64:
        raw = decrypt_bytes(enc, stretch_master_key(master_key))
    elif enc.enc_type == EncryptionType.AES_CBC256_B64:
        raw = decrypt_bytes(enc, SymmetricKey(master_key), allow_legacy=True)
    else:
        raise CryptoError("user key must be a symmetric EncString")
    key = SymmetricKey.from_bytes(raw)
    if key.mac_key is None:
        raise CryptoError("user key must contain a MAC key")
    return key


def derive_shareable_key(
    secret: bytes, name: str, info: str | None = None
) -> SymmetricKey:
    """Derive a key from a 16-byte shared secret (Send links use name="send", info="send")."""
    if len(secret) != 16:
        raise CryptoError("shareable key secret must be 16 bytes")
    prk = hmac.new(f"bitwarden-{name}".encode(), secret, hashlib.sha256).digest()
    raw = _hkdf_expand(prk, (info or "").encode("utf-8"), 64)
    return SymmetricKey.from_bytes(raw)
