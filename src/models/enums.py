"""
Integration Intelligence - Enums and Taxonomy Definitions.

Defines standardized enumerations for authentication mechanisms, credential accessibility,
API surfaces, MCP availability, agent buildability, confidence, and verification statuses.
"""

from enum import Enum
from typing import Any


class CaseInsensitiveEnum(str, Enum):
    """Base enum supporting case-insensitive lookup and string serialization."""

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            val_clean = value.strip().upper().replace(" ", "_").replace("-", "_")
            for member in cls:
                if member.value == val_clean or member.name == val_clean:
                    return member
                # Handle common aliases
                if val_clean in ("COMPOSIO_SUPPORTED", "COMPOSIO"):
                    if hasattr(cls, "COMPOSIO"):
                        return cls.COMPOSIO
                if val_clean in ("EXTENSIVE", "BROAD"):
                    if hasattr(cls, "BROAD"):
                        return cls.BROAD
                if val_clean in ("LIMITED", "MINIMAL", "NARROW"):
                    if hasattr(cls, "NARROW"):
                        return cls.NARROW
                if val_clean in ("FREE_TRIAL", "SELF_SERVE_TRIAL"):
                    if hasattr(cls, "SELF_SERVE_TRIAL"):
                        return cls.SELF_SERVE_TRIAL
                if val_clean in ("PAID_PLAN_REQUIRED", "SELF_SERVE_PAID"):
                    if hasattr(cls, "SELF_SERVE_PAID"):
                        return cls.SELF_SERVE_PAID
                if val_clean in ("ADMIN_APPROVAL_REQUIRED", "ADMIN_APPROVAL"):
                    if hasattr(cls, "ADMIN_APPROVAL"):
                        return cls.ADMIN_APPROVAL
                if val_clean in ("VERY_HIGH", "HIGH"):
                    if hasattr(cls, "HIGH"):
                        return cls.HIGH
                if val_clean in ("HIGH", "BUILDABLE_NOW"):
                    if hasattr(cls, "BUILDABLE_NOW"):
                        return cls.BUILDABLE_NOW
                if val_clean in ("BLOCKED", "NOT_CURRENTLY_BUILDABLE"):
                    if hasattr(cls, "NOT_CURRENTLY_BUILDABLE"):
                        return cls.NOT_CURRENTLY_BUILDABLE
        return super()._missing_(value)


class AuthMethod(CaseInsensitiveEnum):
    """Authentication mechanisms supported by SaaS APIs."""
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BEARER_TOKEN = "BEARER_TOKEN"
    PERSONAL_ACCESS_TOKEN = "PERSONAL_ACCESS_TOKEN"
    BASIC_AUTH = "BASIC_AUTH"
    SESSION_COOKIE = "SESSION_COOKIE"
    WEBHOOK_HMAC = "WEBHOOK_HMAC"
    MTLS = "MTLS"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class CredentialAccessibility(CaseInsensitiveEnum):
    """How developers or agents obtain API credentials."""
    SELF_SERVE_FREE = "SELF_SERVE_FREE"
    SELF_SERVE_TRIAL = "SELF_SERVE_TRIAL"
    SELF_SERVE_PAID = "SELF_SERVE_PAID"
    ADMIN_APPROVAL = "ADMIN_APPROVAL"
    PARTNER_GATED = "PARTNER_GATED"
    CONTACT_SALES = "CONTACT_SALES"
    UNKNOWN = "UNKNOWN"


class APIType(CaseInsensitiveEnum):
    """Architectural style of the API surface."""
    REST = "REST"
    GRAPHQL = "GRAPHQL"
    GRPC = "GRPC"
    WEBHOOKS_ONLY = "WEBHOOKS_ONLY"
    SDK_ONLY = "SDK_ONLY"
    HYBRID = "HYBRID"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class APIBreadth(CaseInsensitiveEnum):
    """Breadth and completeness of public API coverage."""
    BROAD = "BROAD"             # Full CRUD, comprehensive data objects, events, webhooks
    MODERATE = "MODERATE"       # Covers primary business objects and major actions
    NARROW = "NARROW"           # Narrow or limited subset of features exposed
    UNKNOWN = "UNKNOWN"         # Undocumented or cannot be determined


class MCPAvailability(CaseInsensitiveEnum):
    """Availability of Model Context Protocol (MCP) servers."""
    OFFICIAL = "OFFICIAL"                       # Vendor-maintained official MCP server
    COMMUNITY = "COMMUNITY"                     # Verified open-source community MCP server
    COMPOSIO = "COMPOSIO"                       # Available in Composio tooling / MCP catalog
    NO_KNOWN_MCP = "NO_KNOWN_MCP"               # No known MCP server found
    UNKNOWN = "UNKNOWN"                         # Unknown or unverified status


class BuildabilityScore(CaseInsensitiveEnum):
    """Feasibility classification for autonomous agent toolkit integration."""
    BUILDABLE_NOW = "BUILDABLE_NOW"                             # Turnkey / accessible developer API & auth
    BUILDABLE_WITH_LIMITATIONS = "BUILDABLE_WITH_LIMITATIONS"   # Technical friction (rate limits, complex OAuth)
    PARTNERSHIP_REQUIRED = "PARTNERSHIP_REQUIRED"               # Partner program or enterprise contract needed
    NOT_CURRENTLY_BUILDABLE = "NOT_CURRENTLY_BUILDABLE"         # No public API or prohibited by terms of service
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"       # Inadequate evidence to determine feasibility


class BlockerSeverity(CaseInsensitiveEnum):
    """Severity classification of integration impediments."""
    CRITICAL = "CRITICAL"     # Hard blocker, prevents integration entirely
    HIGH = "HIGH"             # Significant barrier, requires human contract or intervention
    MEDIUM = "MEDIUM"         # Technical friction (rate limit quotas, token refresh complexities)
    LOW = "LOW"               # Minor inconvenience (deprecation warnings, optional webhook verification)


class VerificationStatus(CaseInsensitiveEnum):
    """Audit and validation status of the research findings."""
    UNVERIFIED = "UNVERIFIED"
    AUTOMATED_PASS = "AUTOMATED_PASS"
    AUTOMATED_FAIL = "AUTOMATED_FAIL"
    MANUALLY_VERIFIED = "MANUALLY_VERIFIED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class ConfidenceLevel(CaseInsensitiveEnum):
    """Confidence rating in the synthesized research findings."""
    HIGH = "HIGH"             # Multiple corroborating official documentation sources
    MEDIUM = "MEDIUM"         # Single source or partial documentation ambiguity
    LOW = "LOW"               # Inferential, documentation incomplete, or contradictory
    UNKNOWN = "UNKNOWN"       # No reliable evidence discovered
