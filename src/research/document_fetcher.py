"""Production HTTP document fetching with full provenance, redirect tracking, and HTML sanitization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from src.logging_utils import get_logger
from src.models.enums import Provenance

logger = get_logger("research.document_fetcher")


@dataclass
class FetchedDocument:
    """Detailed audit record of an attempted or completed document retrieval."""

    requested_url: str = ""
    final_url: str = ""
    status_code: int = 200
    retrieval_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    content_type: str = "text/html"
    is_success: bool = True
    source_domain: str = ""
    title: str = ""
    text_content: str = ""
    content_length: int = 0
    failure_reason: Optional[str] = None
    meta_description: str = ""
    provenance: Provenance = Provenance.LIVE_FETCHED

    def __init__(
        self,
        requested_url: str = "",
        final_url: str = "",
        status_code: int = 200,
        retrieval_timestamp: Optional[datetime] = None,
        content_type: str = "text/html",
        is_success: bool = True,
        source_domain: str = "",
        title: str = "",
        text_content: str = "",
        content_length: int = 0,
        failure_reason: Optional[str] = None,
        meta_description: str = "",
        provenance: Provenance = Provenance.LIVE_FETCHED,
        url: Optional[str] = None,
        fetched_at: Optional[datetime] = None,
    ) -> None:
        if url:
            requested_url = requested_url or url
            final_url = final_url or url
            if not source_domain:
                source_domain = urlparse(url).netloc or ""

        self.requested_url = requested_url
        self.final_url = final_url
        self.status_code = status_code
        self.retrieval_timestamp = retrieval_timestamp or fetched_at or datetime.now(timezone.utc)
        self.content_type = content_type
        self.is_success = is_success
        self.source_domain = source_domain
        self.title = title
        self.text_content = text_content
        self.content_length = content_length or len(text_content)
        self.failure_reason = failure_reason
        self.meta_description = meta_description
        self.provenance = provenance

    @property
    def url(self) -> str:
        """Alias for backward compatibility."""
        return self.final_url or self.requested_url



class DocumentFetcher:
    """Production HTTP fetcher enforcing real network retrieval and strict audit provenance."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 (IntegrationIntelligence/2.0; +https://composio.dev)"

    # Unit-test only fixtures - STRICTLY FOR ISOLATED OFFLINE UNIT TESTS
    TEST_MOCK_KNOWLEDGE_BASE: Dict[str, dict] = {
        "developer.salesforce.com": {
            "title": "Salesforce REST API Developer Guide",
            "text": "Salesforce REST API Overview: The REST API provides a powerful, convenient, and simple RESTful Web services interface. Authentication is handled via OAuth 2.0 Web Server Flow or JWT Bearer Flow using Connected Apps. API access requires an Enterprise, Unlimited, or Performance Edition, or a free Developer Edition org.",
        },
        "docs.github.com": {
            "title": "GitHub REST API Documentation",
            "text": "GitHub REST API: Create integrations, retrieve data, and automate your workflows with GitHub's REST API. Authenticate with a personal access token (classic or fine-grained), or with a GitHub App using OAuth 2.0. API is available to all users with self-serve free accounts. GitHub also offers a comprehensive GraphQL API (v4). Rate limits: 5,000 requests per hour.",
        },
        "shopify.dev": {
            "title": "Shopify Admin API Documentation",
            "text": "The Shopify Admin API lets you build apps and integrations for merchants. The Admin API is available in REST and GraphQL. Authentication requires OAuth 2.0 access tokens. Developers can create a free Shopify Partner account to create unlimited development stores for testing with full Admin API access. Standard API rate limits use a leaky-bucket algorithm with 40 requests/bucket, refill 2/second.",
        },
        "github.com/sherlock-project": {
            "title": "sherlock-project/sherlock: Hunt down social media accounts by username across social networks",
            "text": "Sherlock is a command-line tool written in Python. It does not provide a cloud SaaS platform, does not provide a hosted REST API, and does not require OAuth or API keys. Integration with AI agents requires running the CLI as a subprocess or importing the Python package locally rather than invoking a SaaS API.",
        },
        "notebooklm.google.com": {
            "title": "NotebookLM - Google's AI-First Notebook",
            "text": "NotebookLM is an experimental personalized AI collaborator developed by Google Labs. Current developer status: Google has not released a public developer REST API, public SDK, or OAuth developer scopes for NotebookLM. Access is strictly end-user facing through the web UI using Google Accounts. There is no official or third-party MCP server or public API endpoint available.",
        },
    }

    def __init__(
        self,
        timeout: float = 15.0,
        allow_mock_kb: bool = False,
        max_redirects: int = 5,
    ) -> None:
        """Initialize document fetcher.

        Args:
            timeout: Network request timeout in seconds.
            allow_mock_kb: ONLY set to True in isolated offline unit tests. Defaults to False.
            max_redirects: Maximum number of HTTP redirects to follow.
        """
        self.timeout = timeout
        self.allow_mock_kb = allow_mock_kb
        self.max_redirects = max_redirects

    def _extract_clean_text(self, html: str) -> tuple[str, str, str]:
        """Sanitize HTML by stripping navigation, styles, scripts, and chrome."""
        soup = BeautifulSoup(html, "html.parser")

        # Strip non-substantive markup
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "svg", "form", "iframe"]):
            element.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta_tag and meta_tag.get("content"):
            meta_desc = str(meta_tag["content"]).strip()

        # Extract text and collapse multiple whitespace
        text = soup.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        return title, meta_desc, text

    def fetch(self, url: str) -> FetchedDocument:
        """Execute genuine HTTP retrieval and record complete provenance metadata.

        Args:
            url: The requested target URL.

        Returns:
            FetchedDocument with verifiable status code, content type, and text.
        """
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        # Test-only short-circuit: ONLY allowed when explicitly constructed with allow_mock_kb=True
        if self.allow_mock_kb:
            for pattern, fixture in self.TEST_MOCK_KNOWLEDGE_BASE.items():
                if pattern in url:
                    logger.warning("Serving TEST MOCK knowledge base fixture for %s (allow_mock_kb=True)", url)
                    return FetchedDocument(
                        requested_url=url,
                        final_url=url,
                        status_code=200,
                        retrieval_timestamp=datetime.now(timezone.utc),
                        content_type="text/html; charset=utf-8",
                        is_success=True,
                        source_domain=domain,
                        title=fixture["title"],
                        text_content=fixture["text"],
                        content_length=len(fixture["text"]),
                        failure_reason=None,
                        meta_description="Test mock fixture",
                        provenance=Provenance.KNOWLEDGE_BASE,
                    )

        now = datetime.now(timezone.utc)

        # Production live retrieval
        try:
            with httpx.Client(
                headers={"User-Agent": self.USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"},
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects,
            ) as client:
                response = client.get(url)
                final_url = str(response.url)
                status_code = response.status_code
                content_type = response.headers.get("content-type", "")

                if status_code == 200:
                    title, meta_desc, clean_text = self._extract_clean_text(response.text)
                    if not title:
                        title = f"Documentation: {domain}"

                    logger.debug("Successfully fetched %s (status 200, %d chars)", final_url, len(clean_text))
                    return FetchedDocument(
                        requested_url=url,
                        final_url=final_url,
                        status_code=200,
                        retrieval_timestamp=now,
                        content_type=content_type,
                        is_success=True,
                        source_domain=domain,
                        title=title,
                        text_content=clean_text[:15000],  # Cap at 15k chars for prompt/processing efficiency
                        content_length=len(clean_text),
                        failure_reason=None,
                        meta_description=meta_desc,
                        provenance=Provenance.LIVE_FETCHED,
                    )
                else:
                    logger.warning("Live fetch HTTP error %d for URL %s", status_code, url)
                    return FetchedDocument(
                        requested_url=url,
                        final_url=final_url,
                        status_code=status_code,
                        retrieval_timestamp=now,
                        content_type=content_type,
                        is_success=False,
                        source_domain=domain,
                        title=f"HTTP {status_code} Error",
                        text_content="",
                        content_length=0,
                        failure_reason=f"HTTP {status_code}: {response.reason_phrase}",
                        provenance=Provenance.LIVE_FETCHED,
                    )

        except httpx.TimeoutException as e:
            logger.warning("Connection timeout for %s: %s", url, e)
            return FetchedDocument(
                requested_url=url,
                final_url=url,
                status_code=0,
                retrieval_timestamp=now,
                content_type="",
                is_success=False,
                source_domain=domain,
                title="Timeout Error",
                text_content="",
                content_length=0,
                failure_reason=f"Connection timed out after {self.timeout}s: {e}",
                provenance=Provenance.UNKNOWN,
            )
        except Exception as e:
            logger.warning("Network retrieval failed for %s: %s", url, e)
            return FetchedDocument(
                requested_url=url,
                final_url=url,
                status_code=0,
                retrieval_timestamp=now,
                content_type="",
                is_success=False,
                source_domain=domain,
                title="Network Error",
                text_content="",
                content_length=0,
                failure_reason=f"Network error: {e}",
                provenance=Provenance.UNKNOWN,
            )
