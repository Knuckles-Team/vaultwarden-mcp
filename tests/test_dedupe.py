import pytest

from vaultwarden_mcp.vault.dedupe import (
    DELETE_BATCH_SIZE,
    apply_plan,
    fingerprint,
    normalize_uri,
    plan_deduplication,
)


def _login(item_id, *, revision="2025-10-09T02:50:59.000Z", password="pw", **extra):
    item = {
        "id": item_id,
        "type": 1,
        "name": "Example",
        "notes": None,
        "revisionDate": revision,
        "login": {
            "username": "user@example.com",
            "password": password,
            "uris": [{"uri": "https://www.example.com/login/"}],
        },
    }
    item.update(extra)
    return item


class RecordingClient:
    def __init__(self):
        self.calls = []

    def soft_delete_ciphers(self, ids):
        self.calls.append(list(ids))


def test_normalize_uri_ignores_scheme_www_and_trailing_slash():
    assert normalize_uri("https://www.Example.com/login/") == "example.com/login"
    assert normalize_uri("example.com/login") == "example.com/login"
    assert normalize_uri(None) == ""


def test_exact_fingerprint_distinguishes_passwords_but_loose_does_not():
    a, b = _login("a"), _login("b", password="other")
    assert fingerprint(a) != fingerprint(b)
    assert fingerprint(a, loose=True) == fingerprint(b, loose=True)


def test_plan_keeps_the_most_recently_edited_copy():
    items = [
        _login("old", revision="2025-01-01T00:00:00.000Z", passwordHistory=[{}, {}]),
        _login("new", revision="2025-06-01T00:00:00.000Z"),
        _login("mid", revision="2025-03-01T00:00:00.000Z"),
    ]
    plan = plan_deduplication(items)
    assert len(plan.groups) == 1
    assert plan.groups[0].keep_id == "new"
    assert set(plan.groups[0].drop_ids) == {"old", "mid"}


def test_ties_prefer_the_copy_with_more_history():
    same = "2025-01-01T00:00:00.000Z"
    items = [
        _login("bare", revision=same),
        _login("rich", revision=same, passwordHistory=[{}]),
    ]
    assert plan_deduplication(items).groups[0].keep_id == "rich"


def test_trashed_and_org_items_are_excluded_by_default():
    items = [
        _login("a"),
        _login("b", deletedDate="2026-01-01T00:00:00.000Z"),
        _login("c", organizationId="org-1"),
    ]
    assert plan_deduplication(items).groups == ()
    org_plan = plan_deduplication(
        [_login("c", organizationId="org-1"), _login("d", organizationId="org-1")],
        include_org=True,
    )
    assert len(org_plan.groups) == 1


def test_summary_contains_identifiers_only():
    summary = plan_deduplication([_login("a"), _login("b")]).summary()
    assert "Example" not in str(summary)
    assert "pw" not in str(summary)
    assert summary["extra_copies"] == 1


def test_apply_batches_soft_deletes():
    items = [
        _login(f"id-{n}", revision=f"2025-01-01T00:00:{n % 60:02d}.{n:03d}Z")
        for n in range(DELETE_BATCH_SIZE + 2)
    ]
    client = RecordingClient()
    trashed = apply_plan(client, plan_deduplication(items))
    assert trashed == DELETE_BATCH_SIZE + 1
    assert [len(c) for c in client.calls] == [DELETE_BATCH_SIZE, 1]


def test_apply_refuses_a_loose_plan():
    plan = plan_deduplication([_login("a"), _login("b", password="x")], loose=True)
    with pytest.raises(ValueError):
        apply_plan(RecordingClient(), plan)
