from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.cache import cache_get, cache_set
from app.core.logging import get_logger
from app.schemas.dexscreener import DexScreenerPair, DexScreenerTokenProfile

log = get_logger(__name__)

BASE_URL = "https://api.dexscreener.com"


class DexScreenerClient:
    """Thin HTTP client over DexScreener's public API. No business logic here —
    just fetch, cache, retry. Normalization happens elsewhere."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _get(self, path: str) -> dict | list:
        response = await self._client.get(path)
        response.raise_for_status()
        return response.json()

    async def get_latest_token_profiles(self) -> list[DexScreenerTokenProfile]:
        cache_key = "dexscreener:token-profiles:latest"
        cached = await cache_get(cache_key)
        if cached is not None:
            log.debug("dexscreener_cache_hit", key=cache_key)
            return [DexScreenerTokenProfile.model_validate(item) for item in cached]

        raw = await self._get("/token-profiles/latest/v1")
        await cache_set(cache_key, raw, ttl_seconds=60)
        log.info("dexscreener_fetched_profiles", count=len(raw))
        return [DexScreenerTokenProfile.model_validate(item) for item in raw]

    async def get_pairs_for_token(self, chain_id: str, token_address: str) -> list[DexScreenerPair]:
        cache_key = f"dexscreener:pairs:{chain_id}:{token_address}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return [DexScreenerPair.model_validate(item) for item in cached]

        raw = await self._get(f"/latest/dex/tokens/{token_address}")
        pairs = raw.get("pairs") or []
        await cache_set(cache_key, pairs, ttl_seconds=60)
        return [DexScreenerPair.model_validate(p) for p in pairs if p.get("chainId") == chain_id]

    async def close(self) -> None:
        await self._client.aclose()
