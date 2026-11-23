"""
Tests for Pydantic Models and Domain Taxonomy Enums.

Verifies schema constraints, validation rules, serialization, and edge cases.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from src.models.app_metadata import AppMetadata
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
from src.models.research import (
    APISurfaceResearch,
    AppResearchResult,
    AuthResearch,
    EvidenceURL,
    FeasibilityEvaluation,
    IntegrationBlocker,
    MCPResearch,
)


def test_app_metadata_valid() -> None:
    """Test valid AppMetadata instantiation."""
    app = AppMetadata(
        id="github",
        name="GitHub",
        category="Developer, Infra and Data platforms",
        original_source_hint="https://github.com",
        website="https://github.com",
        developer_documentation_url="https://docs.github.com/en/rest",
        description="Developer platform for version control and collaboration.",
        target_use_cases=["repo_creation", "issue_triage", "pull_request_review"],
    )
    assert app.id == "github"
    assert str(app.website).rstrip("/") == "https://github.com"
    assert app.original_source_hint == "https://github.com"
    assert app.developer_documentation_url is not None
    assert len(app.target_use_cases) == 3


def test_app_metadata_optional_dev_docs() -> None:
    """Test AppMetadata with null developer_documentation_url."""
    app = AppMetadata(
        id="dealcloud",
        name="DealCloud",
        category="CRM and Sales",
        original_source_hint="https://dealcloud.com",
        website="https://dealcloud.com",
        developer_documentation_url=None,
        description="Specialized CRM platform for private equity and investment banking.",
    )
    assert app.developer_documentation_url is None
    assert app.original_source_hint == "https://dealcloud.com"


def test_app_metadata_invalid_id() -> None:
    """Test AppMetadata rejects uppercase or special character IDs."""
    with pytest.raises(ValidationError):
        AppMetadata(
            id="GitHub_App",  # Invalid uppercase and underscore
            name="GitHub",
            category="Developer, Infra and Data platforms",
            original_source_hint="https://github.com",
            website="https://github.com",
            developer_documentation_url="https://docs.github.com",
            description="A code collaboration and CI/CD platform.",
        )


def test_app_research_result_lifecycle() -> None:
    """Test building a complete AppResearchResult and validating schema integrity."""
    evidence = EvidenceURL(
        url="https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api",
        title="GitHub REST API Authentication Overview",
        snippet="You can authenticate to the GitHub REST API using a personal access token or OAuth app.",
        retrieved_at=datetime.now(timezone.utc),
    )

    blocker = IntegrationBlocker(
        title="Secondary Rate Limit on Bulk GraphQL Queries",
        description="GitHub imposes aggressive concurrent query rate limits for heavy agentic searches.",
        severity=BlockerSeverity.MEDIUM,
        blocker_type="rate_limit",
    )

    auth = AuthResearch(
        supported_methods=[AuthMethod.OAUTH2, AuthMethod.API_KEY, AuthMethod.BEARER_TOKEN],
        primary_method=AuthMethod.OAUTH2,
        credential_accessibility=CredentialAccessibility.SELF_SERVE_FREE,
        oauth_grant_types=["authorization_code", "refresh_token"],
        token_lifespan_notes="User tokens can have configurable expiry or be revoked instantly.",
    )

    api_surface = APISurfaceResearch(
        api_types=[APIType.REST, APIType.GRAPHQL],
        breadth=APIBreadth.BROAD,
        has_webhooks=True,
        has_rate_limits_documented=True,
        rate_limit_details="5,000 requests per hour for authenticated users.",
        official_sdks=["Python (PyGithub)", "TypeScript (@octokit/rest)", "Go (go-github)"],
        openapi_spec_available=True,
        openapi_spec_url="https://github.com/github/rest-api-description",
    )

    mcp = MCPResearch(
        availability=MCPAvailability.COMPOSIO,
        composio_tool_supported=True,
        composio_app_slug="github",
        existing_servers=["@modelcontextprotocol/server-github"],
        notes="Composio provides rich native actions; official MCP server also available.",
    )

    feasibility = FeasibilityEvaluation(
        buildability=BuildabilityScore.BUILDABLE_NOW,
        feasibility_score=9.5,
        rationale="Top-tier API documentation, instant self-serve token generation, and native Composio & MCP support.",
        key_strengths=["Instant self-serve tokens", "Extensive webhooks", "Official OpenAPI specification"],
        primary_blockers=[blocker],
    )

    result = AppResearchResult(
        app_id="github",
        name="GitHub",
        category="Developer Tools & Infrastructure",
        one_line_description="Distributed version control, pull requests, and CI/CD platform.",
        auth=auth,
        api_surface=api_surface,
        mcp=mcp,
        feasibility=feasibility,
        evidence=[evidence],
        confidence=ConfidenceLevel.HIGH,
        verification_status=VerificationStatus.AUTOMATED_PASS,
        agent_version="1.0.0",
    )

    assert result.app_id == "github"
    assert result.feasibility.feasibility_score == 9.5
    assert result.auth.primary_method == AuthMethod.OAUTH2
    assert len(result.evidence) == 1

    # Test JSON serialization and deserialization
    json_data = result.model_dump_json()
    assert "github" in json_data

    rehydrated = AppResearchResult.model_validate_json(json_data)
    assert rehydrated.app_id == result.app_id
    assert rehydrated.feasibility.feasibility_score == 9.5


def test_feasibility_score_boundaries() -> None:
    """Test feasibility score bounds (0.0 to 10.0)."""
    with pytest.raises(ValidationError):
        FeasibilityEvaluation(
            buildability=BuildabilityScore.BUILDABLE_NOW,
            feasibility_score=11.5,  # Exceeds max 10.0
            rationale="This should fail validation due to invalid score range.",
        )

    with pytest.raises(ValidationError):
        FeasibilityEvaluation(
            buildability=BuildabilityScore.NOT_CURRENTLY_BUILDABLE,
            feasibility_score=-1.0,  # Below min 0.0
            rationale="This should fail validation due to negative score.",
        )
