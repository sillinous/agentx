"""
Pytest configuration for marketing-agent tests.
Adds all agent package directories to Python path for imports.
Provides fixtures for mocking LangChain/LangGraph agents.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add all agent package directories to the Python path
package_root = Path(__file__).parent
sys.path.insert(0, str(package_root))
sys.path.insert(0, str(package_root.parent / "builder-agent"))
sys.path.insert(0, str(package_root.parent / "analytics-agent"))


# Mock the LLM and agent initialization to avoid OpenAI API calls during tests
def mock_get_agent():
    """Returns a mock agent that returns a predictable response."""
    mock_agent = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"type": "test", "content": "mock response"}'
    mock_agent.invoke.return_value = {"messages": [mock_response]}
    return mock_agent


# Pre-patch the ChatOpenAI to prevent API calls during module import
mock_llm = MagicMock()
mock_llm.bind_tools.return_value = mock_llm
mock_llm.invoke.return_value = MagicMock(
    content='{"type": "test", "content": "mock"}', tool_calls=[]
)

# Patch before imports happen
patch("langchain_openai.ChatOpenAI", return_value=mock_llm).start()
