from __future__ import annotations

from app.collectors.base import TokenProvider
from app.core.logging import get_logger
from app.repositories.token_repository import TokenRepository

log = get_logger(__name__)


class TokenIngestionService:
    """Orchestrates ingestion across any number of TokenProviders.

    Deduplication is implicit: every provider's tokens flow through the
    same `TokenRepository.upsert()`, keyed on (chain, contract_address).
    A token discovered by two providers is upserted twice but persisted
    as exactly one row — the second write updates the first.
    """

    def __init__(self, providers: list[TokenProvider], repository: TokenRepository) -> None:
        self._providers = providers
        self._repository = repository

    async def ingest_all(self) -> dict[str, int]:
        results: dict[str, int] = {}
        for provider in self._providers:
            tokens = await provider.fetch_latest_tokens()
            for token in tokens:
                await self._repository.upsert(token)
            results[provider.name] = len(tokens)
            log.info("provider_ingestion_complete", provider=provider.name, count=len(tokens))
        return results