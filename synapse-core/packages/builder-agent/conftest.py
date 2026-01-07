"""
Pytest configuration for builder-agent tests.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Set testing environment
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the ChatOpenAI before importing architect
mock_chat_openai = MagicMock()
mock_chat_openai.return_value = MagicMock()


@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI for all tests."""
    with patch("langchain_openai.ChatOpenAI", mock_chat_openai):
        yield
