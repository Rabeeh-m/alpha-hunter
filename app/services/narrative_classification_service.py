from __future__ import annotations

from decimal import Decimal

from app.collectors.anthropic_client import AnthropicClassifierClient
from app.core.logging import get_logger
from app.models.token import Token
from app.repositories.narrative_repository import NarrativeRepository

log = get_logger(__name__)


class NarrativeClassificationService:
    """Unlike WalletDiscoveryService/ContractSecurityService/
    SocialIntelligenceService, this is designed to run ONCE per token,
    not repeatedly. See NarrativeClassification model docstring."""

    def __init__(self, client: AnthropicClassifierClient, repository: NarrativeRepository) -> None:
        self._client = client
        self._repository = repository

    async def classify_token(self, token: Token) -> None:
        result = await self._client.classify(token.symbol, token.name, token.dex)
        await self._repository.upsert(
            token.id, result.primary_narrative, Decimal(str(result.confidence)), result.reasoning
        )

    async def classify_unclassified_batch(self, limit: int = 20) -> dict[str, int]:
        """Backs the scheduled job -- classifies up to `limit` never-
        classified tokens per run, clearing the backlog gradually
        rather than in one large burst of LLM calls."""
        tokens = await self._repository.list_unclassified_tokens(limit=limit)
        classified, failed = 0, 0
        for token in tokens:
            try:
                await self.classify_token(token)
                classified += 1
            except ValueError as exc:
                # Malformed LLM response for ONE token must not abort
                # the whole batch -- log and continue, same "one failure
                # doesn't stop the batch" principle as every collector
                # loop since M3.
                log.warning(
                    "narrative_classification_failed", token_id=str(token.id), error=str(exc)
                )
                failed += 1
        return {"classified": classified, "failed": failed}
