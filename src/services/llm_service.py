"""LLM service abstractions and provider implementations with rule-based fallback."""

from __future__ import annotations

import abc
import json
from typing import Any, Dict, Optional

from src.config import get_settings
from src.exceptions import LLMServiceError
from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata

logger = get_logger("services.llm_service")


class BaseLLMService(abc.ABC):
    """Abstract base class for LLM research extraction services."""

    @abc.abstractmethod
    def extract_research(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Execute prompt against LLM and return structured parsed JSON response."""
        pass


class OpenAILLMService(BaseLLMService):
    """OpenAI API integration for structured research extraction."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def extract_research(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as e:
            logger.error("OpenAI API extraction failed: %s", e)
            raise LLMServiceError(f"OpenAI service failed: {e}") from e


class RuleBasedFallbackService(BaseLLMService):
    """Deterministic fallback service when no external API keys are configured."""

    def extract_research(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        logger.debug("RuleBasedFallbackService active (offline/local mode).")
        return {"mode": "deterministic_fallback"}


def get_llm_service() -> BaseLLMService:
    """Factory function returning the configured LLM provider or fallback service."""
    settings = get_settings()

    if settings.openai_api_key:
        logger.info("Initializing OpenAILLMService with model %s", settings.llm_model)
        return OpenAILLMService(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
        )

    logger.info("No active LLM API key detected. Utilizing RuleBasedFallbackService.")
    return RuleBasedFallbackService()
