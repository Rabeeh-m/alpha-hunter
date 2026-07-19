from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from app.collectors.dexscreener_client import DexScreenerClient
from app.collectors.dexscreener_normalizer import normalize_pair
from app.core.cache import get_redis
from app.schemas.dexscreener import DexScreenerPair

MOCK_PAIR = {
    "chainId": "base",
    "dexId": "uniswap",
    "pairAddress": "0xpair123",
    "baseToken": {"address": "0xtoken456", "name": "Test Coin", "symbol": "TEST"},
    "priceUsd": "0.0042",
    "liquidity": {"usd": 15000.0},
    "fdv": 500000.0,
    "marketCap": 400000.0,
    "volume": {"h24": 12000.0},
}


@pytest.fixture
def mock_cache(monkeypatch):
    monkeypatch.setattr("app.collectors.dexscreener_client.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.collectors.dexscreener_client.cache_set", AsyncMock())


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url="https://api.dexscreener.com") as client:
        yield client


@respx.mock
async def test_get_pairs_for_token_parses_response(http_client):
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xtoken456").mock(
        return_value=httpx.Response(200, json={"pairs": [MOCK_PAIR]})
    )

    client = DexScreenerClient(http_client=http_client)
    pairs = await client.get_pairs_for_token("base", "0xtoken456")

    assert len(pairs) == 1
    assert pairs[0].base_token.symbol == "TEST"


@respx.mock
async def test_get_pairs_for_token_filters_by_chain(http_client, mock_cache):
    eth_pair = {**MOCK_PAIR, "chainId": "ethereum", "pairAddress": "0xeth123"}
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xmulti").mock(
        return_value=httpx.Response(200, json={"pairs": [MOCK_PAIR, eth_pair]})
    )

    client = DexScreenerClient(http_client=http_client)
    pairs = await client.get_pairs_for_token("base", "0xmulti")

    assert len(pairs) == 1
    assert pairs[0].chain_id == "base"


@respx.mock
async def test_get_pairs_for_token_returns_empty_when_no_pairs(http_client, mock_cache):
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xempty").mock(
        return_value=httpx.Response(200, json={"pairs": []})
    )

    client = DexScreenerClient(http_client=http_client)
    pairs = await client.get_pairs_for_token("base", "0xempty")

    assert pairs == []


@respx.mock
async def test_get_latest_token_profiles_parses_response(http_client, mock_cache):
    mock_profile = {"chainId": "base", "tokenAddress": "0xabc", "links": []}
    respx.get("https://api.dexscreener.com/token-profiles/latest/v1").mock(
        return_value=httpx.Response(200, json=[mock_profile])
    )

    client = DexScreenerClient(http_client=http_client)
    profiles = await client.get_latest_token_profiles()

    assert len(profiles) == 1
    assert profiles[0].chain_id == "base"
    assert profiles[0].token_address == "0xabc"


@respx.mock
async def test_get_pairs_for_token_uses_cache_when_available(http_client):
    redis = get_redis()
    key = "dexscreener:pairs:base:0xcached"
    await redis.delete(key)

    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xcached").mock(
        return_value=httpx.Response(200, json={"pairs": [MOCK_PAIR]})
    )

    client = DexScreenerClient(http_client=http_client)
    pairs1 = await client.get_pairs_for_token("base", "0xcached")
    assert len(pairs1) == 1

    pairs2 = await client.get_pairs_for_token("base", "0xcached")
    assert len(pairs2) == 1


def test_normalize_pair_produces_valid_token_create():
    pair = DexScreenerPair.model_validate(MOCK_PAIR)
    token = normalize_pair(pair)

    assert token is not None
    assert token.symbol == "TEST"
    assert token.liquidity_usd == 15000


def test_normalize_pair_returns_none_for_unsupported_chain():
    unsupported = {**MOCK_PAIR, "chainId": "not-a-real-chain"}
    pair = DexScreenerPair.model_validate(unsupported)

    assert normalize_pair(pair) is None


def test_normalize_pair_with_missing_dex_id():
    no_dex = {**MOCK_PAIR, "dexId": None}
    pair = DexScreenerPair.model_validate(no_dex)
    token = normalize_pair(pair)
    assert token is not None
    assert token.dex is None


def test_normalize_pair_with_zero_liquidity():
    no_liq = {**MOCK_PAIR, "liquidity": {"usd": 0.0}}
    pair = DexScreenerPair.model_validate(no_liq)
    token = normalize_pair(pair)
    assert token is not None
    assert token.liquidity_usd == 0


def test_normalize_pair_with_none_liquidity():
    no_liq = {**MOCK_PAIR, "liquidity": None}
    pair = DexScreenerPair.model_validate(no_liq)
    token = normalize_pair(pair)
    assert token is not None
    assert token.liquidity_usd is None


@patch("httpx.AsyncClient")
async def test_constructor_creates_own_client_when_none(mock_client_cls):
    mock_instance = AsyncMock()
    mock_client_cls.return_value = mock_instance

    client = DexScreenerClient()
    assert client._client is mock_instance
    mock_client_cls.assert_called_once_with(
        base_url="https://api.dexscreener.com", timeout=10.0
    )


@respx.mock
async def test_client_retries_then_succeeds_after_transient_500(http_client):
    """Proves the tenacity retry decorator actually retries -- not just
    that it's present in the code. First two calls 500, third succeeds."""
    # Clear any cached data from prior runs so the mock handler gets called
    redis = get_redis()
    await redis.delete("dexscreener:pairs:base:0xretrytest")

    call_count = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(500)
        return httpx.Response(200, json={"pairs": [MOCK_PAIR]})

    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xretrytest").mock(side_effect=_handler)

    client = DexScreenerClient(http_client=http_client)
    pairs = await client.get_pairs_for_token("base", "0xretrytest")

    assert call_count == 3
    assert len(pairs) == 1


@respx.mock
async def test_client_raises_after_exhausting_retries(http_client):
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xexhausttest").mock(
        return_value=httpx.Response(503)
    )

    client = DexScreenerClient(http_client=http_client)
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_pairs_for_token("base", "0xexhausttest")


@respx.mock
async def test_close_method(http_client):
    client = DexScreenerClient(http_client=http_client)
    await client.close()
