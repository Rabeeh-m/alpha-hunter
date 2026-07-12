from __future__ import annotations

import httpx
import pytest
import respx

from app.collectors.dexscreener_client import DexScreenerClient
from app.collectors.dexscreener_normalizer import normalize_pair
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