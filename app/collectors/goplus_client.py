from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.blockchain.chain_ids import EVM_CHAIN_IDS
from app.core.cache import cache_get, cache_set
from app.core.logging import get_logger
from app.models.chain import Chain
from app.schemas.goplus import GoPlusResponse, GoPlusTokenSecurity

log = get_logger(__name__)

BASE_URL = "https://api.gopluslabs.io/api/v1"


class GoPlusClient:
    """Free, public token-security API -- no key required at reasonable
    request volumes (correction to the M1 assumption that reserved
    GOPLUS_API_KEY; not actually needed for this endpoint)."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL, timeout=15.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _get(self, path: str, params: dict) -> dict:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def get_token_security(
        self, chain: Chain, contract_address: str
    ) -> GoPlusTokenSecurity | None:
        chain_id = EVM_CHAIN_IDS.get(chain)
        if chain_id is None:
            raise ValueError(f"Contract security scanning not supported for chain '{chain.value}'")

        cache_key = f"goplus:token_security:{chain.value}:{contract_address}"
        cached = await cache_get(cache_key)
        if cached is not None:
            log.debug("goplus_cache_hit", chain=chain.value, address=contract_address)
            return GoPlusTokenSecurity.model_validate(cached) if cached else None

        raw = await self._get(
            f"/token_security/{chain_id}", {"contract_addresses": contract_address}
        )
        parsed = GoPlusResponse.model_validate(raw)

        result = parsed.result.get(contract_address.lower())
        await cache_set(
            cache_key, result.model_dump() if result else {}, ttl_seconds=3600
        )  # security flags change slowly
        log.info(
            "goplus_fetched", chain=chain.value, address=contract_address, found=result is not None
        )
        return result

    async def close(self) -> None:
        await self._client.aclose()
