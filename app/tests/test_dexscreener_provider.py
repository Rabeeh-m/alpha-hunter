from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.collectors.dexscreener_client import DexScreenerClient
from app.collectors.dexscreener_provider import DexScreenerProvider

MOCK_PROFILE = {"chainId": "base", "tokenAddress": "0xabc", "links": []}
MOCK_PAIR = {
    "chainId": "base",
    "dexId": "uniswap",
    "pairAddress": "0xpair123",
    "baseToken": {"address": "0xabc", "name": "Test Coin", "symbol": "TEST"},
    "priceUsd": "0.0042",
    "liquidity": {"usd": 15000.0},
    "fdv": 500000.0,
    "marketCap": 400000.0,
    "volume": {"h24": 12000.0},
}


@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    monkeypatch.setattr("app.collectors.dexscreener_client.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.collectors.dexscreener_client.cache_set", AsyncMock())


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url="https://api.dexscreener.com") as client:
        yield client


@respx.mock
async def test_fetch_latest_tokens_returns_normalized_tokens(http_client, mock_cache):
    respx.get("https://api.dexscreener.com/token-profiles/latest/v1").mock(
        return_value=httpx.Response(200, json=[MOCK_PROFILE])
    )
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xabc").mock(
        return_value=httpx.Response(200, json={"pairs": [MOCK_PAIR]})
    )

    dex_client = DexScreenerClient(http_client=http_client)
    provider = DexScreenerProvider(client=dex_client)
    tokens = await provider.fetch_latest_tokens()

    assert len(tokens) == 1
    assert tokens[0].symbol == "TEST"
    assert tokens[0].contract_address == "0xabc"
    assert tokens[0].liquidity_usd == 15000


@respx.mock
async def test_fetch_returns_empty_when_no_profiles(http_client, mock_cache):
    respx.get("https://api.dexscreener.com/token-profiles/latest/v1").mock(
        return_value=httpx.Response(200, json=[])
    )

    dex_client = DexScreenerClient(http_client=http_client)
    provider = DexScreenerProvider(client=dex_client)
    tokens = await provider.fetch_latest_tokens()

    assert tokens == []


@respx.mock
async def test_fetch_returns_empty_when_no_pairs(http_client, mock_cache):
    respx.get("https://api.dexscreener.com/token-profiles/latest/v1").mock(
        return_value=httpx.Response(200, json=[MOCK_PROFILE])
    )
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xabc").mock(
        return_value=httpx.Response(200, json={"pairs": []})
    )

    dex_client = DexScreenerClient(http_client=http_client)
    provider = DexScreenerProvider(client=dex_client)
    tokens = await provider.fetch_latest_tokens()

    assert tokens == []


@respx.mock
async def test_fetch_skips_unsupported_chain_pairs(http_client, mock_cache):
    bad_pair = {**MOCK_PAIR, "chainId": "not-a-real-chain"}

    respx.get("https://api.dexscreener.com/token-profiles/latest/v1").mock(
        return_value=httpx.Response(200, json=[MOCK_PROFILE])
    )
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xabc").mock(
        return_value=httpx.Response(200, json={"pairs": [bad_pair, MOCK_PAIR]})
    )

    dex_client = DexScreenerClient(http_client=http_client)
    provider = DexScreenerProvider(client=dex_client)
    tokens = await provider.fetch_latest_tokens()

    assert len(tokens) == 1
    assert tokens[0].chain.value == "base"


@respx.mock
async def test_fetch_includes_social_links_from_profile(http_client, mock_cache):
    profile_with_links = {
        "chainId": "base",
        "tokenAddress": "0xabc",
        "links": [
            {"type": "telegram", "url": "https://t.me/test"},
            {"type": "twitter", "url": "https://x.com/test"},
            {"type": "github", "url": "https://github.com/test/repo"},
        ],
    }

    respx.get("https://api.dexscreener.com/token-profiles/latest/v1").mock(
        return_value=httpx.Response(200, json=[profile_with_links])
    )
    respx.get("https://api.dexscreener.com/latest/dex/tokens/0xabc").mock(
        return_value=httpx.Response(200, json={"pairs": [MOCK_PAIR]})
    )

    dex_client = DexScreenerClient(http_client=http_client)
    provider = DexScreenerProvider(client=dex_client)
    tokens = await provider.fetch_latest_tokens()

    assert len(tokens) == 1
    assert tokens[0].telegram_url == "https://t.me/test"
    assert tokens[0].twitter_handle == "https://x.com/test"
    assert tokens[0].github_url == "https://github.com/test/repo"


@respx.mock
async def test_close_propagates_to_client(http_client, mock_cache):
    dex_client = DexScreenerClient(http_client=http_client)
    provider = DexScreenerProvider(client=dex_client)
    await provider.close()
