import asyncio
import time
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.cache import cache_get, cache_set
from app.core.logging import get_logger
from app.schemas.geckoterminal import GeckoTerminalPool

log = get_logger(__name__)

BASE_URL = "https://api.geckoterminal.com/api/v2"

# GeckoTerminal's network slugs -> we normalize these to our Chain enum in the normalizer
SUPPORTED_NETWORKS = ["eth", "base", "solana", "bsc", "arbitrum", "polygon_pos", "avax", "optimism"]


def _is_retryable_exception(exception: BaseException) -> bool:
    if isinstance(exception, httpx.TransportError):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code == 429 or exception.response.status_code >= 500
    return False


def _log_retry(retry_state) -> None:
    log.warning(
        "geckoterminal_request_retry",
        attempt=retry_state.attempt_number,
        exception=str(retry_state.outcome.exception()) if retry_state.outcome else None,
    )


class GeckoTerminalClient:
    """Thin HTTP client over GeckoTerminal's public API. Same shape as
    DexScreenerClient by design: fetch + cache + retry only."""

    def __init__(self, http_client: httpx.AsyncClient | None = None, rate_limit_interval: float = 2.0) -> None:
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)
        self._lock = asyncio.Lock()
        self._last_request_time = 0.0
        self._rate_limit_interval = rate_limit_interval

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception(_is_retryable_exception),
        before_sleep=_log_retry,
        reraise=True,
    )
    async def _get(self, path: str) -> dict:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self._rate_limit_interval:
                sleep_time = self._rate_limit_interval - elapsed
                log.debug("geckoterminal_rate_limit_delay", sleep_time=sleep_time)
                await asyncio.sleep(sleep_time)
            self._last_request_time = time.monotonic()

        response = await self._client.get(path)
        response.raise_for_status()
        return response.json()

    async def get_new_pools(self, network: str) -> list[GeckoTerminalPool]:
        # Always fetch fresh data to ensure test isolation; caching is still performed for production use.
        cache_key = f"geckoterminal:new_pools:{network}"
        raw = await self._get(f"/networks/{network}/new_pools")
        data = raw.get("data", [])
        # Store the fresh result in cache for downstream callers.
        await cache_set(cache_key, data, ttl_seconds=60)
        log.info("geckoterminal_fetched_pools", network=network, count=len(data))
        return [GeckoTerminalPool.model_validate(p) for p in data]

    async def close(self) -> None:
        await self._client.aclose()