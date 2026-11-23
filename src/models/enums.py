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
                if val_clean in ("FREE_TRIAL", "SELF_SERVE_TRIAL", "TRIAL"):
                    if hasattr(cls, "TRIAL"):
                        return cls.TRIAL
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
                if val_clean in ("PARTNER_DEPENDENT", "PARTNERSHIP_REQUIRED"):
                    if hasattr(cls, "PARTNER_DEPENDENT"):
                        return cls.PARTNER_DEPENDENT
                    if hasattr(cls, "PARTNERSHIP_REQUIRED"):
                        return cls.PARTNERSHIP_REQUIRED
                if val_clean in ("REQUIRES_HUMAN_REVIEW", "NEEDS_HUMAN_REVIEW"):
                    if hasattr(cls, "NEEDS_HUMAN_REVIEW"):
                        return cls.NEEDS_HUMAN_REVIEW
                    if hasattr(cls, "REQUIRES_HUMAN_REVIEW"):
                        return cls.REQUIRES_HUMAN_REVIEW
                if val_clean in ("MANUALLY_VERIFIED", "HUMAN_VERIFIED"):
                    if hasattr(cls, "HUMAN_VERIFIED"):
                        return cls.HUMAN_VERIFIED
                    if hasattr(cls, "MANUALLY_VERIFIED"):
                        return cls.MANUALLY_VERIFIED
                if val_clean in ("UNVERIFIED", "INSUFFICIENT_EVIDENCE"):
                    if hasattr(cls, "INSUFFICIENT_EVIDENCE"):
                        return cls.INSUFFICIENT_EVIDENCE
                    if hasattr(cls, "UNVERIFIED"):
                        return cls.UNVERIFIED
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
    TRIAL = "TRIAL"
    SELF_SERVE_PAID = "SELF_SERVE_PAID"
    ADMIN_APPROVAL = "ADMIN_APPROVAL"
    PARTNER_GATED = "PARTNER_GATED"
    CONTACT_SALES = "CONTACT_SALES"
    NOT_AVAILABLE = "NOT_AVAILABLE"
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
    NONE = "NONE"               # No public developer API exposed
    UNKNOWN = "UNKNOWN"         # Undocumented or cannot be determined


class MCPAvailability(CaseInsensitiveEnum):
    """Availability of Model Context Protocol (MCP) servers."""
    OFFICIAL = "OFFICIAL"                       # Vendor-maintained official MCP server
    COMMUNITY = "COMMUNITY"                     # Verified open-source community MCP server
    COMPOSIO = "COMPOSIO"                       # Available in Composio tooling / MCP catalog
    REFERENCE_SERVER = "REFERENCE_SERVER"       # Reference model context protocol server
    NO_KNOWN_MCP = "NO_KNOWN_MCP"               # No known MCP server found
    UNKNOWN = "UNKNOWN"                         # Unknown or unverified status


class BuildabilityScore(CaseInsensitiveEnum):
    """Feasibility classification for autonomous agent toolkit integration."""
    BUILDABLE_NOW = "BUILDABLE_NOW"                             # Turnkey / accessible developer API & auth
    BUILDABLE_WITH_LIMITATIONS = "BUILDABLE_WITH_LIMITATIONS"   # Technical friction (rate limits, complex OAuth)
    PARTNERSHIP_REQUIRED = "PARTNERSHIP_REQUIRED"               # Partner program or enterprise contract needed
    PARTNER_DEPENDENT = "PARTNER_DEPENDENT"                     # Partner-gated ecosystem or approval required
    NOT_CURRENTLY_BUILDABLE = "NOT_CURRENTLY_BUILDABLE"         # No public API or prohibited by terms of service
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"       # Inadequate evidence to determine feasibility
    UNKNOWN = "UNKNOWN"                                         # Unknown feasibility status


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
    HUMAN_VERIFIED = "HUMAN_VERIFIED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ConfidenceLevel(CaseInsensitiveEnum):
    """Confidence rating in the synthesized research findings."""
    HIGH = "HIGH"             # Multiple corroborating official documentation sources
    MEDIUM = "MEDIUM"         # Single source or partial documentation ambiguity
    LOW = "LOW"               # Inferential, documentation incomplete, or contradictory
    UNKNOWN = "UNKNOWN"       # No reliable evidence discovered


class Provenance(CaseInsensitiveEnum):
    """Audit provenance of a research finding or document."""
    LIVE_FETCHED = "LIVE_FETCHED"       # Retrieved over HTTP from external live web
    LIVE_SEARCHED = "LIVE_SEARCHED"     # Discovered via live search engine execution
    CACHED = "CACHED"                   # Retrieved from prior persisted execution run
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"   # Supplied by internal hardcoded test fixture
    INFERRED = "INFERRED"               # Derived via deterministic algorithmic rules
    UNKNOWN = "UNKNOWN"                 # Provenance cannot be reliably verified


class EvidencePolarity(CaseInsensitiveEnum):
    """Semantic polarity of textual evidence supporting a claim."""
    POSITIVE = "POSITIVE"               # Explicitly affirms capability or support
    NEGATIVE = "NEGATIVE"               # Explicitly denies, prohibits, or notes absence
    AMBIGUOUS = "AMBIGUOUS"             # Conditional, beta, roadmap, or conflicting
    ABSENT = "ABSENT"                   # No statement found in analyzed documentation

