"""
Integration Intelligence - Research Result Models.

Pydantic schemas capturing the multidimensional integration feasibility findings
for each investigated SaaS application.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from src.models.enums import (
    APIBreadth,
    APIType,
    AuthMethod,
    BlockerSeverity,
    BuildabilityScore,
    ConfidenceLevel,
    CredentialAccessibility,
    MCPAvailability,
    VerificationStatus,
)


class EvidenceURL(BaseModel):
    """Corroborating source citation supporting specific research claims."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: HttpUrl = Field(..., description="Absolute URL to documentation or source page.")
    title: str = Field(..., min_length=2, description="Source page title or reference descriptor.")
    snippet: Optional[str] = Field(
        default=None,
        max_length=1500,
        description="Relevant text excerpt substantiating the claim.",
    )
    source_type: str = Field(
        default="official_documentation",
        description="Type of source: official_documentation, api_reference, pricing, repository, or search_result.",
    )
    claim: Optional[str] = Field(
        default=None,
        max_length=500,
        description="The specific integration claim substantiated by this evidence.",
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the reference evidence was retrieved.",
    )


class IntegrationBlocker(BaseModel):
    """Identified barrier or friction point preventing seamless agent integration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=3, max_length=150, description="Short summary of the blocker.")
    description: str = Field(..., min_length=10, description="Detailed explanation of the obstacle.")
    severity: BlockerSeverity = Field(
        default=BlockerSeverity.MEDIUM,
        description="Severity level: CRITICAL, HIGH, MEDIUM, LOW.",
    )
    blocker_type: str = Field(
        ...,
        description="Category of impediment: auth_gate, pricing_tier, rate_limit, missing_endpoints, anti_bot, etc.",
    )


class AuthResearch(BaseModel):
    """Analysis of authentication architecture and credential acquisition."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    supported_methods: List[AuthMethod] = Field(
        ...,
        min_length=1,
        description="All authentication methods supported by the SaaS platform (OAuth2, API Key, Token, etc.).",
    )
    primary_method: AuthMethod = Field(
        ...,
        description="Recommended primary authentication protocol for autonomous agent toolkits.",
    )
    credential_accessibility: CredentialAccessibility = Field(
        ...,
        description="Accessibility tier required to generate developer credentials or access tokens.",
    )
    credential_evidence: Optional[str] = Field(
        default=None,
        description="Detailed evidence explaining the credential accessibility classification.",
    )
    oauth_grant_types: List[str] = Field(
        default_factory=list,
        description="Supported OAuth2 grant flows (e.g., authorization_code, client_credentials, refresh_token).",
    )
    token_lifespan_notes: Optional[str] = Field(
        default=None,
        description="Notes regarding token expiration, refresh mechanisms, and rotation policies.",
    )
    accessibility_notes: Optional[str] = Field(
        default=None,
        description="Details on credential gating, required plans, or approval wait times.",
    )


class APISurfaceResearch(BaseModel):
    """Analysis of the API interface, developer tools, and endpoints."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    api_types: List[APIType] = Field(
        ...,
        min_length=1,
        description="Architectural styles supported by the public API (REST, GraphQL, gRPC, etc.).",
    )
    breadth: APIBreadth = Field(
        ...,
        description="Completeness and scope of public API endpoints: BROAD, MODERATE, NARROW, UNKNOWN.",
    )
    breadth_rationale: Optional[str] = Field(
        default=None,
        description="Explanation of how the API breadth was determined.",
    )
    has_rest: bool = Field(default=False, description="Whether REST endpoints are provided.")
    has_graphql: bool = Field(default=False, description="Whether GraphQL APIs are supported.")
    has_webhooks: bool = Field(
        default=False,
        description="Whether asynchronous webhook events or event streaming are supported.",
    )
    has_rate_limits_documented: bool = Field(
        default=False,
        description="Whether API rate limits and throttling quotas are publicly documented.",
    )
    rate_limit_details: Optional[str] = Field(
        default=None,
        description="Documented rate limits (e.g., requests per minute, per user, or burst allowances).",
    )
    official_sdks: List[str] = Field(
        default_factory=list,
        description="Official SDK languages provided by the vendor (e.g., Python, TypeScript, Go).",
    )
    openapi_spec_available: bool = Field(
        default=False,
        description="Whether an official OpenAPI/Swagger specification exists.",
    )
    openapi_spec_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to the official OpenAPI or Swagger definition file.",
    )


class MCPResearch(BaseModel):
    """Analysis of Model Context Protocol (MCP) ecosystem readiness."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    availability: MCPAvailability = Field(
        ...,
        description="Status of MCP server availability: OFFICIAL, COMMUNITY, COMPOSIO, NO_KNOWN_MCP, UNKNOWN.",
    )
    composio_tool_supported: bool = Field(
        default=False,
        description="Whether Composio natively supports an integration/action toolkit for this app.",
    )
    composio_app_slug: Optional[str] = Field(
        default=None,
        description="Matching application slug in Composio's integration directory if supported.",
    )
    existing_servers: List[str] = Field(
        default_factory=list,
        description="Names or repository links of verified MCP servers (e.g. ModelContextProtocol or Community).",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes on MCP server coverage, tool completeness, or implementation gaps.",
    )


class FeasibilityEvaluation(BaseModel):
    """Evaluation of agent toolkit buildability, score, and architectural rationale."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    buildability: BuildabilityScore = Field(
        ...,
        description="Classification: BUILDABLE_NOW, BUILDABLE_WITH_LIMITATIONS, PARTNERSHIP_REQUIRED, NOT_CURRENTLY_BUILDABLE, INSUFFICIENT_INFORMATION.",
    )
    primary_blocker: Optional[str] = Field(
        default=None,
        description="The single primary blocker or gating factor for this application.",
    )
    feasibility_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Quantitative feasibility index between 0.0 (impossible) and 10.0 (turnkey).",
    )
    rationale: str = Field(
        ...,
        min_length=20,
        description="Comprehensive technical reasoning explaining the assigned score.",
    )
    key_strengths: List[str] = Field(
        default_factory=list,
        description="Key advantages facilitating integration (e.g., clean OAuth, sandbox tier, rich webhooks).",
    )
    primary_blockers: List[IntegrationBlocker] = Field(
        default_factory=list,
        description="List of identified integration blockers or frictional elements.",
    )

    @field_validator("feasibility_score")
    @classmethod
    def round_score(cls, val: float) -> float:
        return round(val, 2)


class AppResearchResult(BaseModel):
    """Complete, validated research profile for a single SaaS application."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    app_id: str = Field(
        ...,
        description="Unique kebab-case identifier matching the dataset.",
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    name: str = Field(..., min_length=1, description="Official application name.")
    category: str = Field(..., min_length=2, description="Standardized application category.")
    one_line_description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Concise, verified description of the application's core functionality.",
    )

    # Core Investigation Dimensions
    auth: AuthResearch = Field(..., description="Authentication mechanisms and credential access.")
    api_surface: APISurfaceResearch = Field(..., description="API architecture and endpoints.")
    mcp: MCPResearch = Field(..., description="Model Context Protocol ecosystem availability.")
    feasibility: FeasibilityEvaluation = Field(..., description="Integration feasibility and buildability rating.")

    # Evidence & Verification
    evidence: List[EvidenceURL] = Field(
        default_factory=list,
        description="Official evidence and citation URLs.",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.HIGH,
        description="Confidence level in the research findings.",
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="Audit verification status.",
    )

    # Metadata
    researched_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when research was conducted.",
    )
    agent_version: str = Field(
        default="1.0.0",
        description="Version identifier of the research agent harness.",
    )
