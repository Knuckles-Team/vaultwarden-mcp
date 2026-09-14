"""Known-answer tests against Bitwarden's own crypto test vectors.

Vectors are reproduced from ``bitwarden/sdk-internal`` crate ``bitwarden-crypto`` at commit
``183f1b778aaaef98a43af2280f56880a8de86b18`` (``keys/kdf.rs``, ``keys/utils.rs``, ``keys/master_key.rs``,
``keys/shareable_key.rs``, ``enc_string/symmetric.rs``, ``enc_string/asymmetric.rs``).
The RSA key below is that crate's public test fixture, not a real account key.
"""

import base64
import hashlib

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.primitives.serialization import load_der_private_key

from vaultwarden_mcp.crypto.encstring import (
    CryptoError,
    EncryptionType,
    EncString,
    SymmetricKey,
    decrypt_bytes,
    decrypt_rsa,
    encrypt_bytes,
    encrypt_rsa,
)
from vaultwarden_mcp.crypto.keys import (
    HashPurpose,
    KdfParams,
    KdfType,
    decrypt_user_key,
    derive_master_key,
    derive_shareable_key,
    master_password_hash,
    stretch_master_key,
)

MASTER_KEY = bytes(
    [
        31,
        79,
        104,
        226,
        150,
        71,
        177,
        90,
        194,
        80,
        172,
        209,
        17,
        129,
        132,
        81,
        138,
        167,
        69,
        167,
        254,
        149,
        2,
        27,
        39,
        197,
        64,
        42,
        22,
        195,
        86,
        75,
    ]
)

