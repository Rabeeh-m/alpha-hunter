from __future__ import annotations

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