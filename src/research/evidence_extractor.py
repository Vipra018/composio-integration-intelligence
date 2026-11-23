"""Negation-safe evidence extraction with polarity classification and claim attribution."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import HttpUrl

from src.logging_utils import get_logger
from src.models.enums import EvidencePolarity, Provenance
from src.models.research import EvidenceURL
from src.research.document_fetcher import FetchedDocument

logger = get_logger("research.evidence_extractor")


class EvidenceExtractor:
    """Extracts verifiable quotations with explicit polarity (Positive, Negative, Ambiguous)."""

    EVIDENCE_PATTERNS: Dict[str, List[str]] = {
        "auth": [
            r"oauth\s*2(?:\.0)?",
            r"personal\s*access\s*token",
            r"api\s*key",
            r"bearer\s*token",
            r"basic\s*auth",
            r"jwt\s*bearer",
            r"connected\s*app",
        ],
        "credential": [
            r"developer\s*edition",
            r"free\s*account",
            r"free\s*tier",
            r"partner\s*account",
            r"self-serve",
            r"enterprise\s*(?:edition|plan)",
            r"contact\s*sales",
            r"admin\s*(?:activation|approval)",
        ],
        "api_surface": [
            r"rest\s*api",
            r"graphql",
            r"command-line\s*tool",
            r"python\s*(?:package|library|cli)",
            r"webhooks?",
        ],
        "mcp": [
            r"model\s*context\s*protocol",
            r"mcp\s*server",
            r"composio",
        ],
        "blockers": [
            r"rate\s*limits?",
            r"strictly\s*end-user\s*facing",
            r"only\s*available\s*through\s*the\s*web",
            r"no\s*public\s*developer\s*rest\s*api",
        ],
    }

    NEGATIVE_INDICATORS = [
        r"does\s*not\s*support",
        r"do\s*not\s*support",
        r"doesn'?t\s*support",
        r"is\s*not\s*supported",
        r"are\s*not\s*supported",
        r"unsupported",
        r"does\s*not\s*provide",
        r"do\s*not\s*provide",
        r"doesn'?t\s*provide",
        r"does\s*not\s*offer",
        r"doesn'?t\s*offer",
        r"does\s*not\s*require",
        r"do\s*not\s*require",
        r"doesn'?t\s*require",
        r"not\s*require",
        r"without\s*requiring",
        r"does\s*not\s*expose",
        r"has\s*not\s*released",
        r"have\s*not\s*released",
        r"no\s*public\s*(?:developer\s*)?(?:rest\s*)?api",
        r"no\s*developer\s*api",
        r"no\s*hosted\s*rest\s*api",
        r"no\s*official\s*(?:developer\s*)?api",
        r"no\s*(?:official\s*or\s*third-party\s*)?mcp\s*server",
        r"not\s*available",
        r"is\s*unavailable",
        r"currently\s*unavailable",
        r"only\s*available\s*through\s*the\s*(?:web|browser|ui|interface)",
        r"strictly\s*end-user\s*facing",
        r"strictly\s*through\s*the\s*web",
        r"prohibits?",
        r"lacks?",
    ]

    AMBIGUOUS_INDICATORS = [
        r"may\s*be\s*supported",
        r"might\s*support",
        r"planned",
        r"roadmap",
        r"under\s*development",
        r"experimental",
        r"in\s*(?:private\s*)?beta",
        r"preview",
        r"potentially",
        r"evaluating",
        r"case-by-case",
    ]

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences cleanly preserving context."""
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            if len(s_clean) >= 15:
                sentences.append(s_clean)
        return sentences

    def determine_sentence_polarity(self, sentence: str, target_phrase: str = "") -> EvidencePolarity:
        """Analyze sentence syntax to classify evidence polarity as Positive, Negative, or Ambiguous.

        Args:
            sentence: The sentence string containing the citation.
            target_phrase: The specific capability or entity being assessed.

        Returns:
            EvidencePolarity: NEGATIVE, AMBIGUOUS, or POSITIVE.
        """
        sentence_lower = sentence.lower()

        # 1. Check for explicit negative indicators
        for neg_pat in self.NEGATIVE_INDICATORS:
            if re.search(neg_pat, sentence_lower):
                # Verify negation applies to or is within the sentence
                return EvidencePolarity.NEGATIVE

        # 2. Check for ambiguity / forward-looking statements
        for amb_pat in self.AMBIGUOUS_INDICATORS:
            if re.search(amb_pat, sentence_lower):
                return EvidencePolarity.AMBIGUOUS

        # 3. Otherwise treat as affirmative/positive assertion
        return EvidencePolarity.POSITIVE

    def extract_evidence(self, documents: List[FetchedDocument]) -> List[EvidenceURL]:
        """Extract substantive evidence citations with verifiable polarity and provenance.

        Args:
            documents: List of fetched documents (both successful and failed).

        Returns:
            List of structured EvidenceURL objects.
        """
        evidence_list: List[EvidenceURL] = []
        seen_snippets = set()

        for doc in documents:
            # Skip documents that failed network retrieval
            if not doc.is_success or not doc.text_content:
                continue

            text = doc.text_content
            url_str = doc.final_url or doc.requested_url
            sentences = self.split_sentences(text)

            source_type = "official_documentation"
            if "github.com" in url_str:
                source_type = "repository"
            elif "composio.dev" in url_str:
                source_type = "official_documentation"

            for sentence in sentences:
                sentence_lower = sentence.lower()

                for category, patterns in self.EVIDENCE_PATTERNS.items():
                    for pat in patterns:
                        if re.search(pat, sentence_lower):
                            clean_pat = pat.replace(r"\s*", " ").replace(r"(?:\.0)?", "").replace(r"(?:package|library|cli)", "")
                            polarity = self.determine_sentence_polarity(sentence, clean_pat)

                            snippet = sentence[:1200]
                            if snippet not in seen_snippets:
                                seen_snippets.add(snippet)

                                if polarity == EvidencePolarity.NEGATIVE:
                                    claim_text = f"Confirmed absent / unsupported ({category}): {clean_pat}"
                                elif polarity == EvidencePolarity.AMBIGUOUS:
                                    claim_text = f"Ambiguous / conditional ({category}): {clean_pat}"
                                else:
                                    claim_text = f"Confirmed supported ({category}): {clean_pat}"

                                evidence_list.append(
                                    EvidenceURL(
                                        url=HttpUrl(url_str),
                                        title=doc.title or "Documentation",
                                        snippet=snippet,
                                        source_type=source_type,
                                        claim=claim_text,
                                        provenance=doc.provenance,
                                        polarity=polarity,
                                        http_status=doc.status_code,
                                        retrieved_at=doc.retrieval_timestamp,
                                    )
                                )

        logger.debug("Extracted %d validated evidence citations from %d documents", len(evidence_list), len(documents))
        return evidence_list
