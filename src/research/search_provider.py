"""Production search provider abstractions, API integrations, and mock fixtures."""

from __future__ import annotations

import abc
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from src.config import get_settings
from src.exceptions import SearchUnavailableError
from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata

logger = get_logger("research.search_provider")


@dataclass
class SearchResult:
    """Represents an individual search engine result with explicit provenance."""

    title: str
    url: str
    snippet: str
    source_domain: str
    retrieval_timestamp: datetime
    provider: str
    rank: int
    source_query: str


@dataclass
class SearchQuery:
    """Represents a targeted search query with execution state."""

    query: str
    category: str  # "auth", "api", "pricing", "mcp"
    executed: bool = False
    results_count: int = 0
    executed_at: Optional[datetime] = None


class BaseSearchProvider(abc.ABC):
    """Abstract base class for research search providers."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self.executed_queries: List[SearchQuery] = []

    def generate_queries(self, app: AppMetadata) -> List[SearchQuery]:
        """Generate targeted search queries for all research dimensions."""
        app_name = app.name
        queries = [
            SearchQuery(
                query=f"{app_name} API authentication OAuth2 API key developer documentation",
                category="auth",
            ),
            SearchQuery(
                query=f"{app_name} developer API documentation REST GraphQL endpoints",
                category="api",
            ),
            SearchQuery(
                query=f"{app_name} API access requirements developer account free tier paid enterprise",
                category="pricing",
            ),
            SearchQuery(
                query=f"{app_name} Model Context Protocol MCP server Composio integration agent",
                category="mcp",
            ),
        ]
        return queries

    @abc.abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute a search query and return top results."""
        pass


class TavilySearchProvider(BaseSearchProvider):
    """Production search provider via Tavily AI Search API."""

    ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout: float = 15.0) -> None:
        super().__init__(provider_name="tavily")
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        sq = SearchQuery(
            query=query,
            category="live_search",
            executed=True,
            executed_at=datetime.now(timezone.utc),
        )
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self.ENDPOINT,
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "basic",
                        "include_answer": False,
                    },
                )
                if resp.status_code != 200:
                    logger.error("Tavily search returned status %d: %s", resp.status_code, resp.text)
                    raise SearchUnavailableError(f"Tavily search HTTP {resp.status_code}: {resp.text}")

                data = resp.json()
                results: List[SearchResult] = []
                for idx, item in enumerate(data.get("results", [])[:max_results], 1):
                    raw_url = item.get("url", "")
                    domain = urlparse(raw_url).netloc or ""
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=raw_url,
                            snippet=item.get("content", ""),
                            source_domain=domain,
                            retrieval_timestamp=datetime.now(timezone.utc),
                            provider="tavily",
                            rank=idx,
                            source_query=query,
                        )
                    )
                sq.results_count = len(results)
                self.executed_queries.append(sq)
                return results
        except Exception as e:
            logger.error("Tavily search failed for query '%s': %s", query, e)
            raise SearchUnavailableError(f"Tavily search failed: {e}") from e


class SerperSearchProvider(BaseSearchProvider):
    """Production search provider via Google Serper API."""

    ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, api_key: str, timeout: float = 15.0) -> None:
        super().__init__(provider_name="serper")
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        sq = SearchQuery(
            query=query,
            category="live_search",
            executed=True,
            executed_at=datetime.now(timezone.utc),
        )
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self.ENDPOINT,
                    headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                    json={"q": query, "num": max_results},
                )
                if resp.status_code != 200:
                    raise SearchUnavailableError(f"Serper search HTTP {resp.status_code}: {resp.text}")

                data = resp.json()
                results: List[SearchResult] = []
                for idx, item in enumerate(data.get("organic", [])[:max_results], 1):
                    raw_url = item.get("link", "")
                    domain = urlparse(raw_url).netloc or ""
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=raw_url,
                            snippet=item.get("snippet", ""),
                            source_domain=domain,
                            retrieval_timestamp=datetime.now(timezone.utc),
                            provider="serper",
                            rank=idx,
                            source_query=query,
                        )
                    )
                sq.results_count = len(results)
                self.executed_queries.append(sq)
                return results
        except Exception as e:
            logger.error("Serper search failed: %s", e)
            raise SearchUnavailableError(f"Serper search failed: {e}") from e


