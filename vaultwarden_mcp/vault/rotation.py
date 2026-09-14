"""Password generation and vault-item password rotation.

Rotation follows Bitwarden's own convention: the outgoing password is
prepended to ``login.passwordHistory`` (capped at 5 entries, oldest dropped)
before ``login.password`` is replaced, so the vault always records what
changed and when. Callers never receive the generated or previous password
back from :func:`rotate_item_password` — only identifiers and the revision
timestamp.
"""

from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime
from typing import Any

from ..crypto.base import VaultCrypto, VaultRecord

_MIN_LENGTH = 12
_MAX_LENGTH = 128
_MAX_PASSWORD_HISTORY = 5
_LOGIN_ITEM_TYPE = 1

_LOWERCASE = string.ascii_lowercase
_UPPERCASE = string.ascii_uppercase
_DIGITS = string.digits
_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def generate_password(length: int = 24, use_symbols: bool = True) -> str:
    """Generate a random password with every required character class present.

    ``length`` is clamped to ``[12, 128]``. Guarantees at least one lowercase
    letter, one uppercase letter, one digit, and (when ``use_symbols``) one
    symbol; the remaining characters are drawn uniformly from the full
    alphabet and the whole password is shuffled with :mod:`secrets`.
    """
    length = max(_MIN_LENGTH, min(_MAX_LENGTH, length))
    alphabet = _LOWERCASE + _UPPERCASE + _DIGITS + (_SYMBOLS if use_symbols else "")
    required = [
        secrets.choice(_LOWERCASE),
        secrets.choice(_UPPERCASE),
        secrets.choice(_DIGITS),
    ]
    if use_symbols:
        required.append(secrets.choice(_SYMBOLS))
    password = required + [
        secrets.choice(alphabet) for _ in range(length - len(required))
    ]
    for i in range(len(password) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password[i], password[j] = password[j], password[i]
    return "".join(password)


def rotate_item_password(
    crypto: VaultCrypto,
    item_id: str,
    *,
    length: int = 24,
    use_symbols: bool = True,
) -> dict[str, Any]:
    """Rotate one login item's password, keeping bounded history.

    Reads the item, requires it to be a login item with an existing
    password, records the outgoing password in ``passwordHistory``, then
    writes the new password back through ``crypto.edit_item``. Returns
    ``{"item_id", "rotated": True, "revision_date"}`` — never a password.
    """
    item = crypto.get_item(item_id)
    if item.get("type") != _LOGIN_ITEM_TYPE:
        raise ValueError(f"item {item_id!r} is not a login item")
    login: VaultRecord = dict(item.get("login") or {})
    old_password = login.get("password")
    if not old_password:
        raise ValueError(f"item {item_id!r} has no password to rotate")

    revision_date = _now_iso()
    history: list[VaultRecord] = list(item.get("passwordHistory") or [])
    history.insert(0, {"lastUsedDate": revision_date, "password": old_password})

    login["password"] = generate_password(length, use_symbols)
    login["passwordRevisionDate"] = revision_date
    item["login"] = login
    item["passwordHistory"] = history[:_MAX_PASSWORD_HISTORY]

    crypto.edit_item(item_id, item)
    return {"item_id": item_id, "rotated": True, "revision_date": revision_date}