# Bitwarden's public RSA test fixture (PKCS#8 DER, base64) from the same commit.
RSA_TEST_KEY_DER_B64 = (
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCXRVrCX+2hfOQS8HzYUS2oc/jG"
    "VTZpv+/Ryuoh9d8ihYX9dd0cYh2tl6KWdFc88lPUH11Oxqy20Rk2e5r/RF6T9yM0Me3NPnaKt+hl"
    "hLtfoc0h86LnhD56A9FDUfuI0dVnPcrwNv0YJIo94LwxtbqBULNvXl6wJ7WAbODrCQy5ZgMVg+iH"
    "+gGpwiqsZqHt+KuoHWcN53MSPDfaF4/YMB99U3TziJMOOJask1TEEnakMPln11PczNDazT17DXIx"
    "YrbPfutPdh6sLs6AQOajdZijfEvepgnOe7cQ7aeatiOJFrjTApKPGxOVRzEMX4XS4xbyhH0QxQeB"
    "6l16l8C0uxIBAgMBAAECggEASaWfeVDA3cVzOPFSpvJm20OTE+R6uGOU+7vh36TX/POq92qBuwbd"
    "0h0oMD32FxsXywd2IxtBDUSiFM9699qufTVuM0Q3tZw6lHDTOVG08+tPdr8qSbMtw7PGFxN79fHL"
    "BxejjO4IrM9lapjWpxEF+11x7r+wM+0xRZQ8sNFYG46aPfIaty4BGbL0I2DQ2y8I57iBCAy69eht"
    "59NLMm27fRWGJIWCuBIjlpfzET1j2HLXUIh5bTBNzqaN039WH49HczGE3mQKVEJZc/efk3HaVd0a"
    "1Sjzyn0QY+N1jtZN3jTRbuDWA1AknkX1LX/0tUhuS3/7C3ejHxjw4Dk1ZLo5/QKBgQDIWvqFn0+I"
    "KRSu6Ua2hDsufIHHUNLelbfLUMmFthxabcUn4zlvIscJO00Tq/ezopSRRvbGiqnxjv/mYxucvOUB"
    "eZtlus0Q9RTACBtw9TGoNTmQbEunJ2FOSlqbQxkBBAjgGEppRPt30iGj/VjAhCATq2MYOa/X4dVR"
    "51BqQAFIEwKBgQDBSIfTFKC/hDk6FKZlgwvupWYJyU9RkyfstPErZFmzoKhPkQ3YORo2oeAYmVUb"
    "S9I2iIYpYpYQJHX8jMuCbCz4ONxTCuSIXYQYUcUq4PglCKp31xBAE6TN8SvhfME9/MvuDssnQinA"
    "HuF0GDAhF646T3LLS1not6Vszv7brwSoGwKBgQC88v/8cGfi80ssQZeMnVvq1UTXIeQcQnoY5lGH"
    "Jl3K8mbS3TnXE6c9j417Fdz+rj8KWzBzwWXQB5pSPflWcdZO886Xu/mVGmy9RWgLuVFhXwCwsVEP"
    "jNX5ramRb0/vY0yzenUCninBsIxFSbIfrPtLUYCc4hpxr+sr2Mg/y6jpvQKBgBezMRRs3xkcuXep"
    "uI2R+BCXL1/b02IJTUf1F+1eLLGd7YV0H+J3fgNc7gGWK51hOrF9JBZHBGeOUPlaukmPwiPdtQZp"
    "u4QNE3l37VlIpKTF30E6mb+BqR+nht3rUjarnMXgAoEZ18y6/KIjpSMpqC92Nnk/EBM9EYe6Cf4e"
    "A9ApAoGAeqEUg46UTlJySkBKURGpIs3v1kkf5I0X8DnOhwb+HPxNaiEdmO7ckm8+tPVgppLcG0+t"
    "MdLjigFQiDUQk2y3WjyxP5ZvXu7U96jaJRI8PFMoE06WeVYcdIzrID2HvqH+w0UQJFrLJ/0Mn4st"
    "FAEzXKZBokBGnjFnTnKcs7nv/O8="
)
RSA_OAEP_SHA256 = "3.SUx5gWrgmAKs/S1BoQrqOmx2Hl5fPVBVHokW17Flvm4TpBnJJRkfoitp7Jc4dfazPYjWGlckJz6X+qe+/AWilS1mxtzS0PmDy7tS5xP0GRlB39dstCd5jDw1wPmTbXiLcQ5VTvzpRAfRMEYVveTsEvVTByvEYAGSn4TnCsUDykyhRbD0YcJ4r1KHLs1b3BCBy2M1Gl5nmwckH08CAXaf8VfuBFStAGRKueovqp4euneQla+4G4fXdVvb8qKPnu0iVuALIE6nUNmeOiA3xN3d+akMxbbGxrQ1Ca4TYWjHVdj9C6abngQHkjKNYQwGUXrYo160hP4LIHn/huK6bZe5dQ=="
RSA_OAEP_SHA1 = "4.DMD1D5r6BsDDd7C/FE1eZbMCKrmryvAsCKj6+bO54gJNUxisOI7SDcpPLRXf+JdhqY15pT+wimQ5cD9C+6OQ6s71LFQHewXPU29l9Pa1JxGeiKqp37KLYf+1IS6UB2K3ANN35C52ZUHh2TlzIS5RuntxnpCw7APbcfpcnmIdLPJBtuj/xbFd6eBwnI3GSe5qdS6/Ixdd0dgsZcpz3gHJBKmIlSo0YN60SweDq3kTJwox9xSqdCueIDg5U4khc7RhjYx8b33HXaNJj3DwgIH8iLj+lqpDekogr630OhHG3XRpvl4QzYO45bmHb8wAh67Dj70nsZcVg6bAEFHdSFohww=="
RSA_OAEP_SHA1_HMAC = "6.DMD1D5r6BsDDd7C/FE1eZbMCKrmryvAsCKj6+bO54gJNUxisOI7SDcpPLRXf+JdhqY15pT+wimQ5cD9C+6OQ6s71LFQHewXPU29l9Pa1JxGeiKqp37KLYf+1IS6UB2K3ANN35C52ZUHh2TlzIS5RuntxnpCw7APbcfpcnmIdLPJBtuj/xbFd6eBwnI3GSe5qdS6/Ixdd0dgsZcpz3gHJBKmIlSo0YN60SweDq3kTJwox9xSqdCueIDg5U4khc7RhjYx8b33HXaNJj3DwgIH8iLj+lqpDekogr630OhHG3XRpvl4QzYO45bmHb8wAh67Dj70nsZcVg6bAEFHdSFohww==|AA=="


def _seeded_test_key(seed: str) -> bytes:
    """``SymmetricCryptoKey::generate_seeded_for_unit_tests``: ChaCha20 keystream
    seeded with SHA-256(seed), first 64 bytes (enc key then MAC key)."""
    cipher = Cipher(
        algorithms.ChaCha20(hashlib.sha256(seed.encode()).digest(), b"\x00" * 16),
        mode=None,
    )
    return cipher.encryptor().update(b"\x00" * 64)


