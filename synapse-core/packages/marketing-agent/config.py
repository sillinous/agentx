"""
Configuration management for Synapse Core Backend.
Uses Pydantic Settings for environment variable validation.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    app_name: str = Field(default="Synapse Agent Server")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database Configuration
    database_url: Optional[str] = Field(default=None)
    postgres_user: str = Field(default="synapse")
    postgres_password: str = Field(default="")
    postgres_db: str = Field(default="synapse")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None)

    # JWT Configuration
    jwt_secret: str = Field(default="development-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)

    # Environment
    node_env: str = Field(default="development")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.node_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.node_env.lower() == "development"

    @property
    def effective_database_url(self) -> str:
        """Returns DATABASE_URL or constructs one from parts."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def validate_production_config(self) -> list[str]:
        """Validates configuration for production deployment.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.is_production:
            if self.jwt_secret == "development-secret-key-change-in-production":
                errors.append("JWT_SECRET must be changed for production")

            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required for production")

            if not self.postgres_password:
                errors.append("POSTGRES_PASSWORD is required for production")

            if self.debug:
                errors.append("DEBUG should be False in production")

        return errors


@lru_cache
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()


def validate_environment() -> None:
    """Validates environment on startup.

    Raises:
        RuntimeError: If production configuration is invalid
    """
    settings = get_settings()
    errors = settings.validate_production_config()

    if errors:
        error_msg = "Production configuration errors:\n" + "\n".join(
            f"  - {e}" for e in errors
        )
        if settings.is_production:
            raise RuntimeError(error_msg)
        else:
            import logging

            logging.warning(error_msg)


# Export for easy access
settings = get_settings()
