from __future__ import annotations

import httpx

from app.collectors.geckoterminal_client import SUPPORTED_NETWORKS, GeckoTerminalClient
from app.collectors.geckoterminal_normalizer import normalize_pool
from app.core.logging import get_logger
from app.schemas.token import TokenCreate

log = get_logger(__name__)


class GeckoTerminalProvider:
    name = "geckoterminal"

    def __init__(self, client: GeckoTerminalClient | None = None) -> None:
        self._client = client or GeckoTerminalClient()

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        tokens: list[TokenCreate] = []
        for network in SUPPORTED_NETWORKS:
            try:
                pools = await self._client.get_new_pools(network)
                tokens.extend(
                    t for pool in pools if (t := normalize_pool(pool, network)) is not None
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    log.error(
                        "geckoterminal_provider_rate_limited",
                        network=network,
                        error=str(e),
                    )
                    continue
                raise
        log.info("geckoterminal_provider_fetched", count=len(tokens))
        return tokens

    async def close(self) -> None:
        await self._client.close()
