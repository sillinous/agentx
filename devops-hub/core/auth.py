"""
Authentication module for DevOps Hub.

Provides API key-based authentication with scopes.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery

from .database import get_database


# API key can be passed in header or query parameter
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)


@dataclass
class APIKey:
    """Represents an API key."""
    id: str
    name: str
    key_hash: str
    scopes: List[str] = field(default_factory=lambda: ["read"])
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def has_scope(self, scope: str) -> bool:
        """Check if the key has a specific scope."""
        if "admin" in self.scopes:
            return True
        if scope in self.scopes:
            return True
        # Check wildcard scopes
        for s in self.scopes:
            if s.endswith("*") and scope.startswith(s[:-1]):
                return True
        return False

    def is_expired(self) -> bool:
        """Check if the key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if the key is valid."""
        return self.is_active and not self.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without key_hash for security)."""
        return {
            "id": self.id,
            "name": self.name,
            "scopes": self.scopes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class APIKeyManager:
    """
    Manages API keys.

    Scopes:
    - read: Read access to agents, workflows, events
    - write: Create/update agents, workflows
    - execute: Execute agents and workflows
    - admin: Full access including key management
    """

    VALID_SCOPES = {"read", "write", "execute", "admin"}

    def __init__(self):
        self.db = get_database()

    def _hash_key(self, key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(key.encode()).hexdigest()

    def create_key(
        self,
        name: str,
        scopes: List[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple[str, APIKey]:
        """
        Create a new API key.

        Returns:
            Tuple of (raw_key, APIKey object)
            The raw key is only returned once and should be stored securely.
        """
        # Validate scopes
        scopes = scopes or ["read"]
        for scope in scopes:
            base_scope = scope.rstrip("*")
            if base_scope and base_scope not in self.VALID_SCOPES:
                raise ValueError(f"Invalid scope: {scope}")

        # Generate key
        raw_key = f"dh_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)

        # Calculate expiry
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        now = datetime.utcnow()
        key = APIKey(
            id=str(uuid4()),
            name=name,
            key_hash=key_hash,
            scopes=scopes,
            is_active=True,
            created_at=now,
            expires_at=expires_at,
        )

        # Store in database
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO api_keys (id, key_hash, name, scopes, is_active, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                key.id,
                key.key_hash,
                key.name,
                ",".join(key.scopes),
                1 if key.is_active else 0,
                key.created_at.isoformat(),
                key.expires_at.isoformat() if key.expires_at else None,
            ))

        return raw_key, key

    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        """
        Validate an API key.

        Returns the APIKey if valid, None otherwise.
        Also updates last_used_at.
        """
        if not raw_key:
            return None

        key_hash = self._hash_key(raw_key)

        row = self.db.fetch_one(
            "SELECT * FROM api_keys WHERE key_hash = ?",
            (key_hash,)
        )

        if not row:
            return None

        key = APIKey(
            id=row["id"],
            name=row["name"],
            key_hash=row["key_hash"],
            scopes=row["scopes"].split(",") if row["scopes"] else ["read"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            last_used_at=datetime.fromisoformat(row["last_used_at"]) if row["last_used_at"] else None,
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        )

        if not key.is_valid():
            return None

        # Update last_used_at
        now = datetime.utcnow()
        with self.db.cursor() as cur:
            cur.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (now.isoformat(), key.id)
            )
        key.last_used_at = now

        return key

    def list_keys(self) -> List[APIKey]:
        """List all API keys (without hashes)."""
        rows = self.db.fetch_all("SELECT * FROM api_keys ORDER BY created_at DESC")
        return [
            APIKey(
                id=row["id"],
                name=row["name"],
                key_hash="[hidden]",
                scopes=row["scopes"].split(",") if row["scopes"] else ["read"],
                is_active=bool(row["is_active"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                last_used_at=datetime.fromisoformat(row["last_used_at"]) if row["last_used_at"] else None,
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            )
            for row in rows
        ]

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        with self.db.cursor() as cur:
            cur.execute(
                "UPDATE api_keys SET is_active = 0 WHERE id = ?",
                (key_id,)
            )
            return cur.rowcount > 0

    def delete_key(self, key_id: str) -> bool:
        """Delete an API key."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
            return cur.rowcount > 0


# Global manager instance
_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the API key manager."""
    global _manager
    if _manager is None:
        _manager = APIKeyManager()
    return _manager


# FastAPI dependencies

class AuthConfig:
    """Authentication configuration."""
    enabled: bool = True
    allow_anonymous_read: bool = True  # Allow read without API key


_auth_config = AuthConfig()


def configure_auth(enabled: bool = True, allow_anonymous_read: bool = True):
    """Configure authentication settings."""
    _auth_config.enabled = enabled
    _auth_config.allow_anonymous_read = allow_anonymous_read


async def get_api_key(
    header_key: str = Security(API_KEY_HEADER),
    query_key: str = Security(API_KEY_QUERY),
) -> Optional[APIKey]:
    """
    Get and validate API key from request.

    Checks both header (X-API-Key) and query parameter (api_key).
    """
    if not _auth_config.enabled:
        return None

    raw_key = header_key or query_key

    if not raw_key:
        if _auth_config.allow_anonymous_read:
            return None
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    manager = get_api_key_manager()
    key = manager.validate_key(raw_key)

    if not key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key


def require_scope(scope: str):
    """
    Dependency that requires a specific scope.

    Usage:
        @app.get("/admin/keys")
        async def list_keys(key: APIKey = Depends(require_scope("admin"))):
            ...
    """
    async def check_scope(
        key: Optional[APIKey] = Depends(get_api_key),
    ) -> APIKey:
        if not _auth_config.enabled:
            # Return a dummy admin key when auth is disabled
            return APIKey(id="system", name="system", key_hash="", scopes=["admin"])

        if key is None:
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if not key.has_scope(scope):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required scope: {scope}",
            )

        return key

    return check_scope


def require_read():
    """Require read scope."""
    return require_scope("read")


def require_write():
    """Require write scope."""
    return require_scope("write")


def require_execute():
    """Require execute scope."""
    return require_scope("execute")


def require_admin():
    """Require admin scope."""
    return require_scope("admin")
