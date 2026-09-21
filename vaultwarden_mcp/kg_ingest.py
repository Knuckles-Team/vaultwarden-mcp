"""Certified metadata projection for the Vaultwarden source connector.

The provider emits opaque identifiers, type codes, lifecycle dates, counts, and
relationships. It never emits item names, usernames, passwords, notes, URIs,
TOTP seeds, custom fields, attachment bodies, folder names, collection names,
send contents, or key material.

This module does not write to the knowledge graph. Agent Utilities source_sync
is the sole commit/checkpoint/reconcile authority and consumes the structural
projection through the vaultwarden-metadata MCP preset.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

_CONTRACT_VERSION = "vaultwarden.metadata-entities/v1"
_SYNC_MODES = frozenset({"delta", "full", "reconcile"})
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,127}$")

_ITEM_CLASSES = {
    1: "VaultwardenLoginItem",
    2: "VaultwardenSecureNoteItem",
    3: "VaultwardenCardItem",
    4: "VaultwardenIdentityItem",
    5: "VaultwardenSshKeyItem",
}
_ITEM_NODE_TYPES = frozenset({"VaultwardenItem", *_ITEM_CLASSES.values()})
_NODE_TYPES = frozenset(
    {
        *_ITEM_NODE_TYPES,
        "VaultwardenFolder",
        "VaultwardenOrganization",
        "VaultwardenCollection",
        "VaultwardenServer",
    }
)
_ENTITY_FIELDS = frozenset(
    {
        "id",
        "node_type",
        "externalToolId",
        "vaultwardenItemType",
        "vaultwardenRevisionDate",
        "vaultwardenCreationDate",
        "vaultwardenDeletedDate",
        "vaultwardenAttachmentCount",
        "vaultwardenReprompt",
        "vaultwardenHasPasskey",
        "vaultwardenWebVaultVersion",
        "vaultwardenServerVersion",
    }
)
_RELATIONSHIPS = frozenset(
    {
        "vaultwardenInFolder",
        "vaultwardenInOrganization",
        "vaultwardenInCollection",
        "vaultwardenCollectionOf",
    }
)


class MetadataProjectionError(ValueError):
    """A provider response violated the certified metadata-only contract."""


def _require_identifier(value: Any, *, field: str) -> str:
    """Accept an opaque provider identifier, never arbitrary user text."""
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise MetadataProjectionError(f"Vaultwarden metadata has an invalid {field}")
    rendered = str(value)
    if not _IDENTIFIER.fullmatch(rendered):
        raise MetadataProjectionError(f"Vaultwarden metadata has an invalid {field}")
    return rendered


def _require_timestamp(value: Any, *, field: str) -> datetime | None:
    """Validate an optional timezone-aware ISO-8601 lifecycle timestamp."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise MetadataProjectionError(f"Vaultwarden metadata has an invalid {field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MetadataProjectionError(
            f"Vaultwarden metadata has an invalid {field}"
        ) from exc
    if parsed.tzinfo is None:
        raise MetadataProjectionError(f"Vaultwarden metadata has an invalid {field}")
    return parsed.astimezone(UTC)


def _item_node(item: dict[str, Any]) -> dict[str, Any]:
    item_id = _require_identifier(item.get("id"), field="item id")
    item_type = item.get("type")
    if item_type is not None and (
        not isinstance(item_type, int) or isinstance(item_type, bool)
    ):
        raise MetadataProjectionError("Vaultwarden metadata has an invalid item type")
    attachments = item.get("attachments") or []
    if not isinstance(attachments, list):
        raise MetadataProjectionError(
            "Vaultwarden metadata has invalid attachments metadata"
        )
    login = item.get("login") or {}
    if not isinstance(login, dict):
        raise MetadataProjectionError("Vaultwarden metadata has invalid login metadata")
    credentials = login.get("fido2Credentials") or []
    if not isinstance(credentials, list):
        raise MetadataProjectionError(
            "Vaultwarden metadata has invalid passkey metadata"
        )

    node: dict[str, Any] = {
        "id": f"vaultwarden:item:{item_id}",
        "node_type": (
            _ITEM_CLASSES.get(item_type, "VaultwardenItem")
            if item_type is not None
            else "VaultwardenItem"
        ),
        "externalToolId": item_id,
        "vaultwardenItemType": item_type,
        "vaultwardenRevisionDate": item.get("revisionDate"),
        "vaultwardenCreationDate": item.get("creationDate"),
        "vaultwardenDeletedDate": item.get("deletedDate"),
        "vaultwardenAttachmentCount": len(attachments),
        "vaultwardenReprompt": bool(item.get("reprompt")),
    }
    if item_type == 1:
        node["vaultwardenHasPasskey"] = bool(credentials)
    return {key: value for key, value in node.items() if value is not None}


def _item_edges(item: dict[str, Any], node_id: str) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for field, kind, relationship in (
        ("folderId", "folder", "vaultwardenInFolder"),
        ("organizationId", "organization", "vaultwardenInOrganization"),
    ):
        if item.get(field):
            target = _require_identifier(item[field], field=field)
            edges.append(
                {
                    "source": node_id,
                    "target": f"vaultwarden:{kind}:{target}",
                    "relationship": relationship,
                }
            )
    collection_ids = item.get("collectionIds") or []
    if not isinstance(collection_ids, list):
        raise MetadataProjectionError("Vaultwarden metadata has invalid collection ids")
    for value in collection_ids:
        collection_id = _require_identifier(value, field="collection id")
        edges.append(
            {
                "source": node_id,
                "target": f"vaultwarden:collection:{collection_id}",
                "relationship": "vaultwardenInCollection",
            }
        )
    return edges


def _folder_nodes(
    folders: Sequence[dict[str, Any] | str], items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    values: list[Any] = [
        *(
            folder.get("id") if isinstance(folder, dict) else folder
            for folder in folders
        ),
        *(item.get("folderId") for item in items if item.get("folderId")),
    ]
    identifiers = sorted(
        {_require_identifier(value, field="folder id") for value in values if value}
    )
    return [
        {
            "id": f"vaultwarden:folder:{identifier}",
            "node_type": "VaultwardenFolder",
            "externalToolId": identifier,
        }
        for identifier in identifiers
    ]


def _collection_slice(
    collections: list[dict[str, Any]], items: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    declared: dict[str, dict[str, Any]] = {}
    for collection in collections:
        if not isinstance(collection, dict):
            raise MetadataProjectionError(
                "Vaultwarden metadata has an invalid collection"
            )
        identifier = _require_identifier(collection.get("id"), field="collection id")
        declared[identifier] = collection
    referenced = {
        _require_identifier(value, field="collection id")
        for item in items
        for value in (item.get("collectionIds") or [])
    }
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, str]] = []
    for identifier in sorted(set(declared) | referenced):
        node_id = f"vaultwarden:collection:{identifier}"
        entities.append(
            {
                "id": node_id,
                "node_type": "VaultwardenCollection",
                "externalToolId": identifier,
            }
        )
        organization = declared.get(identifier, {}).get("organizationId")
        if organization:
            organization_id = _require_identifier(organization, field="organization id")
            relationships.append(
                {
                    "source": node_id,
                    "target": f"vaultwarden:organization:{organization_id}",
                    "relationship": "vaultwardenCollectionOf",
                }
            )
    return entities, relationships


def _organization_nodes(
    items: list[dict[str, Any]], collections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    values = [
        *(item.get("organizationId") for item in items),
        *(collection.get("organizationId") for collection in collections),
    ]
    identifiers = sorted(
        {
            _require_identifier(value, field="organization id")
            for value in values
            if value
        }
    )
    return [
        {
            "id": f"vaultwarden:organization:{identifier}",
            "node_type": "VaultwardenOrganization",
            "externalToolId": identifier,
        }
        for identifier in identifiers
    ]


def _server_node(
    config: dict[str, Any] | None, server_version: str | None
) -> dict[str, Any] | None:
    if not config or not config.get("gitHash"):
        return None
    git_hash = _require_identifier(config["gitHash"], field="server git hash")
    node: dict[str, Any] = {
        "id": f"vaultwarden:server:{git_hash}",
        "node_type": "VaultwardenServer",
        "externalToolId": git_hash,
        "vaultwardenWebVaultVersion": config.get("version"),
        "vaultwardenServerVersion": server_version,
    }
    return {key: value for key, value in node.items() if value is not None}


def _validate_projection_slice(
    entities: list[dict[str, Any]], relationships: list[dict[str, str]]
) -> None:
    """Enforce the metadata allowlist and locally resolved edge contract."""
    node_ids: set[str] = set()
    for entity in entities:
        if not isinstance(entity, dict) or set(entity) - _ENTITY_FIELDS:
            raise MetadataProjectionError(
                "Vaultwarden metadata contains a forbidden field"
            )
        identifier = _require_identifier(entity.get("id"), field="entity id")
        if not identifier.startswith("vaultwarden:") or identifier in node_ids:
            raise MetadataProjectionError(
                "Vaultwarden metadata has an invalid entity id"
            )
        node_ids.add(identifier)
        node_type = _require_identifier(entity.get("node_type"), field="node type")
        if node_type not in _NODE_TYPES:
            raise MetadataProjectionError(
                "Vaultwarden metadata has an invalid node type"
            )
        _require_identifier(entity.get("externalToolId"), field="external id")
        item_type = entity.get("vaultwardenItemType")
        if item_type is not None and (
            not isinstance(item_type, int) or isinstance(item_type, bool)
        ):
            raise MetadataProjectionError(
                "Vaultwarden metadata has an invalid item type"
            )
        count = entity.get("vaultwardenAttachmentCount")
        if count is not None and (
            not isinstance(count, int) or isinstance(count, bool) or count < 0
        ):
            raise MetadataProjectionError(
                "Vaultwarden metadata has an invalid attachment count"
            )
        for field in ("vaultwardenReprompt", "vaultwardenHasPasskey"):
            if field in entity and not isinstance(entity[field], bool):
                raise MetadataProjectionError(
                    f"Vaultwarden metadata has an invalid {field}"
                )
        for field in (
            "vaultwardenRevisionDate",
            "vaultwardenCreationDate",
            "vaultwardenDeletedDate",
        ):
            _require_timestamp(entity.get(field), field=field)
        for field in ("vaultwardenWebVaultVersion", "vaultwardenServerVersion"):
            value = entity.get(field)
            if value is not None and (
                not isinstance(value, str) or not _VERSION.fullmatch(value)
            ):
                raise MetadataProjectionError(
                    f"Vaultwarden metadata has an invalid {field}"
                )

    for relationship in relationships:
        if not isinstance(relationship, dict) or set(relationship) != {
            "source",
            "target",
            "relationship",
        }:
            raise MetadataProjectionError(
                "Vaultwarden relationship has forbidden fields"
            )
        if (
            relationship.get("source") not in node_ids
            or relationship.get("target") not in node_ids
            or relationship.get("relationship") not in _RELATIONSHIPS
        ):
            raise MetadataProjectionError(
                "Vaultwarden relationship is not locally resolved"
            )


def _snapshot_checkpoint(
    entities: list[dict[str, Any]], checkpoint: str | None
) -> str | None:
    revisions: list[tuple[datetime, str]] = []
    for entity in entities:
        revision = entity.get("vaultwardenRevisionDate")
        parsed = _require_timestamp(revision, field="vaultwardenRevisionDate")
        if parsed is not None:
            assert isinstance(revision, str)
            revisions.append((parsed, revision))
    if checkpoint:
        parsed = _require_timestamp(checkpoint, field="checkpoint")
        if parsed is not None:
            revisions.append((parsed, checkpoint))
    return max(revisions)[1] if revisions else None


def _deduplicate_entities(
    entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse identical references and reject conflicting provider identities."""
    by_id: dict[str, dict[str, Any]] = {}
    for entity in entities:
        identifier = str(entity.get("id") or "")
        prior = by_id.get(identifier)
        if prior is not None and prior != entity:
            raise MetadataProjectionError(
                "Vaultwarden metadata contains a conflicting entity identity"
            )
        by_id[identifier] = entity
    return sorted(by_id.values(), key=lambda entity: entity["id"])


def _delta_slice(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, str]],
    checkpoint: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    checkpoint_time = _require_timestamp(checkpoint, field="checkpoint")
    assert checkpoint_time is not None
    included = {
        entity["id"]
        for entity in entities
        if entity["node_type"] in _ITEM_NODE_TYPES
        and (
            revision := _require_timestamp(
                entity.get("vaultwardenRevisionDate"), field="vaultwardenRevisionDate"
            )
        )
        is not None
        and revision > checkpoint_time
    }
    selected_relationships: list[dict[str, str]] = []
    changed = True
    while changed:
        changed = False
        for relationship in relationships:
            if (
                relationship["source"] in included
                and relationship not in selected_relationships
            ):
                selected_relationships.append(relationship)
                if relationship["target"] not in included:
                    included.add(relationship["target"])
                    changed = True
    selected_entities = [entity for entity in entities if entity["id"] in included]
    return selected_entities, selected_relationships


def build_metadata_snapshot(
    *,
    items: list[dict[str, Any]] | None = None,
    folders: list[dict[str, Any]] | list[str] | None = None,
    collections: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    server_version: str | None = None,
    mode: str = "delta",
    checkpoint: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic structural envelope consumed by source_sync."""
    if mode not in _SYNC_MODES:
        raise MetadataProjectionError("Vaultwarden metadata has an invalid sync mode")
    if checkpoint is not None:
        _require_timestamp(checkpoint, field="checkpoint")
    if items is not None and not isinstance(items, list):
        raise MetadataProjectionError("Vaultwarden metadata items are malformed")
    if folders is not None and not isinstance(folders, list):
        raise MetadataProjectionError("Vaultwarden metadata folders are malformed")
    if collections is not None and not isinstance(collections, list):
        raise MetadataProjectionError("Vaultwarden metadata collections are malformed")
    if config is not None and not isinstance(config, dict):
        raise MetadataProjectionError("Vaultwarden server metadata is malformed")

    all_items = list(items or [])
    all_collections = list(collections or [])
    item_entities: list[dict[str, Any]] = []
    item_relationships: list[dict[str, str]] = []
    for item in all_items:
        if not isinstance(item, dict):
            raise MetadataProjectionError("Vaultwarden metadata has an invalid item")
        node = _item_node(item)
        item_entities.append(node)
        item_relationships.extend(_item_edges(item, node["id"]))
    collection_entities, collection_relationships = _collection_slice(
        all_collections, all_items
    )
    entities = [
        *item_entities,
        *_folder_nodes(list(folders or []), all_items),
        *collection_entities,
        *_organization_nodes(all_items, all_collections),
    ]
    server = _server_node(config, server_version)
    if server is not None:
        entities.append(server)

    entities = _deduplicate_entities(entities)
    relationships = sorted(
        {
            (edge["source"], edge["relationship"], edge["target"]): edge
            for edge in [*item_relationships, *collection_relationships]
        }.values(),
        key=lambda edge: (edge["source"], edge["relationship"], edge["target"]),
    )
    _validate_projection_slice(entities, relationships)
    next_checkpoint = _snapshot_checkpoint(entities, checkpoint)
    live_ids = [entity["id"] for entity in entities]

    if mode == "delta" and checkpoint:
        entities, relationships = _delta_slice(entities, relationships, checkpoint)
        _validate_projection_slice(entities, relationships)

    material = json.dumps(
        {"entities": entities, "relationships": relationships},
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "contract": _CONTRACT_VERSION,
        "mode": mode,
        "entities": entities,
        "relationships": relationships,
        "checkpoint": next_checkpoint,
        "content_hash": hashlib.sha256(material.encode()).hexdigest(),
        "reconcile": {
            "authoritative": mode == "reconcile",
            "live_ids": live_ids if mode == "reconcile" else [],
        },
        "backfeed": {"supported": False, "mode": "read_only"},
    }


def refuse_backfeed() -> None:
    """Fail closed because Vaultwarden is a read-only graph source."""
    raise MetadataProjectionError(
        "Vaultwarden metadata backfeed is unsupported (read-only)"
    )
