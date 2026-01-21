"""Pytest configuration and fixtures."""
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_metadata():
    """Sample project metadata for testing."""
    return {
        "has_tests": True,
        "has_docker": True,
        "has_readme": True,
        "has_ci_cd": False,
        "has_stripe": False,
        "has_auth": True,
        "has_api": True,
        "has_database": True,
        "has_typescript": True,
        "has_package_json": True,
        "loc_estimate": 2500,
        "tech_stack": ["Next.js", "FastAPI", "PostgreSQL"],
    }


@pytest.fixture
def empty_metadata():
    """Empty project metadata for testing."""
    return {}


@pytest.fixture
def tier1_metadata():
    """Metadata for a Tier 1 (high-value) project."""
    return {
        "has_tests": True,
        "has_docker": True,
        "has_readme": True,
        "has_ci_cd": True,
        "has_stripe": True,
        "has_auth": True,
        "has_api": True,
        "has_database": True,
        "has_typescript": True,
        "has_package_json": True,
        "loc_estimate": 10000,
        "tech_stack": ["Next.js", "FastAPI", "PostgreSQL", "OpenAI"],
    }


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "id": "test-project-123",
        "name": "TestProject",
        "path": "/path/to/test",
        "description": "A test project",
        "tech_stack": ["Next.js", "FastAPI"],
        "maturity_score": 65,
        "revenue_score": 55,
        "effort_score": 70,
        "overall_score": 62,
        "tier": "tier2",
        "status": "development",
        "revenue_potential_min": 3000,
        "revenue_potential_max": 15000,
    }


@pytest.fixture
def sample_opportunity():
    """Sample opportunity data."""
    return {
        "id": "test-opp-123",
        "project_id": "test-project-123",
        "title": "Add Stripe Integration",
        "description": "Integrate Stripe for payments",
        "category": "payment",
        "priority": "high",
        "effort_hours": 16,
        "revenue_impact": 5000,
        "status": "pending",
    }
