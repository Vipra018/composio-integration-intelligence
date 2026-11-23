"""
Integration Intelligence - Custom Exceptions Hierarchy.

Standardized domain-specific exceptions for configuration, dataset validation,
agent research workflows, MCP integration, and external service handling.
"""

from typing import Any, Dict, Optional


class IntegrationIntelligenceError(Exception):
    """Base exception for all Integration Intelligence operations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(IntegrationIntelligenceError):
    """Raised when environment variables or application configuration are invalid."""
    pass


class DatasetValidationError(IntegrationIntelligenceError):
    """Raised when the input SaaS applications dataset fails integrity or schema checks."""
    pass


class ResearchAgentError(IntegrationIntelligenceError):
    """Raised when an error occurs during agent research execution."""
    pass


class EvidenceVerificationError(IntegrationIntelligenceError):
    """Raised when evidence verification fails or external documentation is unreachable."""
    pass


class ComposioIntegrationError(IntegrationIntelligenceError):
    """Raised when interacting with Composio SDK or tools fails."""
    pass


class BrowserAutomationError(IntegrationIntelligenceError):
    """Raised when browser automation encounters an error during verification."""
    pass


class RateLimitExceededError(IntegrationIntelligenceError):
    """Raised when external API or search rate limits are exceeded."""
    pass


class StorageError(IntegrationIntelligenceError):
    """Raised when loading or persisting research results fails."""
    pass


class LLMServiceError(IntegrationIntelligenceError):
    """Raised when external or local LLM execution fails."""
    pass


# Convenient aliases
DatasetError = DatasetValidationError
ResearchError = ResearchAgentError

