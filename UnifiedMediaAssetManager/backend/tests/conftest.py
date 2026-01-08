"""
Pytest configuration and fixtures for UnifiedMediaAssetManager backend tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["DISABLE_AUTH"] = "false"

from app.main import app
from app.database import get_db
from app.models.database import Base
from app import auth


# Create test database engine with in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    """Generate authentication headers for protected endpoints."""
    token = auth.issue_dev_token(subject="test-user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers():
    """Generate admin authentication headers."""
    # Use create_access_token directly for admin roles
    token = auth.create_access_token(subject="admin-user", roles=["admin"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_universe_data():
    """Sample universe data for testing."""
    import uuid
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Universe",
        "description": "A test universe for automated testing",
        "owner": "",
        "elements": []
    }


@pytest.fixture
def sample_element_data():
    """Sample element data for testing."""
    return {
        "name": "Test Character",
        "element_type": "Character"
    }


@pytest.fixture
def sample_component_data():
    """Sample component data for testing."""
    return {
        "type": "TextComponent",
        "data": {
            "field": "Description",
            "content": "This is a test component"
        }
    }
