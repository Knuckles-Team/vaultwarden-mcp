"""Certified Vaultwarden metadata-projection contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from vaultwarden_mcp import kg_ingest
from vaultwarden_mcp.kg_ingest import MetadataProjectionError

_SECRET_MARKERS = (
    "Personal",
    "Shared Logins",
    "alice@example.invalid",
    "correct horse battery staple",
    "https://private.example.invalid",
    "otpauth://",
    "private note",
    "attachment contents",
    "admin-secret",
)


def _login_item(**overrides):
    item = {
        "id": "item-1",
        "type": 1,
        "name": "Personal",
        "notes": "private note",
        "revisionDate": "2026-01-03T03:04:05.000Z",
        "creationDate": "2026-01-01T03:04:05.000Z",
        "deletedDate": None,
        "reprompt": 1,
        "folderId": "folder-1",
        "organizationId": "org-1",
        "collectionIds": ["collection-1"],
        "attachments": [{"id": "attachment-1", "data": "attachment contents"}],
        "login": {
            "username": "alice@example.invalid",
            "password": "correct horse battery staple",
            "totp": "otpauth://private",
            "uris": [{"uri": "https://private.example.invalid"}],
            "fido2Credentials": [{"credentialId": "private-passkey"}],
        },
    }
    item.update(overrides)
    return item


def _snapshot(**overrides):
    arguments = {
        "items": [_login_item()],
        "folders": [{"id": "folder-1", "name": "Personal"}],
        "collections": [
            {
                "id": "collection-1",
                "organizationId": "org-1",
                "name": "Shared Logins",
            }
        ],
        "config": {
            "gitHash": "eb212e23",
            "version": "2026.6.0",
            "environment": {"adminToken": "admin-secret"},
        },
        "server_version": "1.37.3",
        "mode": "full",
    }
    arguments.update(overrides)
    return kg_ingest.build_metadata_snapshot(**arguments)


def test_snapshot_is_deterministic_metadata_only_and_digest_bound():
    first = _snapshot()
    replay = _snapshot()

    assert first == replay
    assert first["contract"] == "vaultwarden.metadata-entities/v1"
    assert first["mode"] == "full"
    assert first["backfeed"] == {"supported": False, "mode": "read_only"}
    material = json.dumps(
        {
            "entities": first["entities"],
            "relationships": first["relationships"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first["content_hash"] == hashlib.sha256(material.encode()).hexdigest()
    rendered = json.dumps(first)
    assert all(marker not in rendered for marker in _SECRET_MARKERS)
    assert {entity["node_type"] for entity in first["entities"]} == {
        "VaultwardenLoginItem",
        "VaultwardenFolder",
        "VaultwardenOrganization",
        "VaultwardenCollection",
        "VaultwardenServer",
    }


def test_every_relationship_endpoint_is_materialized():
    snapshot = _snapshot(folders=[], collections=[])
    node_ids = {entity["id"] for entity in snapshot["entities"]}

    assert {
        "vaultwarden:folder:folder-1",
        "vaultwarden:organization:org-1",
        "vaultwarden:collection:collection-1",
    } <= node_ids
    assert all(
        edge["source"] in node_ids and edge["target"] in node_ids
        for edge in snapshot["relationships"]
    )


def test_delta_includes_only_changed_items_and_their_structural_closure():
    checkpoint = "2026-01-02T03:04:05.000Z"
    snapshot = _snapshot(
        items=[
            _login_item(id="old", revisionDate=checkpoint),
            _login_item(
                id="new",
                revisionDate="2026-01-04T03:04:05.000Z",
                collectionIds=["collection-1"],
            ),
        ],
        mode="delta",
        checkpoint=checkpoint,
    )
    node_ids = {entity["id"] for entity in snapshot["entities"]}

    assert "vaultwarden:item:old" not in node_ids
    assert "vaultwarden:item:new" in node_ids
    assert {
        "vaultwarden:folder:folder-1",
        "vaultwarden:organization:org-1",
        "vaultwarden:collection:collection-1",
    } <= node_ids
    assert all(
        edge["source"] in node_ids and edge["target"] in node_ids
        for edge in snapshot["relationships"]
    )
    assert snapshot["checkpoint"] == "2026-01-04T03:04:05.000Z"
    assert snapshot["reconcile"] == {"authoritative": False, "live_ids": []}


def test_empty_delta_is_a_safe_structural_noop():
    checkpoint = "2026-01-04T03:04:05.000Z"
    snapshot = _snapshot(mode="delta", checkpoint=checkpoint)

    assert snapshot["entities"] == []
    assert snapshot["relationships"] == []
    assert snapshot["checkpoint"] == checkpoint
    assert (
        snapshot["content_hash"]
        == hashlib.sha256(b'{"entities":[],"relationships":[]}').hexdigest()
    )


def test_reconcile_live_ids_are_complete_and_authoritative():
    snapshot = _snapshot(mode="reconcile")

    assert snapshot["reconcile"] == {
        "authoritative": True,
        "live_ids": sorted(entity["id"] for entity in snapshot["entities"]),
    }


@pytest.mark.parametrize(
    ("overrides", "error"),
    (
        ({"id": "not allowed whitespace"}, "item id"),
        ({"type": "login"}, "item type"),
        ({"revisionDate": "not-a-timestamp"}, "vaultwardenRevisionDate"),
        ({"attachments": "not-a-list"}, "attachments metadata"),
        ({"collectionIds": "not-a-list"}, "collection ids"),
    ),
)
def test_malformed_provider_metadata_fails_closed(overrides, error):
    with pytest.raises(MetadataProjectionError, match=error):
        _snapshot(items=[_login_item(**overrides)])


def test_invalid_server_identity_or_version_fails_closed():
    with pytest.raises(MetadataProjectionError, match="server git hash"):
        _snapshot(config={"gitHash": "bad hash"})
    with pytest.raises(MetadataProjectionError, match="vaultwardenServerVersion"):
        _snapshot(server_version="not a version with spaces")


def test_conflicting_duplicate_provider_identity_fails_closed():
    with pytest.raises(MetadataProjectionError, match="conflicting entity identity"):
        _snapshot(
            items=[
                _login_item(id="same", revisionDate="2026-01-03T00:00:00Z"),
                _login_item(id="same", revisionDate="2026-01-04T00:00:00Z"),
            ]
        )


def test_old_direct_write_authority_is_removed():
    for name in (
        "ingest_entities",
        "ingest_items",
        "ingest_folders",
        "ingest_collections",
        "ingest_server",
        "queue_metadata_ingestion",
    ):
        assert not hasattr(kg_ingest, name)


def test_certified_preset_is_the_only_source_authority():
    presets_path = (
        Path(kg_ingest.__file__).parent / "connectors" / "mcp_source_presets.json"
    )
    presets = json.loads(presets_path.read_text(encoding="utf-8"))

    assert {name for name in presets if not name.startswith("_")} == {
        "vaultwarden-metadata"
    }
    assert presets["vaultwarden-metadata"] == {
        "server": "vaultwarden-mcp",
        "tool": "vaultwarden_metadata",
        "action": "metadata_snapshot",
        "params_style": "json",
        "params": {"mode": "delta"},
        "record_mode": "typed_entities",
        "records_path": "entities",
        "relationships_path": "relationships",
        "id_field": "id",
        "node_type_field": "node_type",
        "updated_field": "vaultwardenRevisionDate",
        "updated_since_param": "checkpoint",
        "checkpoint_path": "checkpoint",
        "reconcile_path": "reconcile.live_ids",
        "authoritative_path": "reconcile.authoritative",
        "strict_schema": True,
        "content_fields": [],
        "metadata_fields": [
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
        ],
        "text_field": "__metadata_entity_has_no_document_text__",
        "doc_type": "vaultwarden_metadata",
        "read_only": True,
        "backfeed_supported": False,
    }


def test_backfeed_and_unknown_modes_fail_closed():
    with pytest.raises(MetadataProjectionError, match=r"unsupported.*read-only"):
        kg_ingest.refuse_backfeed()
    with pytest.raises(MetadataProjectionError, match="invalid sync mode"):
        _snapshot(mode="unsupported")
