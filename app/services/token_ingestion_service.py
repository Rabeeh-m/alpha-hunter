from __future__ import annotations

from app.collectors.base import TokenProvider
from app.core.logging import get_logger
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository

log = get_logger(__name__)


class TokenIngestionService:
    """Orchestrates ingestion across any number of TokenProviders, and
    records a historical snapshot of each token right after it's upserted.

    Snapshot-per-ingestion-cycle is a deliberate choice over
    snapshot-per-API-read: reads should be fast and side-effect-free;
    writing history is a job-time concern, tied to the same cadence as
    the scheduler (currently 90s per collector -- see M5A).
    """

    def __init__(
        self,
        providers: list[TokenProvider],
        repository: TokenRepository,
        snapshot_repository: TokenSnapshotRepository,
    ) -> None:
        self._providers = providers
        self._repository = repository
        self._snapshot_repository = snapshot_repository

    async def ingest_all(self) -> dict[str, int]:
        results: dict[str, int] = {}
        for provider in self._providers:
            tokens = await provider.fetch_latest_tokens()
            for token_data in tokens:
                saved_token = await self._repository.upsert(token_data)
                await self._snapshot_repository.add_snapshot(saved_token)
            results[provider.name] = len(tokens)
            log.info("provider_ingestion_complete", provider=provider.name, count=len(tokens))
        return results