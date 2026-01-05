import os
import pytest
from fastapi import HTTPException

from app import auth


def test_has_role_true_false():
    payload = {"sub": "alice", "roles": ["user", "editor"]}
    assert auth.has_role(payload, "user") is True
    assert auth.has_role(payload, "admin") is False


def test_require_role_allows_when_has():
    payload = {"sub": "bob", "roles": ["admin"]}
    # should not raise
    auth.require_role(payload, "admin")


def test_require_role_denies_when_missing():
    payload = {"sub": "carol", "roles": ["user"]}
    with pytest.raises(HTTPException) as exc:
        auth.require_role(payload, "admin")
    assert exc.value.status_code == 403


def test_require_role_bypasses_when_disable_auth(monkeypatch):
    payload = {"sub": "dev", "roles": []}
    # Temporarily set DISABLE_AUTH to True
    monkeypatch.setattr(auth, "DISABLE_AUTH", True)
    # should not raise
    auth.require_role(payload, "admin")
    # restore handled by monkeypatch fixture
