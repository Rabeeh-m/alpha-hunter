from __future__ import annotations

from app.collectors.dexscreener_client import DexScreenerClient
from app.collectors.dexscreener_normalizer import normalize_pair
from app.core.logging import get_logger
from app.repositories.token_repository import TokenRepository

log = get_logger(__name__)


class TokenIngestionService:
    """Orchestrates: fetch latest profiles -> fetch pairs -> normalize -> upsert.
    This is the only place that knows the full ingestion workflow; the
    collector and repository each know only their own narrow job."""

    def __init__(self, client: DexScreenerClient, repository: TokenRepository) -> None:
        self._client = client
        self._repository = repository

    async def ingest_latest_tokens(self) -> int:
        profiles = await self._client.get_latest_token_profiles()
        ingested = 0

        for profile in profiles:
            pairs = await self._client.get_pairs_for_token(
                profile.chain_id, profile.token_address
            )
            for pair in pairs:
                token_data = normalize_pair(pair)
                if token_data is None:
                    continue
                await self._repository.upsert(token_data)
                ingested += 1

        log.info("token_ingestion_complete", ingested=ingested, profiles_seen=len(profiles))
        return ingested