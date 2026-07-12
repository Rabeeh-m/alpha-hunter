from __future__ import annotations

from app.collectors.dexscreener_client import DexScreenerClient
from app.collectors.dexscreener_normalizer import normalize_pair
from app.core.logging import get_logger
from app.schemas.token import TokenCreate

log = get_logger(__name__)


class DexScreenerProvider:
    name = "dexscreener"

    def __init__(self, client: DexScreenerClient | None = None) -> None:
        self._client = client or DexScreenerClient()

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        profiles = await self._client.get_latest_token_profiles()
        tokens: list[TokenCreate] = []
        for profile in profiles:
            pairs = await self._client.get_pairs_for_token(profile.chain_id, profile.token_address)
            tokens.extend(t for pair in pairs if (t := normalize_pair(pair)) is not None)
        log.info("dexscreener_provider_fetched", count=len(tokens))
        return tokens

    async def close(self) -> None:
        await self._client.close()