def test_pbkdf2_master_key_vector():
    kdf = KdfParams(KdfType.PBKDF2_SHA256, 10_000)
    assert derive_master_key("67t9b5g67$%Dh89n", "test_key", kdf) == MASTER_KEY


def test_stretch_master_key_vector():
    stretched = stretch_master_key(MASTER_KEY)
    assert stretched.enc_key == bytes(
        [
            111,
            31,
            178,
            45,
            238,
            152,
            37,
            114,
            143,
            215,
            124,
            83,
            135,
            173,
            195,
            23,
            142,
            134,
            120,
            249,
            61,
            132,
            163,
            182,
            113,
            197,
            189,
            204,
            188,
            21,
            237,
            96,
        ]
    )
    assert stretched.mac_key == bytes(
        [
            221,
            127,
            206,
            234,
            101,
            27,
            202,
            38,
            86,
            52,
            34,
            28,
            78,
            28,
            185,
            16,
            48,
            61,
            127,
            166,
            209,
            247,
            194,
            87,
            232,
            26,
            48,
            85,
            193,
            249,
            179,
            155,
        ]
    )


@pytest.mark.parametrize(
    "email", ["test@bitwarden.com", "TEST@bitwarden.com", " test@bitwarden.com"]
)
def test_pbkdf2_password_hash_vector_normalizes_email(email):
    kdf = KdfParams(KdfType.PBKDF2_SHA256, 100_000)
    master_key = derive_master_key("asdfasdf", email, kdf)
    assert (
        master_password_hash(master_key, "asdfasdf", HashPurpose.SERVER_AUTHORIZATION)
        == "wmyadRMyBZOH7P/a/ucTCbSghKgdzDpPqUnu/DAVtSw="
    )


def test_argon2id_password_hash_vector():
    kdf = KdfParams(KdfType.ARGON2ID, 4, memory_mib=32, parallelism=2)
    master_key = derive_master_key("asdfasdf", "test_salt", kdf)
    assert (
        master_password_hash(master_key, "asdfasdf")
        == "PR6UjYmjmppTYcdyTiNbAhPJuQQOmynKbdEl1oyi/iQ="
    )


def test_legacy_type0_user_key_vector():
    kdf = KdfParams(KdfType.PBKDF2_SHA256, 600_000)
    master_key = derive_master_key("asdfasdfasdf", "legacy@bitwarden.com", kdf)
    protected = (
        "0.8UClLa8IPE1iZT7chy5wzQ==|6PVfHnVk5S3XqEtQemnM5yb4JodxmPkkWzmDRdfyHtjORmvxqlLX"
        "40tBJZ+CKxQWmS8tpEB5w39rbgHg/gqs0haGdZG4cPbywsgGzxZ7uNI="
    )
    user_key = decrypt_user_key(protected, master_key)
    assert user_key.enc_key == bytes(
        [
            12,
            95,
            151,
            203,
            37,
            4,
            236,
            67,
            137,
            97,
            90,
            58,
            6,
            127,
            242,
            28,
            209,
            168,
            125,
            29,
            118,
            24,
            213,
            44,
            117,
            202,
            2,
            115,
            132,
            165,
            125,
            148,
        ]
    )
    assert user_key.mac_key == bytes(
        [
            186,
            215,
            234,
            137,
            24,
            169,
            227,
            29,
            218,
            57,
            180,
            237,
            73,
            91,
            189,
            51,
            253,
            26,
            17,
            52,
            226,
            4,
            134,
            75,
            194,
            208,
            178,
            133,
            128,
            224,
            140,
            167,
        ]
    )


def test_legacy_type0_raw_master_key_vector():
    master_key = base64.b64decode("hvBMMb1t79YssFZkpetYsM3deyVuQv4r88Uj9gvYe08=")
    protected = (
        "0.tn/heK4HLbbEe+yEkC+kvw==|8QM94f7aVTtjm/bmvRdVxOxiLiiZtHYYO7+oBdjFCkilncesx0iV"
        "rXPl+tMKqW+Jo7+FtZdPNsTrL6RdoG7i5QbCRVwK+9010+xm7MTQY8s="
    )
    user_key = decrypt_user_key(protected, master_key)
    assert user_key.enc_key == bytes(
        [
            116,
            170,
            187,
            43,
            80,
            212,
            193,
            202,
            234,
            181,
            57,
            66,
            151,
            249,
            59,
            47,
            70,
            16,
            57,
            4,
            170,
            78,
            85,
            241,
            152,
            232,
            91,
            57,
            9,
            87,
            209,
            245,
        ]
    )
    assert user_key.mac_key == bytes(
        [
            40,
            245,
            106,
            140,
            2,
            225,
            138,
            213,
            98,
            223,
            92,
            168,
            135,
            208,
            22,
            194,
            31,
            21,
            178,
            252,
            203,
            198,
            35,
            174,
            53,
            218,
            254,
            151,
            235,
            57,
            7,
            98,
        ]
    )


