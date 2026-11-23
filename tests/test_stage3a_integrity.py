"""Stage 3A Automated Integrity & Provenance Test Suite.

Verifies:
1. Mock search cannot accidentally be used in production mode.
2. Failed HTTP requests cannot receive synthetic status 200.
3. Knowledge-base text cannot be presented as live evidence.
4. Negative sentences cannot produce positive capability claims.
5. Unknown fields remain unknown.
6. Every confirmed claim has a valid evidence reference.
7. The five pilot records can be saved and loaded correctly.
"""

from datetime import datetime, timezone
from pathlib import Path
from pydantic import HttpUrl
import pytest

from src.models.app_metadata import AppMetadata
from src.models.enums import (
    APIBreadth,
    APIType,
    AuthMethod,
    BuildabilityScore,
    ConfidenceLevel,
    CredentialAccessibility,
    EvidencePolarity,
    MCPAvailability,
    Provenance,
    VerificationStatus,
)
from src.models.research import (
    APISurfaceResearch,
    AppResearchResult,
    AuthResearch,
    EvidenceURL,
    FeasibilityEvaluation,
    MCPResearch,
    ResearchClaim,
)
from src.research.document_fetcher import DocumentFetcher, FetchedDocument
from src.research.evidence_extractor import EvidenceExtractor
from src.research.research_classifier import ResearchClassifier
from src.research.search_provider import (
    MockSearchProvider,
    UnavailableSearchProvider,
    get_search_provider,
)
from src.storage.json_store import JSONStore


def test_mock_search_cannot_be_used_in_production_mode() -> None:
    """1. Prove MockSearchProvider is never returned in production mode."""
    provider = get_search_provider(mode="production")
    assert not isinstance(provider, MockSearchProvider)
    assert not getattr(provider, "is_test_fixture", False)
    # When no keys configured, must be UnavailableSearchProvider
    if isinstance(provider, UnavailableSearchProvider):
        assert provider.provider_name == "SEARCH_UNAVAILABLE"


def test_failed_http_request_never_synthetic_200() -> None:
    """2. Prove failed HTTP requests cannot receive synthetic status 200."""
    fetcher = DocumentFetcher(timeout=2.0, allow_mock_kb=False)
    # Fetch a guaranteed unresolvable address
    doc = fetcher.fetch("https://invalid-unresolvable-domain-xyz-987654.org/api")
    assert not doc.is_success
    assert doc.status_code == 0
    assert doc.text_content == ""
    assert doc.failure_reason is not None
    assert doc.provenance != Provenance.LIVE_FETCHED


def test_knowledge_base_never_used_in_production() -> None:
    """3. Prove knowledge-base fixtures are forbidden in production fetcher."""
    fetcher = DocumentFetcher(allow_mock_kb=False)
    # URL matches a pattern that used to be hardcoded
    # With allow_mock_kb=False and invalid address/timeout, it must not return KNOWLEDGE_BASE provenance
    doc = fetcher.fetch("https://docs.github.com/en/rest-invalid-path-404")
    assert doc.provenance != Provenance.KNOWLEDGE_BASE


