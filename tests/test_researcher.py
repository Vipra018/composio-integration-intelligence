"""Unit tests for researcher agent and orchestrator."""

from pydantic import HttpUrl

from src.agents.orchestrator import ResearchOrchestrator
from src.agents.researcher import AppResearcher
from src.models.app_metadata import AppMetadata
from src.models.enums import BuildabilityScore, MCPAvailability


def test_app_researcher_salesforce() -> None:
    researcher = AppResearcher(mode="test")
    app = AppMetadata(
        id="salesforce",
        name="Salesforce",
        category="CRM and Sales",
        description="Enterprise CRM platform.",
        website=HttpUrl("https://salesforce.com"),
        original_source_hint="https://developer.salesforce.com",
    )

    result = researcher.research(app)
    assert result.app_id == "salesforce"
    assert result.name == "Salesforce"
    assert len(result.evidence) > 0
    assert result.feasibility.feasibility_score >= 7.0
    assert result.feasibility.buildability in (
        BuildabilityScore.BUILDABLE_NOW,
        BuildabilityScore.BUILDABLE_WITH_LIMITATIONS,
    )


def test_app_researcher_sherlock_cli() -> None:
    researcher = AppResearcher(mode="test")
    app = AppMetadata(
        id="sherlock",
        name="Sherlock",
        category="Data, SEO and Scraping",
        description="OSINT CLI tool to hunt social media accounts.",
        website=HttpUrl("https://github.com/sherlock-project/sherlock"),
        original_source_hint="https://github.com/sherlock-project/sherlock",
    )

    result = researcher.research(app)
    assert result.app_id == "sherlock"
    # CLI tool should be recognized with limitation
    assert result.feasibility.buildability == BuildabilityScore.BUILDABLE_WITH_LIMITATIONS
    assert any(b.blocker_type == "architecture" for b in result.feasibility.primary_blockers)


def test_orchestrator_initialization() -> None:
    orchestrator = ResearchOrchestrator()
    apps = orchestrator.list_apps()
    assert len(apps) == 100
    status = orchestrator.get_status()
    assert status["total_applications"] == 100
    assert "categories" in status
