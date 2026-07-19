from __future__ import annotations

from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.narratives.classifier_prompt import (
    SYSTEM_PROMPT,
    NarrativeClassificationResult,
    build_user_prompt,
    parse_classification_response,
)

log = get_logger(__name__)

# Haiku, not Sonnet/Opus -- this is a simple categorization task from
# ~15 words of input. Spending a frontier-model call on it would be
# real, unnecessary cost at any meaningful token-scanning volume.
MODEL = "claude-haiku-4-5-20251001"


class AnthropicClassifierClient:
    def __init__(self) -> None:
        settings = get_settings()
        api_key = (
            settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
        )
        self._client = AsyncAnthropic(api_key=api_key)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True,
    )
    async def classify(
        self, symbol: str, name: str, dex: str | None
    ) -> NarrativeClassificationResult:
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(symbol, name, dex)}],
        )
        text_block = next((b for b in response.content if b.type == "text"), None)
        if text_block is None:
            raise ValueError("LLM response contained no text content")

        result = parse_classification_response(text_block.text)
        log.info(
            "narrative_classified",
            symbol=symbol,
            narrative=result.primary_narrative.value,
            confidence=result.confidence,
        )
        return result
