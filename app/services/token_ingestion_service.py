from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.collectors.base import TokenProvider
    from app.repositories.token_repository import TokenRepository
    from app.repositories.token_snapshot_repository import TokenSnapshotRepository

log = get_logger(__name__)

_MIN_LIQUIDITY_USD = 10
_MIN_VOLUME_USD = 10


class TokenIngestionService:
    """Orchestrates ingestion across any number of TokenProviders, and
    records a historical snapshot of each token right after it's upserted.

    Snapshot-per-ingestion-cycle is a deliberate choice over
    snapshot-per-API-read: reads should be fast and side-effect-free;
    writing history is a job-time concern, tied to the same cadence as
    the scheduler (currently 90s per collector -- see M5A).

    Quality gate: tokens with less than $_MIN_LIQUIDITY_USD AND less than
    $_MIN_VOLUME_USD are skipped. The DexScreener / GeckoTerminal new-token
    firehose is ~99% mint-and-dump junk; this filter drops tokens that have
    never seen a single real trade.
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
            ingested = 0
            skipped = 0
            for token_data in tokens:
                if not self._passes_quality_gate(token_data):
                    skipped += 1
                    continue
                saved_token = await self._repository.upsert(token_data)
                await self._snapshot_repository.add_snapshot(saved_token)
                ingested += 1
            results[provider.name] = ingested
            log.info(
                "provider_ingestion_complete",
                provider=provider.name,
                count=ingested,
                skipped=skipped,
            )
        return results

    @staticmethod
    def _passes_quality_gate(token_data: object) -> bool:
        liquidity = getattr(token_data, "liquidity_usd", None)
        volume = getattr(token_data, "volume_24h_usd", None)
        has_liquidity = liquidity is not None and liquidity >= _MIN_LIQUIDITY_USD
        has_volume = volume is not None and volume >= _MIN_VOLUME_USD
        return has_liquidity or has_volume
