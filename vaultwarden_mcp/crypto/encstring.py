"""Bitwarden EncString wire format and the primitives that read and write it.

Interoperable with ``bitwarden/sdk-internal`` ``bitwarden-crypto``:

* type 2 ``AesCbc256_HmacSha256_B64`` — ``2.iv|data|mac``; AES-256-CBC with PKCS7, then
  HMAC-SHA256 over ``iv || data``. The MAC is verified in constant time before any
  decryption. Every new symmetric encryption uses this type.
* type 0 ``AesCbc256_B64`` — ``0.iv|data`` with no MAC. Only accepted when a caller opts in
  for unwrapping a legacy user key; never produced.
* types 3/4 ``Rsa2048_OaepSha256_B64`` / ``Rsa2048_OaepSha1_B64`` — RSA-OAEP key wraps.
* types 5/6 — deprecated MAC'd RSA variants; decrypted like 3/4, never produced.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from enum import IntEnum

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import (
    load_der_private_key,
    load_der_public_key,
)

_IV_SIZE = 16
_KEY_SIZE = 32


class CryptoError(ValueError):
    """A value could not be parsed, authenticated, or decrypted."""


class EncryptionType(IntEnum):
    AES_CBC256_B64 = 0
    AES_CBC256_HMAC_SHA256_B64 = 2
    RSA2048_OAEP_SHA256_B64 = 3
    RSA2048_OAEP_SHA1_B64 = 4
    RSA2048_OAEP_SHA256_HMAC_SHA256_B64 = 5
    RSA2048_OAEP_SHA1_HMAC_SHA256_B64 = 6


_SYMMETRIC_TYPES = {
    EncryptionType.AES_CBC256_B64,
    EncryptionType.AES_CBC256_HMAC_SHA256_B64,
}
_SHA256_RSA_TYPES = {
    EncryptionType.RSA2048_OAEP_SHA256_B64,
    EncryptionType.RSA2048_OAEP_SHA256_HMAC_SHA256_B64,
}
_PART_COUNTS = {
    EncryptionType.AES_CBC256_B64: 2,
    EncryptionType.AES_CBC256_HMAC_SHA256_B64: 3,
    EncryptionType.RSA2048_OAEP_SHA256_B64: 1,
    EncryptionType.RSA2048_OAEP_SHA1_B64: 1,
    EncryptionType.RSA2048_OAEP_SHA256_HMAC_SHA256_B64: 2,
    EncryptionType.RSA2048_OAEP_SHA1_HMAC_SHA256_B64: 2,
}


@dataclass(frozen=True, repr=False)
class SymmetricKey:
    """An AES-256 key with its HMAC-SHA256 key (``mac_key`` is None only for legacy keys)."""

    enc_key: bytes
    mac_key: bytes | None = None

    def __post_init__(self) -> None:
        if len(self.enc_key) != _KEY_SIZE:
            raise CryptoError("encryption key must be 32 bytes")
        if self.mac_key is not None and len(self.mac_key) != _KEY_SIZE:
            raise CryptoError("MAC key must be 32 bytes")

    @classmethod
    def from_bytes(cls, raw: bytes) -> SymmetricKey:
        if len(raw) == 2 * _KEY_SIZE:
            return cls(raw[:_KEY_SIZE], raw[_KEY_SIZE:])
        if len(raw) == _KEY_SIZE:
            return cls(raw)
        raise CryptoError("symmetric key must be 32 or 64 bytes")

    @classmethod
    def generate(cls) -> SymmetricKey:
        return cls(os.urandom(_KEY_SIZE), os.urandom(_KEY_SIZE))

    def to_bytes(self) -> bytes:
        return self.enc_key + (self.mac_key or b"")

    def __repr__(self) -> str:
        return "SymmetricKey(<redacted>)"


def _b64decode(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except ValueError as exc:
        raise CryptoError("invalid base64 in EncString") from exc


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


@dataclass(frozen=True)
class EncString:
    """A parsed EncString. ``iv`` and ``mac`` are None where the type has none."""

    enc_type: EncryptionType
    data: bytes
    iv: bytes | None = None
    mac: bytes | None = None

    @classmethod
    def parse(cls, value: str) -> EncString:
        if not isinstance(value, str) or not value:
            raise CryptoError("EncString must be a non-empty string")
        header, dot, body = value.partition(".")
        if dot and header.isdigit():
            try:
                enc_type = EncryptionType(int(header))
            except ValueError as exc:
                raise CryptoError(f"unsupported EncString type {header}") from exc
            parts = body.split("|")
        else:
            # Pre-type-prefix legacy form: infer from the part count.
            parts = value.split("|")
            enc_type = (
                EncryptionType.AES_CBC256_HMAC_SHA256_B64
                if len(parts) == 3
                else EncryptionType.AES_CBC256_B64
            )
        if len(parts) != _PART_COUNTS[enc_type]:
            raise CryptoError(
                f"EncString type {int(enc_type)} expects "
                f"{_PART_COUNTS[enc_type]} parts, got {len(parts)}"
            )
        decoded = [_b64decode(p) for p in parts]
        if enc_type in _SYMMETRIC_TYPES:
            iv, data = decoded[0], decoded[1]
            if len(iv) != _IV_SIZE:
                raise CryptoError("EncString IV must be 16 bytes")
            mac = decoded[2] if len(decoded) == 3 else None
            return cls(enc_type, data, iv=iv, mac=mac)
        return cls(enc_type, decoded[0], mac=decoded[1] if len(decoded) == 2 else None)

    def __str__(self) -> str:
        if self.enc_type in _SYMMETRIC_TYPES:
            parts = [self.iv or b"", self.data]
        else:
            parts = [self.data]
        if self.mac is not None:
            parts.append(self.mac)
        return f"{int(self.enc_type)}." + "|".join(_b64encode(p) for p in parts)


def _mac(mac_key: bytes, iv: bytes, data: bytes) -> bytes:
    return hmac.new(mac_key, iv + data, hashlib.sha256).digest()


def encrypt_bytes(plaintext: bytes, key: SymmetricKey) -> EncString:
    """Encrypt as a type 2 EncString with a fresh random IV."""
    if key.mac_key is None:
        raise CryptoError("type 2 encryption requires a key with a MAC key")
    iv = os.urandom(_IV_SIZE)
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key.enc_key), modes.CBC(iv)).encryptor()
    data = encryptor.update(padded) + encryptor.finalize()
    return EncString(
        EncryptionType.AES_CBC256_HMAC_SHA256_B64,
        data,
        iv=iv,
        mac=_mac(key.mac_key, iv, data),
    )


def encrypt_string(plaintext: str, key: SymmetricKey) -> str:
    return str(encrypt_bytes(plaintext.encode("utf-8"), key))


def _aes_cbc_decrypt(enc_key: bytes, iv: bytes, data: bytes) -> bytes:
    decryptor = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(data) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    try:
        return unpadder.update(padded) + unpadder.finalize()
    except ValueError as exc:
        raise CryptoError("invalid padding") from exc


def decrypt_bytes(
    value: str | EncString, key: SymmetricKey, *, allow_legacy: bool = False
) -> bytes:
    """Authenticate and decrypt a symmetric EncString.

    Type 0 carries no MAC, so it is refused unless ``allow_legacy`` is set — the only
    legitimate use is unwrapping a very old account's user key.
    """
    enc = value if isinstance(value, EncString) else EncString.parse(value)
    if enc.iv is None:
        raise CryptoError("not a symmetric EncString")
    if enc.enc_type == EncryptionType.AES_CBC256_HMAC_SHA256_B64:
        if key.mac_key is None or enc.mac is None:
            raise CryptoError("type 2 EncString requires a MAC and a MAC key")
        if not hmac.compare_digest(enc.mac, _mac(key.mac_key, enc.iv, enc.data)):
            raise CryptoError("MAC verification failed")
        return _aes_cbc_decrypt(key.enc_key, enc.iv, enc.data)
    if enc.enc_type == EncryptionType.AES_CBC256_B64 and allow_legacy:
        return _aes_cbc_decrypt(key.enc_key, enc.iv, enc.data)
    raise CryptoError(f"refusing to decrypt EncString type {int(enc.enc_type)}")


def decrypt_string(value: str, key: SymmetricKey) -> str:
    return decrypt_bytes(value, key).decode("utf-8")


def _oaep(enc_type: EncryptionType) -> rsa_padding.OAEP:
    algorithm: hashes.HashAlgorithm = (
        hashes.SHA256()
        if enc_type in _SHA256_RSA_TYPES
        else hashes.SHA1()  # nosec B303 - Bitwarden RSA-OAEP type 4 mandates SHA-1
    )
    return rsa_padding.OAEP(
        mgf=rsa_padding.MGF1(algorithm=algorithm), algorithm=algorithm, label=None
    )


def decrypt_rsa(value: str | EncString, private_key: RSAPrivateKey) -> bytes:
    """Unwrap an RSA-OAEP EncString (types 3-6; the MAC of 5/6 is not required)."""
    enc = value if isinstance(value, EncString) else EncString.parse(value)
    if enc.enc_type in _SYMMETRIC_TYPES:
        raise CryptoError("not an RSA EncString")
    try:
        return private_key.decrypt(enc.data, _oaep(enc.enc_type))
    except ValueError as exc:
        raise CryptoError("RSA decryption failed") from exc


def encrypt_rsa(
    plaintext: bytes,
    public_key: RSAPublicKey,
    enc_type: EncryptionType = EncryptionType.RSA2048_OAEP_SHA1_B64,
) -> EncString:
    """Wrap bytes (normally a key) for a recipient's RSA public key."""
    if enc_type not in {
        EncryptionType.RSA2048_OAEP_SHA256_B64,
        EncryptionType.RSA2048_OAEP_SHA1_B64,
    }:
        raise CryptoError("only RSA-OAEP types 3 and 4 may be produced")
    return EncString(enc_type, public_key.encrypt(plaintext, _oaep(enc_type)))


def load_private_key(pkcs8_der: bytes) -> RSAPrivateKey:
    key = load_der_private_key(pkcs8_der, password=None)
    if not isinstance(key, RSAPrivateKey):
        raise CryptoError("account private key is not an RSA key")
    return key


def load_public_key(spki_der: bytes) -> RSAPublicKey:
    key = load_der_public_key(spki_der)
    if not isinstance(key, RSAPublicKey):
        raise CryptoError("public key is not an RSA key")
    return key
