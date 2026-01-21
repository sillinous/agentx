"""
Integration Management API endpoints.

Provides REST API for:
- Managing external integrations (Slack, Email, Teams, etc.)
- Storing and retrieving credentials securely
- User settings and preferences
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import logging

from core.integrations import (
    IntegrationType,
    CredentialType,
    Integration,
    get_integration_repository,
    get_credential_repository,
    get_user_settings_repository,
)
from core.auth import get_api_key, require_write, APIKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# Request/Response Models

class CreateIntegrationRequest(BaseModel):
    """Request to create a new integration."""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Integration type: slack, email, teams, discord, webhook, api_endpoint, openai, anthropic, custom")
    config: Dict[str, Any] = Field(default_factory=dict)


class UpdateIntegrationRequest(BaseModel):
    """Request to update an integration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class StoreCredentialRequest(BaseModel):
    """Request to store a credential."""
    credential_type: str = Field(..., description="Type: api_key, oauth_token, webhook_url, smtp_config, bearer_token, basic_auth")
    value: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class IntegrationResponse(BaseModel):
    """Integration response model."""
    id: str
    name: str
    type: str
    config: Dict[str, Any]
    is_active: bool
    has_credentials: bool
    last_used_at: Optional[str]
    last_error: Optional[str]
    created_at: str
    updated_at: str


class UserSettingsRequest(BaseModel):
    """Request to update user settings."""
    theme: Optional[str] = None
    timezone: Optional[str] = None
    cache_duration_seconds: Optional[int] = Field(None, ge=0, le=3600)
    request_timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    monitoring_interval_seconds: Optional[int] = Field(None, ge=10, le=300)


class NotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    enabled: Optional[bool] = None
    channels: Optional[Dict[str, bool]] = None
    events: Optional[Dict[str, bool]] = None


# Slack Configuration Model
class SlackIntegrationConfig(BaseModel):
    """Slack-specific configuration."""
    workspace_name: Optional[str] = None
    default_channel: Optional[str] = "#general"
    bot_name: Optional[str] = "DevOps Hub"
    icon_emoji: Optional[str] = ":robot_face:"


# Email Configuration Model
class EmailIntegrationConfig(BaseModel):
    """Email-specific configuration."""
    smtp_host: str
    smtp_port: int = 587
    use_tls: bool = True
    from_address: str
    from_name: Optional[str] = "DevOps Hub"


# API Endpoints

@router.post("", response_model=IntegrationResponse)
async def create_integration(
    request: CreateIntegrationRequest,
    api_key: APIKey = Depends(require_write()),
):
    """Create a new integration."""
    try:
        integration_type = IntegrationType(request.type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration type: {request.type}. Valid types: {[t.value for t in IntegrationType]}"
        )

    repo = get_integration_repository()
    integration = repo.create(
        name=request.name,
        integration_type=integration_type,
        config=request.config,
        api_key_id=api_key.id,
    )

    logger.info(f"Created integration: {integration.name} ({integration.type.value})")
    return _integration_to_response(integration, has_credentials=False)


@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    type: Optional[str] = None,
    api_key: Optional[APIKey] = Depends(get_api_key),
):
    """List all integrations for the current user."""
    repo = get_integration_repository()
    cred_repo = get_credential_repository()

    if type:
        try:
            integration_type = IntegrationType(type)
            integrations = repo.list_by_type(integration_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid integration type: {type}"
            )
    else:
        integrations = repo.list_by_owner(api_key.id) if api_key else repo.list_all_active()

    result = []
    for integration in integrations:
        # Check if integration has credentials
        has_creds = cred_repo.retrieve(integration.id, CredentialType.API_KEY) is not None or \
                    cred_repo.retrieve(integration.id, CredentialType.WEBHOOK_URL) is not None or \
                    cred_repo.retrieve(integration.id, CredentialType.BEARER_TOKEN) is not None
        result.append(_integration_to_response(integration, has_credentials=has_creds))

    return result


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    api_key: Optional[APIKey] = Depends(get_api_key),
):
    """Get an integration by ID."""
    repo = get_integration_repository()
    integration = repo.get(integration_id)

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {integration_id}"
        )

    cred_repo = get_credential_repository()
    has_creds = cred_repo.retrieve(integration.id, CredentialType.API_KEY) is not None or \
                cred_repo.retrieve(integration.id, CredentialType.WEBHOOK_URL) is not None

    return _integration_to_response(integration, has_credentials=has_creds)


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    request: UpdateIntegrationRequest,
    api_key: APIKey = Depends(require_write()),
):
    """Update an integration."""
    repo = get_integration_repository()
    integration = repo.update(
        integration_id,
        name=request.name,
        config=request.config,
        is_active=request.is_active,
    )

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {integration_id}"
        )

    cred_repo = get_credential_repository()
    has_creds = cred_repo.retrieve(integration.id, CredentialType.API_KEY) is not None

    logger.info(f"Updated integration: {integration.name}")
    return _integration_to_response(integration, has_credentials=has_creds)


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    api_key: APIKey = Depends(require_write()),
):
    """Delete an integration and its credentials."""
    repo = get_integration_repository()
    if repo.delete(integration_id):
        logger.info(f"Deleted integration: {integration_id}")
        return {"deleted": True, "id": integration_id}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Integration not found: {integration_id}"
    )