def test_generic_decrypt_refuses_unauthenticated_type0():
    key = SymmetricKey(base64.b64decode("hvBMMb1t79YssFZkpetYsM3deyVuQv4r88Uj9gvYe08="))
    with pytest.raises(CryptoError):
        decrypt_bytes("0.NQfjHLr6za7VQVAbrpL81w==|wfrjmyJ0bfwkQlySrhw8dA==", key)


@pytest.mark.parametrize(
    ("secret", "name", "info", "expected"),
    [
        (
            b"&/$%F1a895g67HlX",
            "test_key",
            None,
            "4PV6+PcmF2w7YHRatvyMcVQtI7zvCyssv/wFWmzjiH6Iv9altjmDkuBD1aagLVaLezbthbSe+ktR+U6qswxNnQ==",
        ),
        (
            b"67t9b5g67$%Dh89n",
            "test_key",
            "test",
            "F9jVQmrACGx9VUPjuzfMYDjr726JtL300Y3Yg+VYUnVQtQ1s8oImJ5xtp1KALC9h2nav04++1LDW4iFD+infng==",
        ),
    ],
)
def test_shareable_key_vectors(secret, name, info, expected):
    key = derive_shareable_key(secret, name, info)
    assert base64.b64encode(key.to_bytes()).decode() == expected


def test_enc_string_serialization_roundtrip():
    value = "2.pMS6/icTQABtulw52pq2lg==|XXbxKxDTh+mWiN1HjH2N1w==|Q6PkuT+KX/axrgN9ubD5Ajk2YNwxQkgs3WJM0S0wtG8="
    parsed = EncString.parse(value)
    assert parsed.enc_type == EncryptionType.AES_CBC256_HMAC_SHA256_B64
    assert str(parsed) == value
    legacy = "0.pMS6/icTQABtulw52pq2lg==|XXbxKxDTh+mWiN1HjH2N1w=="
    assert str(EncString.parse(legacy)) == legacy


def test_type2_roundtrip_and_tamper_detection():
    key = SymmetricKey.generate()
    enc = encrypt_bytes(b"correct horse battery staple", key)
    assert decrypt_bytes(str(enc), key) == b"correct horse battery staple"
    tampered = EncString(enc.enc_type, enc.data, iv=enc.iv, mac=bytes(32))
    with pytest.raises(CryptoError):
        decrypt_bytes(tampered, key)
    with pytest.raises(CryptoError):
        decrypt_bytes(str(enc), SymmetricKey.generate())


@pytest.mark.parametrize(
    ("value", "enc_type"),
    [
        (RSA_OAEP_SHA256, EncryptionType.RSA2048_OAEP_SHA256_B64),
        (RSA_OAEP_SHA1, EncryptionType.RSA2048_OAEP_SHA1_B64),
        (RSA_OAEP_SHA1_HMAC, EncryptionType.RSA2048_OAEP_SHA1_HMAC_SHA256_B64),
    ],
)
def test_rsa_vectors_unwrap_the_seeded_test_key(value, enc_type):
    private_key = load_der_private_key(
        base64.b64decode(RSA_TEST_KEY_DER_B64), password=None
    )
    assert EncString.parse(value).enc_type == enc_type
    assert decrypt_rsa(value, private_key) == _seeded_test_key("test")


def test_rsa_wrap_roundtrip():
    private_key = load_der_private_key(
        base64.b64decode(RSA_TEST_KEY_DER_B64), password=None
    )
    wrapped = encrypt_rsa(b"\x01" * 64, private_key.public_key())
    assert decrypt_rsa(str(wrapped), private_key) == b"\x01" * 64


def test_keys_are_redacted_in_repr():
    assert "redacted" in repr(SymmetricKey.generate())