class UnavailableSearchProvider(BaseSearchProvider):
    """Search provider when no external search API credentials are configured."""

    def __init__(self) -> None:
        super().__init__(provider_name="SEARCH_UNAVAILABLE")

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        logger.warning(
            "Live search requested, but no search API credentials (Tavily/Serper/Brave) are configured. "
            "Reporting SEARCH_UNAVAILABLE without fabricating results."
        )
        raise SearchUnavailableError(
            "SEARCH_UNAVAILABLE: No live search API credentials are configured. "
            "To enable live web search, set TAVILY_API_KEY or SERPER_API_KEY."
        )


class MockSearchProvider(BaseSearchProvider):
    """Deterministic, offline search provider STRICTLY FOR UNIT TESTING."""

    is_test_fixture: bool = True

    KNOWN_URL_MAPPINGS = {
        "salesforce": [
            SearchResult(
                title="Salesforce Developers: REST API Developer Guide",
                url="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm",
                snippet="Salesforce REST API provides powerful, convenient, and simple RESTful Web services interface.",
                source_domain="developer.salesforce.com",
                retrieval_timestamp=datetime.now(timezone.utc),
                provider="mock_test_fixture",
                rank=1,
                source_query="salesforce api",
            ),
        ],
        "github": [
            SearchResult(
                title="GitHub REST API Documentation",
                url="https://docs.github.com/en/rest",
                snippet="GitHub REST API allows creating integrations, retrieving data, and automating workflows.",
                source_domain="docs.github.com",
                retrieval_timestamp=datetime.now(timezone.utc),
                provider="mock_test_fixture",
                rank=1,
                source_query="github api",
            ),
        ],
        "shopify": [
            SearchResult(
                title="Shopify Dev: Admin API Overview",
                url="https://shopify.dev/docs/api/admin-rest",
                snippet="The Shopify Admin API lets you build apps and integrations for Shopify merchants.",
                source_domain="shopify.dev",
                retrieval_timestamp=datetime.now(timezone.utc),
                provider="mock_test_fixture",
                rank=1,
                source_query="shopify api",
            ),
        ],
        "sherlock": [
            SearchResult(
                title="Sherlock Project: Hunt down social media accounts by username across social networks",
                url="https://github.com/sherlock-project/sherlock",
                snippet="Sherlock is an open-source Python command-line OSINT tool to hunt usernames across social platforms.",
                source_domain="github.com",
                retrieval_timestamp=datetime.now(timezone.utc),
                provider="mock_test_fixture",
                rank=1,
                source_query="sherlock osint",
            ),
        ],
        "notebooklm": [
            SearchResult(
                title="Google NotebookLM - Personalized AI Research Assistant",
                url="https://notebooklm.google.com",
                snippet="NotebookLM is an experimental web application from Google Labs powered by Gemini.",
                source_domain="notebooklm.google.com",
                retrieval_timestamp=datetime.now(timezone.utc),
                provider="mock_test_fixture",
                rank=1,
                source_query="notebooklm api",
            ),
        ],
    }

    def __init__(self) -> None:
        super().__init__(provider_name="mock_test_fixture")

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        query_lower = query.lower()
        results: List[SearchResult] = []

        for key, mapped_results in self.KNOWN_URL_MAPPINGS.items():
            if key in query_lower:
                results.extend(mapped_results)

        if not results:
            first_word = query.split()[0] if query else "app"
            results.append(
                SearchResult(
                    title=f"{first_word.capitalize()} Documentation",
                    url=f"https://docs.{first_word.lower()}.com",
                    snippet=f"Documentation reference for {first_word}.",
                    source_domain=f"docs.{first_word.lower()}.com",
                    retrieval_timestamp=datetime.now(timezone.utc),
                    provider="mock_test_fixture",
                    rank=1,
                    source_query=query,
                )
            )

        return results[:max_results]


def get_search_provider(mode: str = "production") -> BaseSearchProvider:
    """Factory returning configured live search provider or reporting SEARCH_UNAVAILABLE.

    Args:
        mode: "production" or "test". Only "test" allows MockSearchProvider.
    """
    if mode == "test":
        return MockSearchProvider()

    settings = get_settings()

    # Check Tavily
    tavily_key = settings.tavily_api_key or os.getenv("TAVILY_API_KEY")
    if tavily_key:
        logger.info("Initializing live TavilySearchProvider.")
        return TavilySearchProvider(api_key=tavily_key)

    # Check Serper
    serper_key = settings.serper_api_key or os.getenv("SERPER_API_KEY")
    if serper_key:
        logger.info("Initializing live SerperSearchProvider.")
        return SerperSearchProvider(api_key=serper_key)

    logger.warning("No search API credentials found. Returning UnavailableSearchProvider (SEARCH_UNAVAILABLE).")
    return UnavailableSearchProvider()
