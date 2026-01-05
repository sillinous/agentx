"""Base provider class for all external API integrations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str, details: Optional[Dict] = None):
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(f"[{provider}] {message}")


class BaseProvider(ABC):
    """Abstract base class for all external API providers."""

    provider_name: str = "base"
    requires_api_key: bool = True

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the provider.

        Args:
            api_key: API key for the service. If not provided, will attempt
                     to read from environment variable.
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self._api_key = api_key or self._get_api_key_from_env()

        if self.requires_api_key and not self._api_key:
            logger.warning(
                f"{self.provider_name} API key not configured. "
                f"Set {self._env_var_name} environment variable."
            )

    @property
    def _env_var_name(self) -> str:
        """Environment variable name for the API key."""
        return f"{self.provider_name.upper()}_API_KEY"

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable."""
        return os.environ.get(self._env_var_name)

    @property
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        if self.requires_api_key:
            return bool(self._api_key)
        return True

    def validate_config(self) -> bool:
        """Validate that the provider is properly configured."""
        if not self.is_configured:
            raise ProviderError(
                f"API key not configured. Set {self._env_var_name} environment variable.",
                self.provider_name
            )
        return True

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the provider API is accessible.

        Returns:
            Dict with 'status' ('ok' or 'error') and optional 'message'.
        """
        pass

    def _handle_error(self, error: Exception, operation: str) -> None:
        """Handle and log provider errors."""
        logger.error(f"{self.provider_name} error during {operation}: {error}")
        raise ProviderError(
            f"Failed to {operation}: {str(error)}",
            self.provider_name,
            {"original_error": str(error)}
        )
