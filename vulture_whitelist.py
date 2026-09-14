"""Vulture whitelist for vaultwarden-mcp.

Each entry names a genuine false positive and says why vulture is wrong.
"""

# crypto/base.py: ``include_trash`` is a keyword parameter of the ``VaultCrypto``
# protocol method signature; implementations use it, the protocol body cannot.
include_trash: bool | None = None
assert include_trash is None
