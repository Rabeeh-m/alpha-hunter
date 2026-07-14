from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.blockchain.chain_ids import ETHERSCAN_CHAIN_IDS
from app.core.cache import cache_get, cache_set
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chain import Chain
from app.schemas.etherscan import EtherscanTransfer

log = get_logger(__name__)

BASE_URL = "https://api.etherscan.io/v2/api"


class EtherscanClient:
    """Fetches ERC-20 transfer events via Etherscan's V2 multichain API.

    Free tier only -- uses `tokentx` (transfer log), NOT `tokenholderlist`
    (that endpoint requires a paid plan). See milestone note on the
    accuracy trade-off this implies.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL, timeout=15.0)
        self._api_key = get_settings().etherscan_api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _get(self, params: dict) -> dict:
        response = await self._client.get(
            "", params={**params, "apikey": self._api_key.get_secret_value() if self._api_key else ""}
        )
        response.raise_for_status()
        return response.json()

    async def get_recent_transfers(
        self, chain: Chain, contract_address: str, limit: int = 1000
    ) -> list[EtherscanTransfer]:
        chain_id = ETHERSCAN_CHAIN_IDS.get(chain)
        if chain_id is None:
            raise ValueError(f"Wallet scanning not supported for chain '{chain.value}'")

        cache_key = f"etherscan:tokentx:{chain.value}:{contract_address}"
        cached = await cache_get(cache_key)
        if cached is not None:
            log.debug("etherscan_cache_hit", chain=chain.value, address=contract_address)
            return [EtherscanTransfer.model_validate(t) for t in cached]

        raw = await self._get({
            "chainid": chain_id, "module": "account", "action": "tokentx",
            "contractaddress": contract_address, "page": 1, "offset": limit,
            "sort": "desc",
        })
        results = raw.get("result", [])
        if not isinstance(results, list):
            # Etherscan returns {"status":"0","message":"No transactions found"}
            # (result as a STRING, not a list) when there's simply no data --
            # not an error, just empty. Treat it as zero transfers.
            log.info("etherscan_no_transfers", chain=chain.value, address=contract_address)
            results = []

        await cache_set(cache_key, results, ttl_seconds=300)  # 5min -- transfer history changes slower than price
        return [EtherscanTransfer.model_validate(t) for t in results]

    async def close(self) -> None:
        await self._client.aclose()