"""Autonomous researcher agent for investigating individual SaaS applications."""

from __future__ import annotations

from typing import List, Optional

from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata
from src.models.research import AppResearchResult
from src.research.document_fetcher import DocumentFetcher, FetchedDocument
from src.research.documentation_discovery import DocumentationDiscovery
from src.research.evidence_extractor import EvidenceExtractor
from src.research.research_classifier import ResearchClassifier
from src.research.search_provider import BaseSearchProvider, get_search_provider
from src.services.llm_service import BaseLLMService, get_llm_service

logger = get_logger("agents.researcher")


class AppResearcher:
    """Investigates a single SaaS application with live retrieval and verified provenance."""

    def __init__(
        self,
        search_provider: Optional[BaseSearchProvider] = None,
        doc_fetcher: Optional[DocumentFetcher] = None,
        evidence_extractor: Optional[EvidenceExtractor] = None,
        classifier: Optional[ResearchClassifier] = None,
        llm_service: Optional[BaseLLMService] = None,
        mode: str = "production",
    ) -> None:
        self.mode = mode
        self.search_provider = search_provider or get_search_provider(mode=mode)
        self.doc_discovery = DocumentationDiscovery(self.search_provider, mode=mode)
        # Production mode strictly prohibits mock knowledge base fixtures
        self.doc_fetcher = doc_fetcher or DocumentFetcher(allow_mock_kb=(mode == "test"))
        self.evidence_extractor = evidence_extractor or EvidenceExtractor()
        self.classifier = classifier or ResearchClassifier()
        self.llm_service = llm_service or get_llm_service()

    def research(self, app: AppMetadata) -> AppResearchResult:
        """Execute full research pipeline for a single application.

        Args:
            app: Application metadata.

        Returns:
            AppResearchResult with verified evidence and feasibility scores.
        """
        logger.info("Starting research for application: %s (%s)", app.name, app.app_id)

        # 1. Discover documentation and reference URLs
        candidate_urls = self.doc_discovery.discover_candidate_urls(app)
        logger.debug("Discovered %d candidate URLs for %s", len(candidate_urls), app.name)

        # 2. Fetch documents via live HTTP
        fetched_docs: List[FetchedDocument] = []
        for url in candidate_urls[:4]:  # Top 4 candidate URLs
            doc = self.doc_fetcher.fetch(url)
            fetched_docs.append(doc)

        successful_docs = [d for d in fetched_docs if d.is_success]
        logger.info(
            "Fetched %d/%d documents successfully for %s",
            len(successful_docs),
            len(fetched_docs),
            app.name,
        )

        aggregated_text = "\n\n".join([f"[{d.title} ({d.url})]: {d.text_content}" for d in successful_docs])

        # 3. Extract evidence citations with polarity checking
        evidence = self.evidence_extractor.extract_evidence(fetched_docs)
        logger.debug("Extracted %d evidence items for %s", len(evidence), app.name)

        # 4. Classify and evaluate integration feasibility
        result = self.classifier.classify(
            app=app,
            evidence=evidence,
            full_text=aggregated_text,
            search_status=self.doc_discovery.last_search_status,
        )

        logger.info(
            "Completed research for %s. Score: %.1f/10, Buildability: %s",
            app.name,
            result.feasibility.feasibility_score,
            result.feasibility.buildability.value,
        )
        return result
