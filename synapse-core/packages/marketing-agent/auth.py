"""
JWT Authentication Module for Synapse Core
Handles token generation, validation, and user authentication.
"""

import os
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError
from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Load configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "development-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


# --- Pydantic Models ---
class TokenData(BaseModel):
    user_id: str
    email: Optional[str] = None
    subscription_tier: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Token Generation ---
def create_access_token(
    user_id: str, email: str, subscription_tier: str = "standard"
) -> str:
    """
    Creates a JWT access token for a user.

    Args:
        user_id: Unique identifier for the user
        email: User's email address
        subscription_tier: User's subscription level

    Returns:
        Encoded JWT token as a string
    """
    expiration = datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload = {
        "user_id": user_id,
        "email": email,
        "subscription_tier": subscription_tier,
        "exp": expiration,
        "iat": datetime.now(UTC),
        "type": "access_token",
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    logger.info(
        "Access token created",
        extra={
            "user_id": user_id,
            "email": email,
            "expiration": expiration.isoformat(),
        },
    )

    return token


# --- Token Validation ---
def decode_access_token(token: str) -> TokenData:
    """
    Decodes and validates a JWT access token.

    Args:
        token: JWT token string

    Returns:
        TokenData object containing user information

    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        subscription_tier: str = payload.get("subscription_tier")

        if user_id is None:
            logger.warning("Token missing user_id claim")
            raise credentials_exception

        if payload.get("type") != "access_token":
            logger.warning("Invalid token type", extra={"type": payload.get("type")})
            raise credentials_exception

        logger.info("Token successfully decoded", extra={"user_id": user_id})

        return TokenData(
            user_id=user_id,
            email=email,
            subscription_tier=subscription_tier,
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except PyJWTError as e:
        logger.error("JWT validation error", extra={"error": str(e)})
        raise credentials_exception


# --- Token Extraction ---
def extract_token_from_header(authorization: str) -> str:
    """
    Extracts the token from the Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Extracted token string

    Raises:
        HTTPException: If header format is invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return authorization[7:]  # Remove "Bearer " prefix


# --- Development Mode Utilities ---
def create_development_token(user_id: str = "dev-user-001") -> str:
    """
    Creates a development token for testing purposes.
    Only use in development environment!

    Args:
        user_id: Optional user ID for the dev token

    Returns:
        JWT token for development use
    """
    if os.getenv("NODE_ENV") == "production":
        raise RuntimeError("Development tokens cannot be created in production")

    logger.warning(
        "Creating DEVELOPMENT TOKEN - This should only be used in development!",
        extra={"user_id": user_id},
    )

    return create_access_token(
        user_id=user_id,
        email=f"{user_id}@dev.synapse.local",
        subscription_tier="enterprise",  # Give dev token full access
    )


# --- Authentication Verification ---
def verify_user_access(token_data: TokenData, required_tier: str = "standard") -> bool:
    """
    Verifies if a user has the required subscription tier for an operation.

    Args:
        token_data: Decoded token data
        required_tier: Minimum required subscription tier

    Returns:
        True if user has required access, False otherwise
    """
    tier_hierarchy = {
        "standard": 1,
        "enterprise": 2,
    }

    user_tier_level = tier_hierarchy.get(token_data.subscription_tier, 0)
    required_tier_level = tier_hierarchy.get(required_tier, 0)

    has_access = user_tier_level >= required_tier_level

    logger.info(
        "Access verification",
        extra={
            "user_id": token_data.user_id,
            "user_tier": token_data.subscription_tier,
            "required_tier": required_tier,
            "has_access": has_access,
        },
    )

    return has_access