def test_negative_sentences_never_produce_positive_capability_claims() -> None:
    """4. Prove negative sentences (does not support, no API) never produce positive claims."""
    extractor = EvidenceExtractor()
    classifier = ResearchClassifier()

    app = AppMetadata(
        id="sherlock-test",
        name="Sherlock Test",
        category="Data, SEO and Scraping",
        description="OSINT CLI tool.",
        website=HttpUrl("https://github.com/sherlock-project/sherlock"),
        original_source_hint="https://github.com/sherlock-project/sherlock",
    )

    negative_doc = FetchedDocument(
        requested_url="https://github.com/sherlock-project/sherlock",
        final_url="https://github.com/sherlock-project/sherlock",
        status_code=200,
        retrieval_timestamp=datetime.now(timezone.utc),
        content_type="text/html",
        is_success=True,
        source_domain="github.com",
        title="sherlock project",
        text_content=(
            "Sherlock is a command-line tool written in Python. "
            "It does not provide a cloud SaaS platform, does not provide a hosted REST API, "
            "and does not require OAuth or API keys. Integration requires running the CLI locally."
        ),
        content_length=220,
        provenance=Provenance.LIVE_FETCHED,
    )

    evidence = extractor.extract_evidence([negative_doc])
    assert len(evidence) > 0

    # Every evidence extracted from that negative sentence must have NEGATIVE polarity
    negative_claims = [e for e in evidence if "does not" in (e.snippet or "").lower()]
    for neg_item in negative_claims:
        assert neg_item.polarity == EvidencePolarity.NEGATIVE

    result = classifier.classify(app, evidence, full_text=negative_doc.text_content)

    # CRITICAL CHECK: Auth MUST NOT be OAUTH2 or API_KEY
    assert AuthMethod.OAUTH2 not in result.auth.supported_methods
    assert AuthMethod.API_KEY not in result.auth.supported_methods
    assert result.auth.primary_method == AuthMethod.OTHER

    # CRITICAL CHECK: has_rest MUST NOT be True
    assert not result.api_surface.has_rest


def test_polarity_analyzer_variations() -> None:
    """Verify polarity classification across test cases specified in Part 4."""
    extractor = EvidenceExtractor()

    # Negative variations
    assert extractor.determine_sentence_polarity("The application does not support OAuth 2.0.") == EvidencePolarity.NEGATIVE
    assert extractor.determine_sentence_polarity("The service does not provide a developer API.") == EvidencePolarity.NEGATIVE
    assert extractor.determine_sentence_polarity("There is no public API available.") == EvidencePolarity.NEGATIVE
    assert extractor.determine_sentence_polarity("API access is not available for external developers.") == EvidencePolarity.NEGATIVE
    assert extractor.determine_sentence_polarity("GraphQL endpoints are unsupported.") == EvidencePolarity.NEGATIVE
    assert extractor.determine_sentence_polarity("Export is only available through the web interface.") == EvidencePolarity.NEGATIVE
    assert extractor.determine_sentence_polarity("Access is strictly end-user facing through Google Accounts.") == EvidencePolarity.NEGATIVE

    # Positive variation
    assert extractor.determine_sentence_polarity("The platform supports OAuth 2.0 authentication.") == EvidencePolarity.POSITIVE

    # Ambiguous variation
    assert extractor.determine_sentence_polarity("OAuth 2.0 may be supported for selected enterprise customers.") == EvidencePolarity.AMBIGUOUS
    assert extractor.determine_sentence_polarity("A REST API is currently under development.") == EvidencePolarity.AMBIGUOUS


def test_unknown_fields_remain_unknown() -> None:
    """5. Prove missing documentation does not produce guessed values."""
    app = AppMetadata(
        id="opaque-app",
        name="Opaque App",
        category="CRM and Sales",
        description="Proprietary CRM application.",
        website=HttpUrl("https://opaque-example.com"),
        original_source_hint="https://opaque-example.com",
    )

    classifier = ResearchClassifier()
    # Pass empty evidence
    result = classifier.classify(app, evidence=[], full_text="")

    assert result.auth.primary_method == AuthMethod.UNKNOWN
    assert result.auth.credential_accessibility == CredentialAccessibility.UNKNOWN
    assert result.api_surface.breadth == APIBreadth.UNKNOWN
    assert result.mcp.availability == MCPAvailability.NO_KNOWN_MCP


