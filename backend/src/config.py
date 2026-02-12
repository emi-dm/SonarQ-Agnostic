"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # SonarQube settings
    sonarqube_url: str = Field(default="", description="SonarQube server URL")
    sonarqube_token: str = Field(default="", description="SonarQube API token")

    # Application settings
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")

    # Database settings
    database_url: str = Field(
        default="sqlite:///./sonarqube_visualizer.db",
        description="Database connection URL"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
