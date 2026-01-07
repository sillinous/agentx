"""
Pytest configuration and fixtures for marketing-agent tests.
"""

import os
import sys
from pathlib import Path

# Set test environment variables BEFORE importing any modules
os.environ["TESTING"] = "1"
os.environ["JWT_SECRET"] = "test-secret-for-testing"

# Add parent directory to path so tests can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
