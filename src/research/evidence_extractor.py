"""Evidence extractor for harvesting verifiable textual citations and claims."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from pydantic import HttpUrl

from src.logging_utils import get_logger
from src.models.research import EvidenceURL
from src.research.document_fetcher import FetchedDocument

logger = get_logger("research.evidence_extractor")


class EvidenceExtractor:
    """Extracts verifiable quotes, claims, and URLs from fetched documentation."""

    EVIDENCE_PATTERNS = {
        "auth": [
            r"oauth\s*2(?:\.0)?",
            r"personal\s*access\s*token",
            r"api\s*key",
            r"bearer\s*token",
            r"basic\s*auth",
            r"jwt\s*bearer",
            r"connected\s*app",
            r"no\s*official\s*hosted\s*rest\s*api\s*or\s*oauth",
        ],
        "credential": [
            r"developer\s*edition",
            r"free\s*account",
            r"free\s*tier",
            r"free\s*partner\s*account",
            r"self-serve",
            r"enterprise\s*(?:edition|plan)",
            r"contact\s*sales",
            r"admin\s*activation",
            r"no\s*public\s*developer\s*rest\s*api",
        ],
        "api_surface": [
            r"rest\s*api",
            r"graphql",
            r"command-line\s*tool",
            r"python\s*(?:package|library)",
            r"no\s*developer\s*rest\s*api",
            r"no\s*hosted\s*rest\s*api",
            r"web\s*application",
        ],
        "mcp": [
            r"model\s*context\s*protocol",
            r"mcp\s*server",
            r"composio",
        ],
        "blockers": [
            r"enterprise.*required",
            r"no\s*public\s*developer\s*rest\s*api",
            r"not\s*a\s*cloud\s*saas\s*platform",
            r"rate\s*limits",
            r"strictly\s*end-user\s*facing",
        ],
    }

    def _extract_sentences_matching(self, text: str, pattern: str) -> List[str]:
        """Split text into sentences and return those containing the regex pattern."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        matches = []
        for s in sentences:
            if re.search(pattern, s, re.IGNORECASE):
                cleaned = s.strip()
                if 20 <= len(cleaned) <= 300:
                    matches.append(cleaned)
        return matches

    def extract_evidence(self, documents: List[FetchedDocument]) -> List[EvidenceURL]:
        """Extract substantive evidence citations from a collection of documents.

        Args:
            documents: List of fetched documents.

        Returns:
            List of structured EvidenceURL objects.
        """
        evidence_list: List[EvidenceURL] = []
        seen_excerpts = set()

        for doc in documents:
            text = doc.text_content
            url_str = doc.url

            source_type = "official_documentation"
            if "github.com" in url_str:
                source_type = "repository"
            elif "composio.dev" in url_str:
                source_type = "official_documentation"

            # Check each category of pattern
            for category, patterns in self.EVIDENCE_PATTERNS.items():
                for pat in patterns:
                    matched_sentences = self._extract_sentences_matching(text, pat)
                    for sentence in matched_sentences:
                        if sentence not in seen_excerpts:
                            seen_excerpts.add(sentence)
                            claim = f"Verified {category.replace('_', ' ')}: {pat.replace(r'\s*', ' ').replace(r'(?:\.0)?', '')}"
                            evidence_list.append(
                                EvidenceURL(
                                    url=HttpUrl(url_str),
                                    title=doc.title or "Documentation",
                                    snippet=sentence,
                                    source_type=source_type,
                                    claim=claim,
                                    retrieved_at=datetime.now(timezone.utc),
                                )
                            )

        logger.debug("Extracted %d evidence items from %d documents", len(evidence_list), len(documents))
        return evidence_list
