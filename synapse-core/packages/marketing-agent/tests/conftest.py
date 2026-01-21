"""
Pytest configuration and fixtures for marketing-agent tests.
"""

import os
import sys
from pathlib import Path

# Set test environment variables BEFORE importing any modules
# This must be done before any imports that use these values
os.environ["TESTING"] = "true"
os.environ["JWT_SECRET"] = "test-secret-for-unit-tests-only"

# Add parent directory to path so tests can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


# Export the test secret for use in tests
TEST_JWT_SECRET = "test-secret-for-unit-tests-only"