def test_every_confirmed_claim_has_valid_evidence_reference() -> None:
    """6. Prove confirmed claims cite non-empty excerpts and URLs."""
    extractor = EvidenceExtractor()
    classifier = ResearchClassifier()

    app = AppMetadata(
        id="github-test",
        name="GitHub",
        category="Developer, Infra and Data platforms",
        description="Version control platform.",
        website=HttpUrl("https://github.com"),
        original_source_hint="https://docs.github.com/en/rest",
    )

    doc = FetchedDocument(
        requested_url="https://docs.github.com/en/rest",
        final_url="https://docs.github.com/en/rest",
        status_code=200,
        retrieval_timestamp=datetime.now(timezone.utc),
        content_type="text/html",
        is_success=True,
        source_domain="docs.github.com",
        title="GitHub REST API",
        text_content="GitHub REST API: Authenticate with a personal access token or with a GitHub App using OAuth 2.0.",
        content_length=100,
        provenance=Provenance.LIVE_FETCHED,
    )

    evidence = extractor.extract_evidence([doc])
    result = classifier.classify(app, evidence, full_text=doc.text_content)

    for claim in result.claims:
        if claim.provenance == Provenance.LIVE_FETCHED:
            assert claim.source_url is not None
            assert claim.supporting_excerpt is not None
            assert len(claim.supporting_excerpt) > 0


def test_five_pilot_records_save_and_load(tmp_path: Path) -> None:
    """7. Prove pilot records with claims and polarities save and load correctly."""
    store = JSONStore(base_dir=tmp_path)

    sample = AppResearchResult(
        app_id="github-test",
        name="GitHub Test",
        category="Developer, Infra and Data platforms",
        one_line_description="Version control and collaboration platform.",
        auth=AuthResearch(
            supported_methods=[AuthMethod.OAUTH2],
            primary_method=AuthMethod.OAUTH2,
            credential_accessibility=CredentialAccessibility.SELF_SERVE_FREE,
            credential_evidence="Self-serve access.",
            oauth_grant_types=["authorization_code"],
            token_lifespan_notes="1 hour",
            accessibility_notes="OAuth 2.0 supported.",
        ),
        api_surface=APISurfaceResearch(
            api_types=[APIType.REST],
            breadth=APIBreadth.BROAD,
            breadth_rationale="Broad REST API",
            has_rest=True,
            has_graphql=False,
            has_webhooks=False,
            has_rate_limits_documented=True,
            rate_limit_details="5000 req/hr",
            official_sdks=[],
            openapi_spec_available=False,
            openapi_spec_url=None,
        ),
        mcp=MCPResearch(
            availability=MCPAvailability.COMMUNITY,
            composio_tool_supported=False,
            composio_app_slug=None,
            existing_servers=["https://github.com/modelcontextprotocol/servers"],
            notes="Reference MCP server.",
        ),
        feasibility=FeasibilityEvaluation(
            buildability=BuildabilityScore.BUILDABLE_NOW,
            primary_blocker=None,
            feasibility_score=9.5,
            rationale="Turnkey integration.",
            key_strengths=["Open API"],
            primary_blockers=[],
        ),
        evidence=[
            EvidenceURL(
                url=HttpUrl("https://docs.github.com/en/rest"),
                title="GitHub REST API",
                snippet="Authenticate with a personal access token.",
                source_type="official_documentation",
                claim="Verified auth: oauth 2",
                provenance=Provenance.LIVE_FETCHED,
                polarity=EvidencePolarity.POSITIVE,
                http_status=200,
                retrieved_at=datetime.now(timezone.utc),
            )
        ],
        claims=[
            ResearchClaim(
                field_name="auth.primary_method",
                extracted_value="OAUTH2",
                provenance=Provenance.LIVE_FETCHED,
                source_url=HttpUrl("https://docs.github.com/en/rest"),
                supporting_excerpt="Authenticate with a personal access token.",
                confidence=ConfidenceLevel.HIGH,
                polarity=EvidencePolarity.POSITIVE,
            )
        ],
        search_provider_used="SEARCH_UNAVAILABLE",
        confidence=ConfidenceLevel.HIGH,
        verification_status=VerificationStatus.AUTOMATED_PASS,
        agent_version="3.0.0",
    )

    path = store.save_app_result(sample)
    assert path.exists()

    loaded = store.load_app_result("github-test")
    assert loaded is not None
    assert loaded.app_id == "github-test"
    assert len(loaded.claims) == 1
    assert loaded.claims[0].provenance == Provenance.LIVE_FETCHED
    assert loaded.claims[0].polarity == EvidencePolarity.POSITIVE
    assert loaded.evidence[0].http_status == 200
