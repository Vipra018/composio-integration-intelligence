"""Documentation discovery service for locating developer resources."""

from __future__ import annotations

from typing import List, Optional, Tuple
from urllib.parse import urlparse

from src.exceptions import SearchUnavailableError
from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata
from src.research.search_provider import BaseSearchProvider, get_search_provider

logger = get_logger("research.documentation_discovery")


class DocumentationDiscovery:
    """Discovers official documentation, auth guides, API references, and MCP resources."""

    def __init__(self, search_provider: Optional[BaseSearchProvider] = None, mode: str = "production") -> None:
        self.search_provider = search_provider or get_search_provider(mode=mode)
        self.last_search_status: str = "INITIALIZED"

    def discover_candidate_urls(self, app: AppMetadata) -> List[str]:
        """Discover and rank candidate documentation URLs for an application.

        Priority order:
        1. developer_documentation_url (if already explicitly populated)
        2. original_source_hint (if it points to docs, developer portal, or repo)
        3. Search results from live queries (if live search is available)
        4. Derived standard developer subdomains (e.g. docs.domain.com, developer.domain.com)

        Args:
            app: AppMetadata to discover documentation for.

        Returns:
            Ranked list of distinct candidate URLs.
        """
        candidates: List[str] = []

        # 1. Explicit developer doc URL
        if app.developer_documentation_url:
            candidates.append(str(app.developer_documentation_url))

        # 2. Original source hint if applicable
        hint = app.original_source_hint.strip()
        if hint.startswith("http://") or hint.startswith("https://"):
            if "docs" in hint or "developer" in hint or "api" in hint or "github.com" in hint:
                candidates.append(hint)
            elif not candidates:
                candidates.append(hint)

        # 3. Live search queries (if live search provider is configured)
        try:
            queries = self.search_provider.generate_queries(app)
            for q in queries:
                search_results = self.search_provider.search(q.query, max_results=3)
                for res in search_results:
                    if res.url not in candidates:
                        candidates.append(res.url)
            self.last_search_status = f"LIVE_{self.search_provider.provider_name.upper()}"
        except SearchUnavailableError as e:
            logger.info("Search engine unavailable (%s); proceeding with canonical hints and developer domains.", e)
            self.last_search_status = "SEARCH_UNAVAILABLE"
        except Exception as e:
            logger.warning("Search query execution failed: %s; relying on canonical hints.", e)
            self.last_search_status = f"SEARCH_FAILED: {e}"

        # 4. Standard developer subdomains derived from canonical website
        website = str(app.website)
        parsed = urlparse(website)
        domain = parsed.netloc or parsed.path
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            base_domain = ".".join(domain_parts[-2:])
            candidates.append(f"https://developer.{base_domain}")
            candidates.append(f"https://docs.{base_domain}")

        # Deduplicate while preserving priority order
        seen = set()
        unique_candidates: List[str] = []
        for url in candidates:
            normalized = url.rstrip("/")
            if normalized not in seen:
                seen.add(normalized)
                unique_candidates.append(url)

        logger.debug("Discovered %d candidate URLs for app %s", len(unique_candidates), app.app_id)
        return unique_candidates
