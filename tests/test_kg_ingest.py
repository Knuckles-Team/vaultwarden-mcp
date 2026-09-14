"""Native epistemic-graph ingestion — metadata only, never vault contents.

Exercises the real ingestion seam with the native primitive replaced by a recorder, and
asserts that encrypted or decrypted contents (names, usernames, passwords, notes, URIs,
folder and collection names) never appear in what is written to the graph.
"""

from __future__ import annotations

import json

import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError

from vaultwarden_mcp import kg_ingest

SECRET_MARKERS = (
    "Example Bank",
    "user@example.com",
    "hunter2",
    "otpauth://",
    "private note",
    "https://bank.example.com",
    "Personal",
    "Shared Logins",
)


@pytest.fixture
def recorded(monkeypatch):
    calls = []

    def fake_native(entities, relationships, **kwargs):
        calls.append({"entities": entities, "relationships": relationships, **kwargs})
        return {"nodes": len(entities), "edges": len(relationships or [])}

    monkeypatch.setattr(kg_ingest, "_native_ingest_entities", fake_native)
    return calls


def _login_item(**extra):
    item = {
        "id": "item-1",
        "type": 1,
        "name": "Example Bank",
        "notes": "private note",
        "folderId": "folder-1",
        "organizationId": "org-1",
        "collectionIds": ["col-1"],
        "revisionDate": "2026-01-02T03:04:05.000Z",
        "creationDate": "2025-01-02T03:04:05.000Z",
        "reprompt": 0,
        "attachments": [{"id": "att-1", "fileName": "statement.pdf"}],
        "login": {
            "username": "user@example.com",
            "password": "hunter2",
            "totp": "otpauth://totp/x",
            "uris": [{"uri": "https://bank.example.com"}],
            "fido2Credentials": [{"credentialId": "c"}],
        },
    }
    item.update(extra)
    return item


def test_items_map_to_typed_nodes_and_links(recorded):
    result = kg_ingest.ingest_items([_login_item()])
    assert result == {"nodes": 1, "edges": 3}
    (call,) = recorded
    (node,) = call["entities"]
    assert node["node_type"] == "VaultwardenLoginItem"
    assert node["vaultwardenAttachmentCount"] == 1
    assert node["vaultwardenHasPasskey"] is True
    assert {e["relationship"] for e in call["relationships"]} == {
        "vaultwardenInFolder",
        "vaultwardenInOrganization",
        "vaultwardenInCollection",
    }
    assert call["source"] == "vaultwarden-mcp"
    assert call["domain"] == "vaultwarden"


def test_no_vault_contents_reach_the_graph(recorded):
    kg_ingest.ingest_items([_login_item()])
    kg_ingest.ingest_collections(
        [{"id": "col-1", "organizationId": "org-1", "name": "Shared Logins"}]
    )
    kg_ingest.ingest_folders(["folder-1"])
    written = json.dumps(recorded)
    for marker in SECRET_MARKERS:
        assert marker not in written


def test_unknown_item_type_falls_back_to_base_class(recorded):
    kg_ingest.ingest_items([{"id": "x", "type": 99}])
    assert recorded[0]["entities"][0]["node_type"] == "VaultwardenItem"


def test_server_node_uses_versions_only(recorded):
    kg_ingest.ingest_server(
        {"version": "2026.6.0", "gitHash": "eb212e23", "environment": {"vault": "x"}},
        server_version="1.37.3",
    )
    (node,) = recorded[0]["entities"]
    assert node["vaultwardenServerVersion"] == "1.37.3"
    assert node["vaultwardenWebVaultVersion"] == "2026.6.0"
    assert "environment" not in node


@pytest.mark.parametrize(
    "call",
    [
        lambda: kg_ingest.ingest_items([]),
        lambda: kg_ingest.ingest_folders(None),
        lambda: kg_ingest.ingest_collections([]),
        lambda: kg_ingest.ingest_server({}),
    ],
)
def test_empty_input_is_rejected(recorded, call):
    with pytest.raises(NativeIngestError):
        call()
