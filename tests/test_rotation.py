import string
from unittest.mock import MagicMock

import pytest

from vaultwarden_mcp.vault.rotation import generate_password, rotate_item_password


@pytest.mark.concept("VW-ECO.mcp.maintenance-operations")
class TestGeneratePassword:
    def test_default_length(self):
        password = generate_password()
        assert len(password) == 24

    def test_length_clamped_low(self):
        assert len(generate_password(length=1)) == 12

    def test_length_clamped_high(self):
        assert len(generate_password(length=10_000)) == 128

    def test_contains_every_required_class(self):
        password = generate_password(length=40, use_symbols=True)
        assert any(c in string.ascii_lowercase for c in password)
        assert any(c in string.ascii_uppercase for c in password)
        assert any(c in string.digits for c in password)
        assert any(not c.isalnum() for c in password)

    def test_no_symbols_when_disabled(self):
        password = generate_password(length=40, use_symbols=False)
        assert all(c.isalnum() for c in password)
        assert any(c in string.ascii_lowercase for c in password)
        assert any(c in string.ascii_uppercase for c in password)
        assert any(c in string.digits for c in password)

    def test_passwords_are_not_identical(self):
        passwords = {generate_password() for _ in range(20)}
        assert len(passwords) > 1


@pytest.mark.concept("VW-ECO.mcp.maintenance-operations")
class TestRotateItemPassword:
    def _login_item(self, **overrides):
        item = {
            "id": "item-1",
            "type": 1,
            "name": "example",
            "login": {"username": "alice", "password": "old-password"},
            "passwordHistory": [],
        }
        item.update(overrides)
        return item

    def test_requires_login_item_type(self):
        crypto = MagicMock()
        crypto.get_item.return_value = self._login_item(type=2)
        with pytest.raises(ValueError, match="not a login item"):
            rotate_item_password(crypto, "item-1")

    def test_requires_existing_password(self):
        crypto = MagicMock()
        item = self._login_item()
        item["login"]["password"] = ""
        crypto.get_item.return_value = item
        with pytest.raises(ValueError, match="no password to rotate"):
            rotate_item_password(crypto, "item-1")

    def test_result_never_contains_a_password(self):
        crypto = MagicMock()
        crypto.get_item.return_value = self._login_item()
        result = rotate_item_password(crypto, "item-1")
        assert result == {
            "item_id": "item-1",
            "rotated": True,
            "revision_date": result["revision_date"],
        }
        assert "password" not in result
        assert all("password" not in str(v).lower() for v in result.values())

    def test_edit_item_receives_new_password_and_bounded_history(self):
        crypto = MagicMock()
        history = [{"lastUsedDate": f"t{i}", "password": f"p{i}"} for i in range(5)]
        crypto.get_item.return_value = self._login_item(passwordHistory=list(history))
        rotate_item_password(crypto, "item-1", length=16, use_symbols=False)

        assert crypto.edit_item.call_count == 1
        (item_id, edited_item), _ = crypto.edit_item.call_args
        assert item_id == "item-1"
        assert edited_item["login"]["password"] != "old-password"
        assert len(edited_item["login"]["password"]) == 16
        assert len(edited_item["passwordHistory"]) == 5
        assert edited_item["passwordHistory"][0]["password"] == "old-password"
        # Oldest entry (p4) was dropped to keep at most 5.
        assert all(
            entry["password"] != "p4" for entry in edited_item["passwordHistory"]
        )

    def test_revision_date_is_iso8601_z(self):
        crypto = MagicMock()
        crypto.get_item.return_value = self._login_item()
        result = rotate_item_password(crypto, "item-1")
        assert result["revision_date"].endswith("Z")
        assert "T" in result["revision_date"]
