"""Search query generation and provider interfaces."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata

logger = get_logger("research.search_provider")


@dataclass
class SearchResult:
    """Represents an individual search engine result."""

    title: str
    url: str
    snippet: str
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

    def __init__(self) -> None:
        self.executed_queries: List[SearchQuery] = []

    def generate_queries(self, app: AppMetadata) -> List[SearchQuery]:
        """Generate targeted search queries for all research dimensions.

        Args:
            app: Target application metadata.

        Returns:
            List of structured SearchQuery objects.
        """
        app_name = app.name
        queries = [
            # Authentication queries
            SearchQuery(
                query=f"{app_name} API authentication OAuth2 API key developer documentation",
                category="auth",
            ),
            # API Surface & documentation
            SearchQuery(
                query=f"{app_name} developer API documentation REST GraphQL endpoints",
                category="api",
            ),
            # Credential accessibility & pricing
            SearchQuery(
                query=f"{app_name} API access requirements developer account free tier paid enterprise",
                category="pricing",
            ),
            # MCP & Tooling availability
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


class MockSearchProvider(BaseSearchProvider):
    """Deterministic, sandbox-friendly search provider with pre-mapped references."""

    # Curated authoritative mappings for benchmark and pilot apps
    KNOWN_URL_MAPPINGS = {
        "salesforce": [
            SearchResult(
                title="Salesforce Developers: REST API Developer Guide",
                url="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm",
                snippet="Salesforce REST API provides powerful, convenient, and simple RESTful Web services interface. Requires OAuth 2.0 or Connected App. Developer Edition orgs are free.",
                rank=1,
                source_query="salesforce api",
            ),
            SearchResult(
                title="Salesforce Composio Integration Toolkit",
                url="https://composio.dev/tools/salesforce",
                snippet="Composio supports Salesforce with built-in OAuth2 authentication and actions for leads, contacts, and opportunities.",
                rank=2,
                source_query="salesforce composio",
            ),
        ],
        "github": [
            SearchResult(
                title="GitHub REST API Documentation",
                url="https://docs.github.com/en/rest",
                snippet="GitHub REST API allows creating integrations, retrieving data, and automating workflows. Supports Personal Access Tokens (PAT) and OAuth 2.0 apps. Self-serve free access.",
                rank=1,
                source_query="github api",
            ),
            SearchResult(
                title="GitHub Official Model Context Protocol (MCP) Server",
                url="https://github.com/modelcontextprotocol/servers/tree/main/src/github",
                snippet="Official reference MCP server for GitHub providing repositories, issues, pulls, and git operations. Available on Composio.",
                rank=2,
                source_query="github mcp",
            ),
        ],
        "shopify": [
            SearchResult(
                title="Shopify Dev: Admin API Overview",
                url="https://shopify.dev/docs/api/admin-rest",
                snippet="The Shopify Admin API lets you build apps and integrations for Shopify merchants. Supports OAuth 2.0 and Custom App access tokens. Free Partner accounts for app development.",
                rank=1,
                source_query="shopify api",
            ),
            SearchResult(
                title="Shopify Composio Agent Tool",
                url="https://composio.dev/tools/shopify",
                snippet="Integrate Shopify with AI agents using Composio's pre-built actions and triggers for products, orders, and customer management.",
                rank=2,
                source_query="shopify composio",
            ),
        ],
        "sherlock": [
            SearchResult(
                title="Sherlock Project: Hunt down social media accounts by username across social networks",
                url="https://github.com/sherlock-project/sherlock",
                snippet="Sherlock is an open-source Python command-line OSINT tool to hunt usernames across social platforms. Not a hosted SaaS platform; no official hosted REST API or OAuth authentication.",
                rank=1,
                source_query="sherlock osint",
            ),
        ],
        "notebooklm": [
            SearchResult(
                title="Google NotebookLM - Personalized AI Research Assistant",
                url="https://notebooklm.google.com",
                snippet="NotebookLM is an experimental web application from Google Labs powered by Gemini. As of 2024-2025, NotebookLM does not offer a public developer REST API, OAuth scopes, or public SDK.",
                rank=1,
                source_query="notebooklm api",
            ),
        ],
    }

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Return curated results or fallback heuristic results."""
        sq = SearchQuery(
            query=query,
            category="general",
            executed=True,
            executed_at=datetime.now(timezone.utc),
        )

        query_lower = query.lower()
        results: List[SearchResult] = []

        for key, mapped_results in self.KNOWN_URL_MAPPINGS.items():
            if key in query_lower:
                results.extend(mapped_results)

        # Fallback dynamic result if no direct known mapping
        if not results:
            first_word = query.split()[0] if query else "app"
            results.append(
                SearchResult(
                    title=f"{first_word.capitalize()} Developer Documentation & API Reference",
                    url=f"https://developer.{first_word.lower()}.com/docs",
                    snippet=f"Official API reference and developer guides for {first_word}.",
                    rank=1,
                    source_query=query,
                )
            )

        trimmed = results[:max_results]
        sq.results_count = len(trimmed)
        self.executed_queries.append(sq)
        return trimmed
