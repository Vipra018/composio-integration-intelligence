"""
Integration Intelligence - Configuration Management.

Loads and validates settings from environment variables and .env files using Pydantic Settings.
Guarantees fail-fast behavior on missing critical parameters while providing robust defaults.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory: parent directory of 'src'
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Global configuration settings for Integration Intelligence."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    environment: str = Field(default="development", description="Environment: development, testing, production")
    app_name: str = Field(default="Integration Intelligence", description="System application name")
    project_root: Path = Field(default=PROJECT_ROOT, description="Root folder of the repository")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    log_file_path: Path = Field(
        default=PROJECT_ROOT / "logs" / "integration_intelligence.log",
        description="Path to local log output file",
    )

    # LLM Settings
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, or google")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    llm_model: str = Field(default="gpt-4o-mini", description="Model name to use for research extraction")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Sampling temperature for LLM")
    llm_max_tokens: int = Field(default=2500, ge=100, le=8192, description="Max generation tokens")

    # Composio Integration Settings
    composio_api_key: Optional[str] = Field(default=None, description="Composio API key")
    composio_base_url: str = Field(
        default="https://backend.composio.dev/api/v1",
        description="Composio API base endpoint",
    )
    composio_entity_id: str = Field(default="default", description="Entity ID used in Composio connections")

    # Research Agent Operational Parameters
    max_concurrent_research_tasks: int = Field(default=5, ge=1, le=20, description="Max concurrent agent tasks")
    request_timeout_seconds: int = Field(default=30, ge=5, le=120, description="HTTP request timeout in seconds")
    rate_limit_delay_seconds: float = Field(default=1.0, ge=0.0, description="Delay between consecutive queries")
    max_search_results_per_query: int = Field(default=5, ge=1, le=10, description="Results retrieved per query")

    # Browser Automation Settings (Verification)
    headless_browser: bool = Field(default=True, description="Run browser automation in headless mode")
    browser_timeout_ms: int = Field(default=15000, description="Browser action timeout in milliseconds")

    # Storage & Data Paths
    dataset_path: Path = Field(default=PROJECT_ROOT / "data" / "apps.json", description="Benchmark dataset path")
    results_dir: Path = Field(default=PROJECT_ROOT / "data" / "results", description="Target output directory")
    reports_dir: Path = Field(default=PROJECT_ROOT / "reports", description="Report and visualization export directory")

    def ensure_directories_exist(self) -> None:
        """Create necessary directories if they do not yet exist."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)


# Singleton settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return the global Settings instance."""
    return settings

