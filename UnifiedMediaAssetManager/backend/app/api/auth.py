"""Authentication API endpoints with registration, login, and test users."""

import os
import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.database import UserDB
from .. import auth as auth_module

router = APIRouter(prefix="/auth", tags=["authentication"])

# =============================================================================
# Configuration
# =============================================================================

IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development").lower() == "production"
ALLOW_TEST_USERS = os.environ.get("ALLOW_TEST_USERS", "true").lower() == "true"

# Test user definitions - NEVER use in production
TEST_USERS = [
    {
        "username": "test_admin",
        "email": "admin@test.local",
        "display_name": "Test Admin User",
        "password": "TestAdmin123!",
        "roles": ["admin", "editor", "viewer"],
    },
    {
        "username": "test_editor",
        "email": "editor@test.local",
        "display_name": "Test Editor User",
        "password": "TestEditor123!",
        "roles": ["editor", "viewer"],
    },
    {
        "username": "test_viewer",
        "email": "viewer@test.local",
        "display_name": "Test Viewer User",
        "password": "TestViewer123!",
        "roles": ["viewer"],
    },
    {
        "username": "test_creator",
        "email": "creator@test.local",
        "display_name": "Test Content Creator",
        "password": "TestCreator123!",
        "roles": ["creator", "viewer"],
    },
]


# =============================================================================
# Pydantic Models
# =============================================================================

class UserRegister(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    display_name: Optional[str]
    roles: List[str]
    is_test_user: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# Helper Functions
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    if not password_hash or ":" not in password_hash:
        return False
    salt, hashed = password_hash.split(":", 1)
    check_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return check_hash == hashed


def user_to_response(user: UserDB) -> UserResponse:
    """Convert UserDB to response model."""
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=getattr(user, 'email', None),
        display_name=user.display_name,
        roles=getattr(user, 'roles', ["viewer"]) or ["viewer"],
        is_test_user=getattr(user, 'is_test_user', False),
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user account."""
    existing = db.query(UserDB).filter(UserDB.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    user = UserDB(
        username=data.username,
        display_name=data.display_name or data.username,
    )
    # Set additional fields if they exist on the model
    if hasattr(user, 'email'):
        user.email = data.email
    if hasattr(user, 'password_hash'):
        user.password_hash = hash_password(data.password)
    if hasattr(user, 'roles'):
        user.roles = ["viewer"]
    if hasattr(user, 'is_test_user'):
        user.is_test_user = False
    if hasattr(user, 'is_active'):
        user.is_active = True

    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth_module.create_access_token(
        subject=user.username,
        roles=getattr(user, 'roles', ["viewer"]),
    )

    return TokenResponse(
        access_token=token,
        user=user_to_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Login with username and password."""
    user = db.query(UserDB).filter(UserDB.username == data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check password if model has password_hash
    if hasattr(user, 'password_hash') and user.password_hash:
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

    # Update last login if field exists
    if hasattr(user, 'last_login'):
        user.last_login = datetime.utcnow()
        db.commit()

    token = auth_module.create_access_token(
        subject=user.username,
        roles=getattr(user, 'roles', ["viewer"]),
    )

    return TokenResponse(
        access_token=token,
        user=user_to_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(auth_module.get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Get current authenticated user's information."""
    user = db.query(UserDB).filter(UserDB.username == current_user.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_to_response(user)


@router.post("/seed-test-users", response_model=Dict[str, Any])
async def seed_test_users(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Seed test users for development/testing.
    CRITICAL: Disabled in production.
    """
    if IS_PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test user seeding is disabled in production"
        )

    if not ALLOW_TEST_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test user seeding is disabled by configuration"
        )

    created = []
    skipped = []

    for test_user in TEST_USERS:
        existing = db.query(UserDB).filter(UserDB.username == test_user["username"]).first()
        if existing:
            skipped.append(test_user["username"])
            continue

        user = UserDB(
            username=test_user["username"],
            display_name=test_user["display_name"],
        )
        if hasattr(user, 'email'):
            user.email = test_user["email"]
        if hasattr(user, 'password_hash'):
            user.password_hash = hash_password(test_user["password"])
        if hasattr(user, 'roles'):
            user.roles = test_user["roles"]
        if hasattr(user, 'is_test_user'):
            user.is_test_user = True
        if hasattr(user, 'is_active'):
            user.is_active = True

        db.add(user)
        created.append({
            "username": test_user["username"],
            "password": test_user["password"],
            "roles": test_user["roles"],
        })

    db.commit()

    return {
        "message": "Test users seeded successfully",
        "warning": "FOR DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION",
        "created": created,
        "skipped": skipped,
    }


@router.delete("/purge-test-users", response_model=Dict[str, Any])
async def purge_test_users(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Remove all test users. Call before production deployment."""
    if hasattr(UserDB, 'is_test_user'):
        test_users = db.query(UserDB).filter(UserDB.is_test_user == True).all()
    else:
        test_users = db.query(UserDB).filter(
            UserDB.username.in_([u["username"] for u in TEST_USERS])
        ).all()

    count = len(test_users)
    usernames = [u.username for u in test_users]

    for user in test_users:
        db.delete(user)
    db.commit()

    return {"message": f"Purged {count} test users", "purged_usernames": usernames}


@router.get("/test-users", response_model=List[Dict[str, Any]])
async def list_test_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all test users in the system."""
    if hasattr(UserDB, 'is_test_user'):
        test_users = db.query(UserDB).filter(UserDB.is_test_user == True).all()
    else:
        test_users = db.query(UserDB).filter(
            UserDB.username.in_([u["username"] for u in TEST_USERS])
        ).all()

    return [
        {
            "username": u.username,
            "roles": getattr(u, 'roles', ["viewer"]),
            "email": getattr(u, 'email', None),
        }
        for u in test_users
    ]


@router.get("/production-check", response_model=Dict[str, Any])
async def production_readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Check if system is ready for production deployment."""
    if hasattr(UserDB, 'is_test_user'):
        test_user_count = db.query(UserDB).filter(UserDB.is_test_user == True).count()
    else:
        test_user_count = db.query(UserDB).filter(
            UserDB.username.in_([u["username"] for u in TEST_USERS])
        ).count()

    issues = []
    warnings = []

    if test_user_count > 0:
        issues.append(f"{test_user_count} test user(s) exist - run /auth/purge-test-users")

    if auth_module.JWT_SECRET == "dev-secret":
        issues.append("JWT_SECRET is using default value")

    if auth_module.DISABLE_AUTH:
        issues.append("Authentication is disabled (DISABLE_AUTH=true)")

    if not IS_PRODUCTION:
        warnings.append("ENVIRONMENT is not set to 'production'")

    return {
        "ready_for_production": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "test_user_count": test_user_count,
    }
