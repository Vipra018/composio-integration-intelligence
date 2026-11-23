"""
Integration Intelligence - Enums and Taxonomy Definitions.

Defines standardized enumerations for authentication mechanisms, credential accessibility,
API surfaces, MCP availability, agent buildability, and verification statuses.
"""

from enum import Enum


class AuthMethod(str, Enum):
    """Authentication mechanisms supported by SaaS APIs."""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    SESSION_COOKIE = "session_cookie"
    WEBHOOK_HMAC = "webhook_hmac"
    MTLS = "mtls"
    OTHER = "other"


class CredentialAccessibility(str, Enum):
    """How developers or agents obtain API credentials."""
    SELF_SERVE_FREE = "self_serve_free"
    FREE_TRIAL = "free_trial"
    PAID_PLAN_REQUIRED = "paid_plan_required"
    ADMIN_APPROVAL_REQUIRED = "admin_approval_required"
    PARTNER_GATED = "partner_gated"
    CONTACT_SALES = "contact_sales"
    INVITE_ONLY = "invite_only"


class APIType(str, Enum):
    """Architectural style of the API surface."""
    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBHOOKS_ONLY = "webhooks_only"
    SDK_ONLY = "sdk_only"
    HYBRID = "hybrid"


class APIBreadth(str, Enum):
    """Breadth and completeness of public API coverage."""
    EXTENSIVE = "extensive"     # Full CRUD, events, webhooks, admin controls
    MODERATE = "moderate"       # Covers primary business objects and actions
    LIMITED = "limited"         # Narrow subset of features exposed
    MINIMAL = "minimal"         # Very few endpoints, strictly read-only or single action


class MCPAvailability(str, Enum):
    """Availability of Model Context Protocol (MCP) servers."""
    OFFICIAL = "official"                         # Vendor-maintained official MCP server
    COMMUNITY = "community"                       # Verified open-source community MCP server
    COMPOSIO_SUPPORTED = "composio_supported"     # Available in Composio tooling/MCP catalog
    CUSTOM_BUILD_REQUIRED = "custom_build_required" # No existing MCP server, must be built
    NONE = "none"                                 # Impossible or completely unsupported


class BuildabilityScore(str, Enum):
    """Feasibility of developing an autonomous agent tool or integration."""
    HIGH = "high"             # Standard auth, accessible sandbox, robust API docs, high developer velocity
    MEDIUM = "medium"         # Some friction (e.g. strict rate limits, complex OAuth, or paid tier required)
    LOW = "low"               # High friction (e.g. partner-gated, enterprise sales, legacy SOAP/XML)
    BLOCKED = "blocked"       # Zero public API access, anti-bot gates, or explicitly forbidden in ToS


class BlockerSeverity(str, Enum):
    """Severity classification of integration impediments."""
    CRITICAL = "critical"     # Hard blocker, prevents integration entirely
    HIGH = "high"             # Significant barrier, requires human intervention or paid contract
    MEDIUM = "medium"         # Technical friction (complex token refresh, tricky pagination)
    LOW = "low"               # Minor inconvenience (rate limit caution, deprecation notices)


class VerificationStatus(str, Enum):
    """Audit and validation status of the research findings."""
    UNVERIFIED = "unverified"
    AUTOMATED_PASS = "automated_pass"
    AUTOMATED_FAIL = "automated_fail"
    MANUALLY_VERIFIED = "manually_verified"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class ConfidenceLevel(str, Enum):
    """Confidence rating in the synthesized research findings."""
    VERY_HIGH = "very_high"   # Verified against official live API docs & Composio specs
    HIGH = "high"             # Multiple corroborating official documentation sources
    MEDIUM = "medium"         # Single source or partial documentation ambiguity
    LOW = "low"               # Inferential, documentation incomplete, or contradictory
