import os
import time
from typing import Optional, Dict

import jwt
from fastapi import Depends, HTTPException, Header

# Simple JWT-based auth for dev and prototyping.
# Environment variables:
# - JWT_SECRET: secret signing key (default: 'dev-secret')
# - JWT_ALGO: signing algorithm (default: HS256)
# - DISABLE_AUTH: if set to '1' or 'true', auth checks bypassed (for local dev)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGO = os.environ.get("JWT_ALGO", "HS256")
DISABLE_AUTH = os.environ.get("DISABLE_AUTH", "false").lower() in ("1", "true")


def create_access_token(subject: str = "dev", roles: Optional[list] = None, expires_in: int = 60 * 60 * 24) -> str:
    payload = {
        "sub": subject,
        "roles": roles or ["admin"],
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> Dict:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """Dependency that returns decoded token payload or raises 401.

    If `DISABLE_AUTH` is true, returns a default dev user payload.
    """
    if DISABLE_AUTH:
        return {"sub": "dev", "roles": ["admin"]}

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if authorization.lower().startswith("bearer "):
        token = authorization.split(None, 1)[1]
    else:
        token = authorization

    return decode_token(token)


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict]:
    """Dependency that returns decoded token payload or None if not authenticated.

    Unlike `get_current_user`, this does not raise an error for missing tokens.
    Useful for endpoints that work with or without authentication.
    """
    if DISABLE_AUTH:
        return {"sub": "dev", "roles": ["admin"]}

    if not authorization:
        return None

    try:
        if authorization.lower().startswith("bearer "):
            token = authorization.split(None, 1)[1]
        else:
            token = authorization
        return decode_token(token)
    except HTTPException:
        return None


# Lightweight endpoint helpers for testing: create a token (dev use only)
def issue_dev_token(subject: str = "dev") -> str:
    return create_access_token(subject=subject)


def has_role(user_payload: dict, role: str) -> bool:
    roles = user_payload.get("roles", []) if isinstance(user_payload, dict) else []
    return role in roles


def require_role(user_payload: dict, role: str) -> None:
    """Raise 403 if `user_payload` does not have `role` in its roles list.

    Respects the `DISABLE_AUTH` toggle for local development (no-op when true).
    """
    if DISABLE_AUTH:
        return
    if not has_role(user_payload, role):
        raise HTTPException(status_code=403, detail=f"Missing required role: {role}")
