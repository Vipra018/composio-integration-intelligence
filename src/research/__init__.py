"""Research and intelligence gathering pipeline modules."""

from src.research.document_fetcher import DocumentFetcher, FetchedDocument
from src.research.documentation_discovery import DocumentationDiscovery
from src.research.evidence_extractor import EvidenceExtractor
from src.research.research_classifier import ResearchClassifier
from src.research.search_provider import BaseSearchProvider, SearchQuery, SearchResult

__all__ = [
    "BaseSearchProvider",
    "SearchQuery",
    "SearchResult",
    "DocumentationDiscovery",
    "DocumentFetcher",
    "FetchedDocument",
    "EvidenceExtractor",
    "ResearchClassifier",
]
