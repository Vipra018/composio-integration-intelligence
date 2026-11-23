"""Unit tests for evidence extraction and classification logic."""

from datetime import datetime, timezone
from pydantic import HttpUrl

from src.models.app_metadata import AppMetadata
from src.models.enums import (
    APIBreadth,
    AuthMethod,
    BuildabilityScore,
    CredentialAccessibility,
)
from src.research.document_fetcher import FetchedDocument
from src.research.evidence_extractor import EvidenceExtractor
from src.research.research_classifier import ResearchClassifier


def test_evidence_extractor_pattern_matching() -> None:
    extractor = EvidenceExtractor()
    doc = FetchedDocument(
        url="https://docs.github.com/en/rest",
        title="GitHub REST API",
        text_content=(
            "GitHub REST API: Authenticate with a personal access token (classic or fine-grained), "
            "or with a GitHub App using OAuth 2.0. Available to all users with self-serve free accounts. "
            "Rate limits: 5,000 requests per hour."
        ),
        status_code=200,
        fetched_at=datetime.now(timezone.utc),
        content_length=220,
    )

    evidence = extractor.extract_evidence([doc])
    assert len(evidence) > 0
    claims = [e.claim.lower() for e in evidence if e.claim]
    assert any("auth" in c for c in claims)
    assert any("credential" in c for c in claims)


def test_classifier_github() -> None:
    app = AppMetadata(
        id="github",
        name="GitHub",
        category="Developer, Infra and Data platforms",
        description="Version control and collaboration platform.",
        website=HttpUrl("https://github.com"),
        original_source_hint="https://docs.github.com",
    )

    extractor = EvidenceExtractor()
    classifier = ResearchClassifier()

    doc = FetchedDocument(
        url="https://docs.github.com/en/rest",
        title="GitHub REST API",
        text_content=(
            "GitHub REST API allows creating integrations, retrieving data, and automating workflows. "
            "Supports Personal Access Tokens (PAT) and OAuth 2.0 apps. Self-serve free access is available. "
            "Rate limits apply."
        ),
        status_code=200,
        fetched_at=datetime.now(timezone.utc),
        content_length=250,
    )

    evidence = extractor.extract_evidence([doc])
    result = classifier.classify(app, evidence, full_text=doc.text_content)

    assert result.app_id == "github"
    assert result.auth.primary_method in (AuthMethod.OAUTH2, AuthMethod.PERSONAL_ACCESS_TOKEN)
    assert result.auth.credential_accessibility == CredentialAccessibility.SELF_SERVE_FREE
    assert result.feasibility.buildability == BuildabilityScore.BUILDABLE_NOW
    assert result.feasibility.feasibility_score >= 8.0


def test_classifier_notebooklm_no_public_api() -> None:
    app = AppMetadata(
        id="notebooklm",
        name="NotebookLM",
        category="AI, Research and Media-native",
        description="Personalized AI research assistant.",
        website=HttpUrl("https://notebooklm.google.com"),
        original_source_hint="https://notebooklm.google.com",
    )

    extractor = EvidenceExtractor()
    classifier = ResearchClassifier()

    doc = FetchedDocument(
        url="https://notebooklm.google.com",
        title="NotebookLM",
        text_content="NotebookLM is an experimental web app. Google has no public developer REST API or SDK for NotebookLM.",
        status_code=200,
        fetched_at=datetime.now(timezone.utc),
        content_length=120,
    )

    evidence = extractor.extract_evidence([doc])
    result = classifier.classify(app, evidence, full_text=doc.text_content)

    assert result.feasibility.buildability == BuildabilityScore.NOT_CURRENTLY_BUILDABLE
    assert result.feasibility.feasibility_score <= 2.0
    assert any(b.blocker_type == "missing_endpoints" for b in result.feasibility.primary_blockers)
