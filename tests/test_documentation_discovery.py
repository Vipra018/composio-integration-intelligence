"""Unit tests for search provider and documentation discovery."""

from pydantic import HttpUrl

from src.models.app_metadata import AppMetadata
from src.research.documentation_discovery import DocumentationDiscovery
from src.research.search_provider import MockSearchProvider


def test_mock_search_provider_query_generation() -> None:
    provider = MockSearchProvider()
    app = AppMetadata(
        id="github",
        name="GitHub",
        category="Developer, Infra and Data platforms",
        description="Developer collaboration and code hosting platform.",
        website=HttpUrl("https://github.com"),
        original_source_hint="https://docs.github.com",
    )

    queries = provider.generate_queries(app)
    assert len(queries) >= 4
    categories = {q.category for q in queries}
    assert "auth" in categories
    assert "api" in categories
    assert "pricing" in categories
    assert "mcp" in categories


def test_mock_search_provider_results() -> None:
    provider = MockSearchProvider()
    results = provider.search("github api documentation", max_results=3)
    assert len(results) > 0
    assert any("docs.github.com" in r.url for r in results)


def test_documentation_discovery_candidate_ranking() -> None:
    app = AppMetadata(
        id="salesforce",
        name="Salesforce",
        category="CRM and Sales",
        description="Enterprise customer relationship management platform.",
        website=HttpUrl("https://salesforce.com"),
        original_source_hint="https://developer.salesforce.com/docs",
        developer_documentation_url=HttpUrl("https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm"),
    )

    discovery = DocumentationDiscovery(search_provider=MockSearchProvider())
    candidates = discovery.discover_candidate_urls(app)

    # 1st candidate should be explicit developer_documentation_url
    assert len(candidates) > 0
    assert "intro_rest.htm" in candidates[0]
    # No duplicate URLs in candidate list
    assert len(candidates) == len(set(candidates))
