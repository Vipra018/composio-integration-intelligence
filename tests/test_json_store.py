"""Unit tests for JSONStore persistence and checkpointing."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import HttpUrl

from src.models.enums import (
    APIBreadth,
    APIType,
    AuthMethod,
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
    MCPResearch,
)
from src.storage.json_store import JSONStore


@pytest.fixture
def temp_store(tmp_path: Path) -> JSONStore:
    return JSONStore(base_dir=tmp_path)


@pytest.fixture
def sample_result() -> AppResearchResult:
    return AppResearchResult(
        app_id="test-app",
        name="Test App",
        category="Developer, Infra and Data platforms",
        one_line_description="Test SaaS application for storage validation purposes.",
        auth=AuthResearch(
            supported_methods=[AuthMethod.OAUTH2, AuthMethod.API_KEY],
            primary_method=AuthMethod.OAUTH2,
            credential_accessibility=CredentialAccessibility.SELF_SERVE_FREE,
            credential_evidence="Self-serve developer credentials available.",
            oauth_grant_types=["authorization_code", "refresh_token"],
            token_lifespan_notes="1 hour access token.",
            accessibility_notes="Instant self-serve registration.",
        ),
        api_surface=APISurfaceResearch(
            api_types=[APIType.REST],
            breadth=APIBreadth.BROAD,
            breadth_rationale="Extensive REST endpoints covering all primary models.",
            has_rest=True,
            has_graphql=False,
            has_webhooks=True,
            has_rate_limits_documented=True,
            rate_limit_details="5000 requests per hour.",
            official_sdks=["Python"],
            openapi_spec_available=True,
            openapi_spec_url=None,
        ),
        mcp=MCPResearch(
            availability=MCPAvailability.OFFICIAL,
            composio_tool_supported=True,
            composio_app_slug="test-app",
            existing_servers=["https://github.com/example/mcp"],
            notes="Official MCP server supported.",
        ),
        feasibility=FeasibilityEvaluation(
            buildability=BuildabilityScore.BUILDABLE_NOW,
            primary_blocker=None,
            feasibility_score=9.0,
            rationale="Comprehensive technical reasoning explaining the assigned score for test app.",
            key_strengths=["Free tier", "OpenAPI spec"],
            primary_blockers=[],
        ),
        evidence=[
            EvidenceURL(
                url=HttpUrl("https://developer.example.com"),
                title="Developer Example Docs",
                snippet="We support standard OAuth2 authentication.",
                source_type="official_documentation",
                claim="OAuth2 supported",
                retrieved_at=datetime.now(timezone.utc),
            )
        ],
        confidence=ConfidenceLevel.HIGH,
        verification_status=VerificationStatus.AUTOMATED_PASS,
        agent_version="2.0.0",
    )


def test_save_and_load_individual_result(temp_store: JSONStore, sample_result: AppResearchResult) -> None:
    path = temp_store.save_app_result(sample_result)
    assert path.exists()
    assert path.name == "test-app.json"
    assert temp_store.has_checkpoint("test-app")

    loaded = temp_store.load_app_result("test-app")
    assert loaded is not None
    assert loaded.app_id == "test-app"
    assert loaded.name == "Test App"
    assert loaded.feasibility.feasibility_score == 9.0
    assert loaded.auth.primary_method == AuthMethod.OAUTH2


def test_load_nonexistent_returns_none(temp_store: JSONStore) -> None:
    assert temp_store.load_app_result("non-existent") is None
    assert not temp_store.has_checkpoint("non-existent")


def test_completed_app_ids_and_listing(temp_store: JSONStore, sample_result: AppResearchResult) -> None:
    temp_store.save_app_result(sample_result)
    ids = temp_store.get_completed_app_ids()
    assert "test-app" in ids

    all_res = temp_store.list_results()
    assert len(all_res) == 1
    assert all_res[0].app_id == "test-app"


def test_save_and_load_aggregated_results(temp_store: JSONStore, sample_result: AppResearchResult) -> None:
    results_map = {"test-app": sample_result}
    agg_path = temp_store.save_all_results(results_map)
    assert agg_path.exists()

    loaded_map = temp_store.load_all_results(agg_path)
    assert len(loaded_map) == 1
    assert "test-app" in loaded_map
    assert loaded_map["test-app"].name == "Test App"

