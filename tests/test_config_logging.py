"""
Tests for Configuration Management, Logging, and Custom Exceptions.
"""

from pathlib import Path
import pytest

from src.config import Settings
from src.exceptions import (
    BrowserAutomationError,
    ComposioIntegrationError,
    ConfigurationError,
    DatasetValidationError,
    EvidenceVerificationError,
    IntegrationIntelligenceError,
    RateLimitExceededError,
    ResearchAgentError,
)
from src.logging_utils import configure_logging, logger


def test_settings_defaults() -> None:
    """Test default values of Settings."""
    settings = Settings()
    assert settings.environment == "development"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.max_concurrent_research_tasks == 5
    assert settings.request_timeout_seconds == 30
    assert settings.dataset_path.name == "apps.json"


def test_settings_ensure_directories(tmp_path: Path) -> None:
    """Test that ensure_directories_exist creates target folders."""
    custom_settings = Settings(
        environment="testing",
        results_dir=tmp_path / "custom_results",
        reports_dir=tmp_path / "custom_reports",
        log_file_path=tmp_path / "custom_logs" / "agent.log",
    )
    assert not custom_settings.results_dir.exists()
    assert not custom_settings.reports_dir.exists()
    assert not custom_settings.log_file_path.parent.exists()

    custom_settings.ensure_directories_exist()

    assert custom_settings.results_dir.exists()
    assert custom_settings.reports_dir.exists()
    assert custom_settings.log_file_path.parent.exists()


def test_exception_hierarchy() -> None:
    """Verify that domain exceptions derive from IntegrationIntelligenceError."""
    exceptions = [
        ConfigurationError("Config missing"),
        DatasetValidationError("Dataset bad"),
        ResearchAgentError("Agent failed"),
        EvidenceVerificationError("Evidence invalid"),
        ComposioIntegrationError("Composio API error"),
        BrowserAutomationError("Browser crashed"),
        RateLimitExceededError("Rate limit exceeded"),
    ]

    for exc in exceptions:
        assert isinstance(exc, IntegrationIntelligenceError)
        assert exc.message in str(exc)

    # Test error with details dictionary
    exc_with_details = ResearchAgentError("Timeout", details={"app": "salesforce", "attempt": 3})
    assert "salesforce" in str(exc_with_details)


def test_logging_configuration(tmp_path: Path) -> None:
    """Verify that logger initializes and writes to log file without error."""
    log_file = tmp_path / "test_logging.log"
    custom_settings = Settings(
        environment="testing",
        log_level="DEBUG",
        log_file_path=log_file,
    )
    configure_logging(custom_settings)

    test_message = "Test log message for integration intelligence"
    logger.info(test_message)

    assert log_file.exists(), "Log file was not created"
    content = log_file.read_text(encoding="utf-8")
    assert test_message in content
