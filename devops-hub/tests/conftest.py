"""
Pytest configuration and fixtures for DevOps Hub tests.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture
def test_client():
    """Create a test client for the API."""
    from service.api import app
    import httpx
    # Use httpx directly with ASGITransport for compatibility
    from httpx._transports.asgi import ASGITransport
    transport = ASGITransport(app=app)
    return httpx.Client(transport=transport, base_url="http://test")


@pytest.fixture
def sample_agent_metadata():
    """Sample agent metadata for testing."""
    return {
        "id": "test-agent",
        "name": "Test Agent",
        "version": "1.0.0",
        "type": "worker",
        "domain": "utility",
        "status": "development",
        "description": "A test agent for unit testing",
        "capabilities": ["test-capability", "another-capability"],
        "protocols": ["a2a/1.0", "acp/1.0"],
        "implementations": {"python": "tests/test_agent.py"},
        "documentation": "docs/test-agent.md",
    }


@pytest.fixture
def sample_workflow_definition():
    """Sample workflow definition for testing."""
    return {
        "name": "Test Workflow",
        "description": "A workflow for testing",
        "version": "1.0.0",
        "steps": [
            {
                "name": "Step 1",
                "type": "agent",
                "agent_id": "research-analyzer",
                "capability": "market-analysis",
                "input_mapping": {"market": "input.market"},
                "output_key": "step1_result",
            },
            {
                "name": "Step 2",
                "type": "agent",
                "agent_id": "documentation-generator",
                "capability": "guide-creation",
                "output_key": "step2_result",
            },
        ],
    }
