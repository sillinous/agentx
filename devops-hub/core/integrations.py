"""
Integration and Credential Management for DevOps Hub.

Provides secure storage and management for:
- External API credentials
- Notification channel configurations (Slack, Email, Teams, Discord)
- Webhook endpoints
- User-specific integration settings
"""

import json
import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from .database import get_database, Database

logger = logging.getLogger(__name__)


class IntegrationType(str, Enum):
    """Types of integrations supported."""
    SLACK = "slack"
    EMAIL = "email"
    TEAMS = "teams"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    API_ENDPOINT = "api_endpoint"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class CredentialType(str, Enum):
    """Types of credentials."""
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    WEBHOOK_URL = "webhook_url"
    SMTP_CONFIG = "smtp_config"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"


@dataclass
class Integration:
    """An external integration configuration."""
    id: str
    name: str
    type: IntegrationType
    config: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str
    api_key_id: Optional[str] = None  # Owner's API key
    last_used_at: Optional[str] = None
    last_error: Optional[str] = None


def _init_integration_schema(db: Database):
    """Initialize integration tables."""
    with db.cursor() as cur:
        # User integrations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id TEXT PRIMARY KEY,
                api_key_id TEXT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                config TEXT NOT NULL DEFAULT '{}',
                is_active INTEGER NOT NULL DEFAULT 1,
                last_used_at TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Encrypted credentials vault
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id TEXT PRIMARY KEY,
                integration_id TEXT NOT NULL,
                credential_type TEXT NOT NULL,
                encrypted_value TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE
            )
        """)

        # User settings/preferences table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                api_key_id TEXT PRIMARY KEY,
                settings TEXT NOT NULL DEFAULT '{}',
                notification_preferences TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_integrations_api_key
            ON integrations(api_key_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_integrations_type
            ON integrations(type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_credentials_integration
            ON credentials(integration_id)
        """)


