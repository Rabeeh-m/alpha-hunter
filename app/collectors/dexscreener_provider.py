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
            links_by_type = {link.type: link.url for link in profile.links if link.type}
            pairs = await self._client.get_pairs_for_token(profile.chain_id, profile.token_address)
            for pair in pairs:
                token = normalize_pair(pair)
                if token is None:
                    continue
                token.telegram_url = links_by_type.get("telegram")
                token.twitter_handle = links_by_type.get("twitter")
                token.github_url = links_by_type.get("github")
                tokens.append(token)
        log.info("dexscreener_provider_fetched", count=len(tokens))
        return tokens
    
    async def close(self) -> None:
        await self._client.close()