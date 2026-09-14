"""Plan and apply vault item deduplication.

Planning is pure: it takes decrypted records (Bitwarden CLI JSON shape) and returns which
copies to keep and which to trash. Applying needs only item identifiers, so it runs
through the API client's bulk soft delete — trashed items stay restorable for 30 days.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlsplit

from ..crypto.base import VaultRecord

DELETE_BATCH_SIZE = 500


class SoftDeleteClient(Protocol):
    def soft_delete_ciphers(self, ids: list[str]) -> Any: ...


@dataclass(frozen=True)
class DuplicateGroup:
    """One set of matching items: the copy to keep and the copies to trash."""

    keep_id: str
    keep_revision_date: str
    drop_ids: tuple[str, ...]


@dataclass(frozen=True)
class DedupePlan:
    """The outcome of planning; contains identifiers only, never item contents."""

    scanned: int
    loose: bool
    groups: tuple[DuplicateGroup, ...] = field(default_factory=tuple)

    @property
    def drop_ids(self) -> list[str]:
        return [item_id for group in self.groups for item_id in group.drop_ids]

    def summary(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "loose": self.loose,
            "duplicate_groups": len(self.groups),
            "extra_copies": len(self.drop_ids),
            "groups": [
                {"keep": g.keep_id, "drop": list(g.drop_ids)} for g in self.groups
            ],
        }


def normalize_uri(uri: str | None) -> str:
    """Reduce a login URI to host + path so trivial variants compare equal."""
    if not uri:
        return ""
    value = uri.strip()
    parts = urlsplit(value if "://" in value else f"https://{value}")
    host = (parts.hostname or "").lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}"


def fingerprint(item: VaultRecord, *, loose: bool = False) -> str:
    """Identity of an item for duplicate detection.

    Exact mode requires every secret-bearing field to match. Loose mode compares only
    name, username, and URIs, so its matches can differ in password or notes and are for
    review, never for automatic deletion.
    """
    login = item.get("login") or {}
    key: dict[str, Any] = {
        "type": item.get("type"),
        "org": item.get("organizationId"),
        "name": (item.get("name") or "").strip().lower(),
        "username": (login.get("username") or "").strip().lower(),
        "uris": sorted({normalize_uri(u.get("uri")) for u in login.get("uris") or []}),
    }
    if not loose:
        key |= {
            "password": login.get("password"),
            "totp": login.get("totp"),
            "notes": (item.get("notes") or "").strip(),
            "card": item.get("card"),
            "identity": item.get("identity"),
            "sshKey": item.get("sshKey"),
            "fields": sorted(
                (f.get("name") or "", f.get("value") or "")
                for f in item.get("fields") or []
            ),
        }
    encoded = json.dumps(key, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def keeper_rank(item: VaultRecord) -> tuple[str, int, int, int]:
    """Most recently edited wins; attachments, passkeys, and history break ties."""
    login = item.get("login") or {}
    return (
        item.get("revisionDate") or "",
        len(item.get("attachments") or []),
        len(login.get("fido2Credentials") or []),
        len(item.get("passwordHistory") or []),
    )


def plan_deduplication(
    items: list[VaultRecord], *, loose: bool = False, include_org: bool = False
) -> DedupePlan:
    """Group matching items and choose the newest copy of each group to keep."""
    candidates = [
        item
        for item in items
        if not item.get("deletedDate")
        and (include_org or not item.get("organizationId"))
    ]
    buckets: dict[str, list[VaultRecord]] = defaultdict(list)
    for item in candidates:
        buckets[fingerprint(item, loose=loose)].append(item)

    groups = []
    for bucket in buckets.values():
        if len(bucket) < 2:
            continue
        keep, *drop = sorted(bucket, key=keeper_rank, reverse=True)
        groups.append(
            DuplicateGroup(
                keep_id=keep["id"],
                keep_revision_date=keep.get("revisionDate") or "",
                drop_ids=tuple(d["id"] for d in drop),
            )
        )
    groups.sort(key=lambda g: g.keep_id)
    return DedupePlan(scanned=len(candidates), loose=loose, groups=tuple(groups))


def apply_plan(client: SoftDeleteClient, plan: DedupePlan) -> int:
    """Move every extra copy to trash in bulk; return how many were trashed."""
    if plan.loose:
        raise ValueError(
            "A loose plan matches items whose passwords or notes differ; "
            "review it instead of applying it."
        )
    ids = plan.drop_ids
    for start in range(0, len(ids), DELETE_BATCH_SIZE):
        client.soft_delete_ciphers(ids[start : start + DELETE_BATCH_SIZE])
    return len(ids)