class IntegrationRepository:
    """Repository for managing integrations."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_database()
        _init_integration_schema(self.db)

    def create(
        self,
        name: str,
        integration_type: IntegrationType,
        config: Dict[str, Any],
        api_key_id: Optional[str] = None,
    ) -> Integration:
        """Create a new integration."""
        now = datetime.utcnow().isoformat()
        integration_id = f"int_{secrets.token_hex(8)}"

        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO integrations
                (id, api_key_id, name, type, config, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                integration_id,
                api_key_id,
                name,
                integration_type.value,
                json.dumps(config),
                now,
                now,
            ))

        logger.info(f"Created integration: {name} ({integration_type.value})")
        return self.get(integration_id)

    def get(self, integration_id: str) -> Optional[Integration]:
        """Get an integration by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM integrations WHERE id = ?",
            (integration_id,)
        )
        return self._row_to_integration(row) if row else None

    def list_by_owner(self, api_key_id: str) -> List[Integration]:
        """List integrations owned by an API key."""
        rows = self.db.fetch_all(
            "SELECT * FROM integrations WHERE api_key_id = ? ORDER BY name",
            (api_key_id,)
        )
        return [self._row_to_integration(row) for row in rows]

    def list_by_type(self, integration_type: IntegrationType) -> List[Integration]:
        """List integrations of a specific type."""
        rows = self.db.fetch_all(
            "SELECT * FROM integrations WHERE type = ? AND is_active = 1 ORDER BY name",
            (integration_type.value,)
        )
        return [self._row_to_integration(row) for row in rows]

    def list_all_active(self) -> List[Integration]:
        """List all active integrations."""
        rows = self.db.fetch_all(
            "SELECT * FROM integrations WHERE is_active = 1 ORDER BY type, name"
        )
        return [self._row_to_integration(row) for row in rows]

    def update(
        self,
        integration_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Integration]:
        """Update an integration."""
        now = datetime.utcnow().isoformat()
        existing = self.get(integration_id)
        if not existing:
            return None

        with self.db.cursor() as cur:
            cur.execute("""
                UPDATE integrations SET
                    name = COALESCE(?, name),
                    config = COALESCE(?, config),
                    is_active = COALESCE(?, is_active),
                    updated_at = ?
                WHERE id = ?
            """, (
                name,
                json.dumps(config) if config else None,
                1 if is_active else (0 if is_active is False else None),
                now,
                integration_id,
            ))

        return self.get(integration_id)

    def update_last_used(self, integration_id: str, error: Optional[str] = None):
        """Update last used timestamp and optionally set error."""
        now = datetime.utcnow().isoformat()
        with self.db.cursor() as cur:
            cur.execute("""
                UPDATE integrations SET
                    last_used_at = ?,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
            """, (now, error, now, integration_id))

    def delete(self, integration_id: str) -> bool:
        """Delete an integration and its credentials."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM credentials WHERE integration_id = ?", (integration_id,))
            cur.execute("DELETE FROM integrations WHERE id = ?", (integration_id,))
            return cur.rowcount > 0

    def _row_to_integration(self, row: Dict[str, Any]) -> Integration:
        """Convert database row to Integration object."""
        return Integration(
            id=row["id"],
            name=row["name"],
            type=IntegrationType(row["type"]),
            config=json.loads(row["config"]),
            is_active=bool(row["is_active"]),
            api_key_id=row["api_key_id"],
            last_used_at=row["last_used_at"],
            last_error=row["last_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class CredentialRepository:
    """Repository for managing encrypted credentials."""

    def __init__(self, db: Optional[Database] = None, encryption_key: Optional[str] = None):
        self.db = db or get_database()
        # In production, use proper encryption (Fernet, etc.)
        # For now, using simple obfuscation - MUST be replaced with real encryption
        self._key = encryption_key or "devops-hub-default-key"
        _init_integration_schema(self.db)

    def _encrypt(self, value: str) -> str:
        """Encrypt a credential value. TODO: Use proper encryption."""
        # Simple XOR obfuscation - REPLACE with Fernet in production
        key_bytes = self._key.encode()
        value_bytes = value.encode()
        encrypted = bytes(v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(value_bytes))
        return encrypted.hex()

    def _decrypt(self, encrypted: str) -> str:
        """Decrypt a credential value. TODO: Use proper decryption."""
        key_bytes = self._key.encode()
        encrypted_bytes = bytes.fromhex(encrypted)
        decrypted = bytes(v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(encrypted_bytes))
        return decrypted.decode()

    def store(
        self,
        integration_id: str,
        credential_type: CredentialType,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store an encrypted credential."""
        now = datetime.utcnow().isoformat()
        credential_id = f"cred_{secrets.token_hex(8)}"
        encrypted = self._encrypt(value)

        with self.db.cursor() as cur:
            # Delete existing credential of same type for this integration
            cur.execute("""
                DELETE FROM credentials
                WHERE integration_id = ? AND credential_type = ?
            """, (integration_id, credential_type.value))

            cur.execute("""
                INSERT INTO credentials
                (id, integration_id, credential_type, encrypted_value, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                credential_id,
                integration_id,
                credential_type.value,
                encrypted,
                json.dumps(metadata or {}),
                now,
                now,
            ))

        logger.info(f"Stored credential for integration {integration_id}")
        return credential_id

    def retrieve(self, integration_id: str, credential_type: CredentialType) -> Optional[str]:
        """Retrieve and decrypt a credential."""
        row = self.db.fetch_one("""
            SELECT encrypted_value FROM credentials
            WHERE integration_id = ? AND credential_type = ?
        """, (integration_id, credential_type.value))

        if row:
            return self._decrypt(row["encrypted_value"])
        return None

    def delete(self, integration_id: str, credential_type: Optional[CredentialType] = None) -> bool:
        """Delete credentials for an integration."""
        with self.db.cursor() as cur:
            if credential_type:
                cur.execute("""
                    DELETE FROM credentials
                    WHERE integration_id = ? AND credential_type = ?
                """, (integration_id, credential_type.value))
            else:
                cur.execute(
                    "DELETE FROM credentials WHERE integration_id = ?",
                    (integration_id,)
                )
            return cur.rowcount > 0


class UserSettingsRepository:
    """Repository for user settings and preferences."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_database()
        _init_integration_schema(self.db)

    def get_settings(self, api_key_id: str) -> Dict[str, Any]:
        """Get user settings."""
        row = self.db.fetch_one(
            "SELECT settings FROM user_settings WHERE api_key_id = ?",
            (api_key_id,)
        )
        if row:
            return json.loads(row["settings"])
        return self._default_settings()

    def update_settings(self, api_key_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings."""
        now = datetime.utcnow().isoformat()
        existing = self.get_settings(api_key_id)
        merged = {**existing, **settings}

        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO user_settings (api_key_id, settings, notification_preferences, created_at, updated_at)
                VALUES (?, ?, '{}', ?, ?)
                ON CONFLICT(api_key_id) DO UPDATE SET
                    settings = ?,
                    updated_at = ?
            """, (api_key_id, json.dumps(merged), now, now, json.dumps(merged), now))

        return merged

    def get_notification_preferences(self, api_key_id: str) -> Dict[str, Any]:
        """Get notification preferences."""
        row = self.db.fetch_one(
            "SELECT notification_preferences FROM user_settings WHERE api_key_id = ?",
            (api_key_id,)
        )
        if row:
            return json.loads(row["notification_preferences"])
        return self._default_notification_preferences()

    def update_notification_preferences(
        self, api_key_id: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update notification preferences."""
        now = datetime.utcnow().isoformat()
        existing = self.get_notification_preferences(api_key_id)
        merged = {**existing, **preferences}

        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO user_settings (api_key_id, settings, notification_preferences, created_at, updated_at)
                VALUES (?, '{}', ?, ?, ?)
                ON CONFLICT(api_key_id) DO UPDATE SET
                    notification_preferences = ?,
                    updated_at = ?
            """, (api_key_id, json.dumps(merged), now, now, json.dumps(merged), now))

        return merged

    def _default_settings(self) -> Dict[str, Any]:
        """Default user settings."""
        return {
            "theme": "system",
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD",
            "cache_duration_seconds": 30,
            "request_timeout_seconds": 30,
            "monitoring_interval_seconds": 30,
            "max_workflow_steps": 50,
        }

    def _default_notification_preferences(self) -> Dict[str, Any]:
        """Default notification preferences."""
        return {
            "enabled": True,
            "channels": {
                "email": False,
                "slack": False,
                "teams": False,
                "discord": False,
                "webhook": False,
            },
            "events": {
                "workflow_completed": True,
                "workflow_failed": True,
                "agent_error": True,
                "health_alert": True,
            },
        }


# Convenience functions
_integration_repo: Optional[IntegrationRepository] = None
_credential_repo: Optional[CredentialRepository] = None
_settings_repo: Optional[UserSettingsRepository] = None


def get_integration_repository() -> IntegrationRepository:
    """Get the integration repository instance."""
    global _integration_repo
    if _integration_repo is None:
        _integration_repo = IntegrationRepository()
    return _integration_repo


def get_credential_repository() -> CredentialRepository:
    """Get the credential repository instance."""
    global _credential_repo
    if _credential_repo is None:
        _credential_repo = CredentialRepository()
    return _credential_repo


def get_user_settings_repository() -> UserSettingsRepository:
    """Get the user settings repository instance."""
    global _settings_repo
    if _settings_repo is None:
        _settings_repo = UserSettingsRepository()
    return _settings_repo
