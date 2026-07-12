from __future__ import annotations

from unittest.mock import patch, AsyncMock
import httpx
import pytest
import respx

from app.collectors.geckoterminal_client import GeckoTerminalClient
from app.collectors.geckoterminal_normalizer import normalize_pool
from app.collectors.geckoterminal_provider import GeckoTerminalProvider
from app.models.chain import Chain
from app.schemas.geckoterminal import GeckoTerminalPool

MOCK_POOL = {
    "id": "eth_0xpool789",
    "attributes": {
        "name": "TEST / WETH",
        "base_token_price_usd": "0.0055",
        "reserve_in_usd": "22000.5",
        "fdv_usd": "600000",
        "market_cap_usd": "450000",
        "volume_usd": {"h24": "9000"},
        "pool_created_at": "2026-07-01T00:00:00Z",
    },
    "relationships": {
        "base_token": {"data": {"id": "eth_0xtoken789", "type": "token"}},
        "dex": {"data": {"id": "uniswap_v3", "type": "dex"}},
    },
}


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url="https://api.geckoterminal.com/api/v2") as client:
        yield client


@respx.mock
async def test_get_new_pools_parses_response(http_client):
    respx.get("https://api.geckoterminal.com/api/v2/networks/eth/new_pools").mock(
        return_value=httpx.Response(200, json={"data": [MOCK_POOL]})
    )

    client = GeckoTerminalClient(http_client=http_client)
    pools = await client.get_new_pools("eth")

    assert len(pools) == 1
    assert pools[0].relationships.base_token.data.id == "eth_0xtoken789"


def test_normalize_pool_extracts_address_and_symbol():
    pool = GeckoTerminalPool.model_validate(MOCK_POOL)
    token = normalize_pool(pool, "eth")

    assert token is not None
    assert token.contract_address == "0xtoken789"
    assert token.symbol == "TEST"
    assert token.liquidity_usd == pytest.approx(22000.5)


def test_normalize_pool_returns_none_for_unsupported_network():
    pool = GeckoTerminalPool.model_validate(MOCK_POOL)
    assert normalize_pool(pool, "not-a-real-network") is None


@respx.mock
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_provider_fetch_latest_tokens_skips_429(mock_sleep, http_client):
    # Mock eth to return 429
    respx.get("https://api.geckoterminal.com/api/v2/networks/eth/new_pools").mock(
        return_value=httpx.Response(429, json={"error": "Too Many Requests"})
    )
    # Mock base to return valid pool
    respx.get("https://api.geckoterminal.com/api/v2/networks/base/new_pools").mock(
        return_value=httpx.Response(200, json={"data": [MOCK_POOL]})
    )
    # Mock all other networks to return empty 200
    for network in ["solana", "bsc", "arbitrum", "polygon_pos", "avax", "optimism"]:
        respx.get(f"https://api.geckoterminal.com/api/v2/networks/{network}/new_pools").mock(
            return_value=httpx.Response(200, json={"data": []})
        )

    client = GeckoTerminalClient(http_client=http_client, rate_limit_interval=0.0)
    provider = GeckoTerminalProvider(client=client)

    tokens = await provider.fetch_latest_tokens()

    # eth was skipped (error logged), but base succeeded
    assert len(tokens) == 1
    assert tokens[0].chain == Chain.BASE
    assert tokens[0].contract_address == "0xtoken789"


@respx.mock
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_client_retries_and_backs_off_on_429(mock_sleep, http_client):
    route = respx.get("https://api.geckoterminal.com/api/v2/networks/eth/new_pools")
    route.side_effect = [
        httpx.Response(429, json={"error": "Too Many Requests"}),
        httpx.Response(429, json={"error": "Too Many Requests"}),
        httpx.Response(200, json={"data": [MOCK_POOL]})
    ]

    client = GeckoTerminalClient(http_client=http_client, rate_limit_interval=0.0)
    pools = await client.get_new_pools("eth")

    assert len(pools) == 1
    assert route.call_count == 3
    # Verify that tenacity sleep was actually called during retry backoff
    assert mock_sleep.call_count >= 2


@respx.mock
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_client_rate_limiting(mock_sleep, http_client):
    respx.get("https://api.geckoterminal.com/api/v2/networks/eth/new_pools").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    respx.get("https://api.geckoterminal.com/api/v2/networks/base/new_pools").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    client = GeckoTerminalClient(http_client=http_client, rate_limit_interval=1.0)

    # First call: no previous requests, should not call sleep
    await client.get_new_pools("eth")
    assert mock_sleep.call_count == 0

    # Second call: immediately after, should trigger rate limiting sleep
    await client.get_new_pools("base")
    assert mock_sleep.call_count == 1
    called_sleep_time = mock_sleep.call_args[0][0]
    assert 0.8 < called_sleep_time <= 1.0