@router.post("/{integration_id}/credentials")
async def store_credential(
    integration_id: str,
    request: StoreCredentialRequest,
    api_key: APIKey = Depends(require_write()),
):
    """Store a credential for an integration."""
    try:
        credential_type = CredentialType(request.credential_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid credential type: {request.credential_type}. Valid types: {[t.value for t in CredentialType]}"
        )

    # Verify integration exists
    int_repo = get_integration_repository()
    integration = int_repo.get(integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {integration_id}"
        )

    cred_repo = get_credential_repository()
    credential_id = cred_repo.store(
        integration_id=integration_id,
        credential_type=credential_type,
        value=request.value,
        metadata=request.metadata,
    )

    logger.info(f"Stored {credential_type.value} credential for integration {integration_id}")
    return {
        "stored": True,
        "credential_id": credential_id,
        "credential_type": credential_type.value,
    }


@router.delete("/{integration_id}/credentials/{credential_type}")
async def delete_credential(
    integration_id: str,
    credential_type: str,
    api_key: APIKey = Depends(require_write()),
):
    """Delete a credential from an integration."""
    try:
        cred_type = CredentialType(credential_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid credential type: {credential_type}"
        )

    cred_repo = get_credential_repository()
    if cred_repo.delete(integration_id, cred_type):
        return {"deleted": True}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Credential not found"
    )


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    api_key: APIKey = Depends(require_write()),
):
    """Test an integration by sending a test message/request."""
    int_repo = get_integration_repository()
    integration = int_repo.get(integration_id)

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {integration_id}"
        )

    cred_repo = get_credential_repository()

    # Test based on integration type
    try:
        if integration.type == IntegrationType.SLACK:
            webhook_url = cred_repo.retrieve(integration_id, CredentialType.WEBHOOK_URL)
            if not webhook_url:
                return {"success": False, "error": "No webhook URL configured"}

            # Import here to avoid circular imports
            from service.notification_service import send_slack_message
            result = await send_slack_message(
                webhook_url=webhook_url,
                message="Test message from DevOps Hub",
                channel=integration.config.get("default_channel"),
            )
            int_repo.update_last_used(integration_id, error=None if result["success"] else result.get("error"))
            return result

        elif integration.type == IntegrationType.WEBHOOK:
            webhook_url = cred_repo.retrieve(integration_id, CredentialType.WEBHOOK_URL)
            if not webhook_url:
                return {"success": False, "error": "No webhook URL configured"}

            from service.notification_service import send_webhook
            result = await send_webhook(
                url=webhook_url,
                payload={"test": True, "message": "Test from DevOps Hub", "timestamp": datetime.utcnow().isoformat()},
            )
            int_repo.update_last_used(integration_id, error=None if result["success"] else result.get("error"))
            return result

        elif integration.type == IntegrationType.EMAIL:
            # Email test would require SMTP config
            return {"success": False, "error": "Email testing not yet implemented"}

        else:
            return {"success": False, "error": f"Testing not implemented for {integration.type.value}"}

    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        int_repo.update_last_used(integration_id, error=str(e))
        return {"success": False, "error": str(e)}


# User Settings Endpoints

settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@settings_router.get("")
async def get_settings(
    api_key: Optional[APIKey] = Depends(get_api_key),
):
    """Get user settings."""
    user_id = api_key.id if api_key else "__default__"
    repo = get_user_settings_repository()
    settings = repo.get_settings(user_id)
    preferences = repo.get_notification_preferences(user_id)
    return {
        "settings": settings,
        "notification_preferences": preferences,
    }


@settings_router.patch("")
async def update_settings(
    request: UserSettingsRequest,
    api_key: APIKey = Depends(require_write()),
):
    """Update user settings."""
    repo = get_user_settings_repository()
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    settings = repo.update_settings(api_key.id, updates)
    return {"settings": settings}


@settings_router.get("/notifications")
async def get_notification_preferences(
    api_key: Optional[APIKey] = Depends(get_api_key),
):
    """Get notification preferences."""
    user_id = api_key.id if api_key else "__default__"
    repo = get_user_settings_repository()
    return repo.get_notification_preferences(user_id)


@settings_router.patch("/notifications")
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    api_key: APIKey = Depends(require_write()),
):
    """Update notification preferences."""
    repo = get_user_settings_repository()
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    preferences = repo.update_notification_preferences(api_key.id, updates)
    return preferences


# Helper Functions

def _integration_to_response(integration: Integration, has_credentials: bool) -> IntegrationResponse:
    """Convert Integration to response model."""
    return IntegrationResponse(
        id=integration.id,
        name=integration.name,
        type=integration.type.value,
        config=integration.config,
        is_active=integration.is_active,
        has_credentials=has_credentials,
        last_used_at=integration.last_used_at,
        last_error=integration.last_error,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )
