"""Native epistemic-graph ingestion for Vaultwarden metadata.

Only identifiers, type codes, lifecycle dates, counts, and relationships are accepted.
Item names, usernames, passwords, notes, URIs, TOTP seeds, custom fields, attachments,
folder names, collection names, send contents, and every key are never read into the graph.

All writes use the required ``agent_utilities.knowledge_graph.memory.native_ingest``
primitive. Nodes use canonical ``node_type`` and edges use canonical ``relationship``;
nodes and edges commit in one native transaction. Missing engine dependencies, rejected
records, conflicts, and transaction failures propagate as ``NativeIngestError``.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    NativeIngestError,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)

_SOURCE = "vaultwarden-mcp"
_DOMAIN = "vaultwarden"

_ITEM_CLASSES = {
    1: "VaultwardenLoginItem",
    2: "VaultwardenSecureNoteItem",
    3: "VaultwardenCardItem",
    4: "VaultwardenIdentityItem",
    5: "VaultwardenSshKeyItem",
}


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships in one native transaction."""
    return _native_ingest_entities(
        entities,
        relationships,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


def _item_node(item: dict[str, Any]) -> dict[str, Any] | None:
    item_id = item.get("id")
    if not item_id:
        return None
    item_type = item.get("type")
    login = item.get("login") or {}
    node: dict[str, Any] = {
        "id": f"vaultwarden:item:{item_id}",
        "node_type": (
            _ITEM_CLASSES.get(item_type, "VaultwardenItem")
            if isinstance(item_type, int)
            else "VaultwardenItem"
        ),
        "externalToolId": str(item_id),
        "vaultwardenItemType": item_type,
        "vaultwardenRevisionDate": item.get("revisionDate"),
        "vaultwardenCreationDate": item.get("creationDate"),
        "vaultwardenDeletedDate": item.get("deletedDate"),
        "vaultwardenAttachmentCount": len(item.get("attachments") or []),
        "vaultwardenReprompt": bool(item.get("reprompt")),
    }
    if item_type == 1:
        node["vaultwardenHasPasskey"] = bool(login.get("fido2Credentials"))
    return {k: v for k, v in node.items() if v is not None}


def _item_edges(item: dict[str, Any], node_id: str) -> list[dict[str, Any]]:
    edges = []
    if item.get("folderId"):
        edges.append(
            {
                "source": node_id,
                "target": f"vaultwarden:folder:{item['folderId']}",
                "relationship": "vaultwardenInFolder",
            }
        )
    if item.get("organizationId"):
        edges.append(
            {
                "source": node_id,
                "target": f"vaultwarden:organization:{item['organizationId']}",
                "relationship": "vaultwardenInOrganization",
            }
        )
    for collection_id in item.get("collectionIds") or []:
        edges.append(
            {
                "source": node_id,
                "target": f"vaultwarden:collection:{collection_id}",
                "relationship": "vaultwardenInCollection",
            }
        )
    return edges


def ingest_items(
    items: list[dict[str, Any]] | None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map vault items -> typed item nodes plus folder/organization/collection links.

    Accepts decrypted records or raw API ciphers; either way only whitelisted metadata is
    copied, so encrypted or decrypted contents never reach the graph.
    """
    if not items:
        raise NativeIngestError("Vaultwarden item ingestion requires item metadata")
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    for item in items:
        node = _item_node(item)
        if node is None:
            continue
        entities.append(node)
        relationships.extend(_item_edges(item, node["id"]))
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_folders(
    folder_ids: list[str] | None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map folder identifiers -> ``:VaultwardenFolder`` nodes (names are never ingested)."""
    if not folder_ids:
        raise NativeIngestError("Vaultwarden folder ingestion requires folder ids")
    entities = [
        {
            "id": f"vaultwarden:folder:{folder_id}",
            "node_type": "VaultwardenFolder",
            "externalToolId": str(folder_id),
        }
        for folder_id in folder_ids
        if folder_id
    ]
    return ingest_entities(entities, None, client=client, graph=graph)


def ingest_collections(
    collections: list[dict[str, Any]] | None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map collections -> ``:VaultwardenCollection`` nodes linked to their organization."""
    if not collections:
        raise NativeIngestError("Vaultwarden collection ingestion requires collections")
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    for collection in collections:
        collection_id = collection.get("id")
        if not collection_id:
            continue
        node_id = f"vaultwarden:collection:{collection_id}"
        entities.append(
            {
                "id": node_id,
                "node_type": "VaultwardenCollection",
                "externalToolId": str(collection_id),
            }
        )
        if collection.get("organizationId"):
            relationships.append(
                {
                    "source": node_id,
                    "target": f"vaultwarden:organization:{collection['organizationId']}",
                    "relationship": "vaultwardenCollectionOf",
                }
            )
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_server(
    config: dict[str, Any] | None,
    *,
    server_version: str | None = None,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map ``/api/config`` (+ ``/api/version``) -> one ``:VaultwardenServer`` node."""
    if not config:
        raise NativeIngestError("Vaultwarden server ingestion requires /api/config")
    git_hash = config.get("gitHash") or "unknown"
    node: dict[str, Any] = {
        "id": f"vaultwarden:server:{git_hash}",
        "node_type": "VaultwardenServer",
        "externalToolId": str(git_hash),
        "vaultwardenWebVaultVersion": config.get("version"),
        "vaultwardenServerVersion": server_version,
    }
    node = {k: v for k, v in node.items() if v is not None}
    return ingest_entities([node], None, client=client, graph=graph)
