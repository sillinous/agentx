"""
Tests for the authentication module.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from core.database import Database, DatabaseConfig
from core.auth import APIKey, APIKeyManager


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    config = DatabaseConfig(path=db_path)
    db = Database(config)
    yield db
    db.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def manager(temp_db, monkeypatch):
    """Create an API key manager with temp database."""
    # Patch the get_database function to return our temp db
    import core.auth
    monkeypatch.setattr(core.auth, "get_database", lambda: temp_db)
    return APIKeyManager()


class TestAPIKey:
    """Tests for APIKey dataclass."""

    def test_has_scope_exact_match(self):
        key = APIKey(id="1", name="test", key_hash="h", scopes=["read", "write"])
        assert key.has_scope("read") is True
        assert key.has_scope("write") is True
        assert key.has_scope("admin") is False

    def test_has_scope_admin(self):
        key = APIKey(id="1", name="test", key_hash="h", scopes=["admin"])
        assert key.has_scope("read") is True
        assert key.has_scope("write") is True
        assert key.has_scope("execute") is True
        assert key.has_scope("admin") is True

    def test_has_scope_wildcard(self):
        key = APIKey(id="1", name="test", key_hash="h", scopes=["read*"])
        assert key.has_scope("read") is True
        assert key.has_scope("read_all") is True
        assert key.has_scope("write") is False

    def test_is_expired_no_expiry(self):
        key = APIKey(id="1", name="test", key_hash="h", expires_at=None)
        assert key.is_expired() is False

    def test_is_expired_future(self):
        future = datetime.utcnow() + timedelta(days=30)
        key = APIKey(id="1", name="test", key_hash="h", expires_at=future)
        assert key.is_expired() is False

    def test_is_expired_past(self):
        past = datetime.utcnow() - timedelta(days=1)
        key = APIKey(id="1", name="test", key_hash="h", expires_at=past)
        assert key.is_expired() is True

    def test_is_valid(self):
        key = APIKey(id="1", name="test", key_hash="h", is_active=True)
        assert key.is_valid() is True

        key.is_active = False
        assert key.is_valid() is False

    def test_to_dict(self):
        key = APIKey(
            id="1",
            name="test",
            key_hash="h",
            scopes=["read"],
            is_active=True,
        )
        d = key.to_dict()
        assert "id" in d
        assert "name" in d
        assert "scopes" in d
        assert "key_hash" not in d  # Should not expose hash


class TestAPIKeyManager:
    """Tests for APIKeyManager."""

    def test_create_key(self, manager):
        raw_key, key = manager.create_key(
            name="Test Key",
            scopes=["read", "write"],
        )

        assert raw_key.startswith("dh_")
        assert len(raw_key) > 20
        assert key.name == "Test Key"
        assert "read" in key.scopes
        assert "write" in key.scopes

    def test_create_key_with_expiry(self, manager):
        raw_key, key = manager.create_key(
            name="Expiring Key",
            expires_in_days=30,
        )

        assert key.expires_at is not None
        assert key.expires_at > datetime.utcnow()

    def test_create_key_invalid_scope(self, manager):
        with pytest.raises(ValueError):
            manager.create_key(name="Bad Key", scopes=["invalid_scope"])

    def test_validate_key_success(self, manager):
        raw_key, _ = manager.create_key(name="Valid Key")

        validated = manager.validate_key(raw_key)
        assert validated is not None
        assert validated.name == "Valid Key"
        assert validated.last_used_at is not None

    def test_validate_key_invalid(self, manager):
        validated = manager.validate_key("dh_invalid_key_12345")
        assert validated is None

    def test_validate_key_empty(self, manager):
        assert manager.validate_key("") is None
        assert manager.validate_key(None) is None

    def test_validate_key_expired(self, manager):
        # Create a key that's already expired
        raw_key, key = manager.create_key(
            name="Expired Key",
            expires_in_days=0,  # Expires today
        )

        # Manually set it to expired in the past
        manager.db.execute(
            "UPDATE api_keys SET expires_at = ? WHERE id = ?",
            ((datetime.utcnow() - timedelta(days=1)).isoformat(), key.id)
        )

        validated = manager.validate_key(raw_key)
        assert validated is None

    def test_list_keys(self, manager):
        manager.create_key(name="Key 1")
        manager.create_key(name="Key 2")

        keys = manager.list_keys()
        assert len(keys) == 2
        # Keys should have hidden hash
        for key in keys:
            assert key.key_hash == "[hidden]"

    def test_revoke_key(self, manager):
        raw_key, key = manager.create_key(name="To Revoke")

        # Key should work initially
        assert manager.validate_key(raw_key) is not None

        # Revoke
        result = manager.revoke_key(key.id)
        assert result is True

        # Key should no longer work
        assert manager.validate_key(raw_key) is None

    def test_revoke_nonexistent(self, manager):
        result = manager.revoke_key("nonexistent-id")
        assert result is False

    def test_delete_key(self, manager):
        _, key = manager.create_key(name="To Delete")

        assert len(manager.list_keys()) == 1

        result = manager.delete_key(key.id)
        assert result is True

        assert len(manager.list_keys()) == 0

    def test_multiple_keys_independent(self, manager):
        raw1, _ = manager.create_key(name="Key 1", scopes=["read"])
        raw2, _ = manager.create_key(name="Key 2", scopes=["admin"])

        key1 = manager.validate_key(raw1)
        key2 = manager.validate_key(raw2)

        assert key1.has_scope("admin") is False
        assert key2.has_scope("admin") is True
