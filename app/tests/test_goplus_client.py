from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.collectors.goplus_client import GoPlusClient
from app.models.chain import Chain
from app.schemas.goplus import GoPlusTokenSecurity


MOCK_SECURITY_RESPONSE = {
    "code": 1,
    "message": "OK",
    "result": {
        "0xabc": {
            "is_open_source": "1",
            "is_proxy": "0",
            "is_mintable": "0",
            "is_honeypot": "0",
            "buy_tax": "0",
            "sell_tax": "0",
            "holder_count": "1000",
        }
    },
}

MOCK_SECURITY_RESPONSE_NO_RESULT = {
    "code": 1,
    "message": "OK",
    "result": {},
}


@pytest.fixture
def mock_cache(monkeypatch):
    monkeypatch.setattr("app.collectors.goplus_client.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.collectors.goplus_client.cache_set", AsyncMock())


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url="https://api.gopluslabs.io/api/v1") as client:
        yield client


class TestGoPlusClient:
    @respx.mock
    async def test_get_token_security_parses_response(self, http_client, mock_cache):
        respx.get("https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses=0xabc").mock(
            return_value=httpx.Response(200, json=MOCK_SECURITY_RESPONSE)
        )
        client = GoPlusClient(http_client=http_client)
        result = await client.get_token_security(Chain.BASE, "0xabc")
        assert result is not None
        assert result.is_open_source == "1"
        assert result.is_honeypot == "0"
        assert result.holder_count == "1000"

    @respx.mock
    async def test_returns_none_when_address_not_in_result(self, http_client, mock_cache):
        respx.get("https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses=0xmissing").mock(
            return_value=httpx.Response(200, json=MOCK_SECURITY_RESPONSE_NO_RESULT)
        )
        client = GoPlusClient(http_client=http_client)
        result = await client.get_token_security(Chain.BASE, "0xmissing")
        assert result is None

    @respx.mock
    async def test_raises_on_unsupported_chain(self, http_client, mock_cache):
        client = GoPlusClient(http_client=http_client)
        with pytest.raises(ValueError, match="not supported for chain 'solana'"):
            await client.get_token_security(Chain.SOLANA, "0xabc")

    @respx.mock
    async def test_uses_cached_value_when_available(self, http_client):
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.collectors.goplus_client.cache_get", AsyncMock(return_value={
            "is_open_source": "1", "is_proxy": "0", "is_mintable": "0",
            "is_honeypot": "0", "buy_tax": "0", "sell_tax": "0", "holder_count": "500",
        }))
        monkeypatch.setattr("app.collectors.goplus_client.cache_set", AsyncMock())

        try:
            client = GoPlusClient(http_client=http_client)
            result = await client.get_token_security(Chain.BASE, "0xcached")
            assert result is not None
            assert result.holder_count == "500"
        finally:
            monkeypatch.undo()

    @respx.mock
    async def test_retry_then_succeeds_after_transient_500(self, http_client, mock_cache):
        call_count = 0

        def _handler(request):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return httpx.Response(500)
            return httpx.Response(200, json={
                "code": 1, "message": "OK",
                "result": {"0xretry": {"is_open_source": "1", "is_honeypot": "0", "holder_count": "500"}},
            })

        respx.get("https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses=0xretry").mock(side_effect=_handler)
        client = GoPlusClient(http_client=http_client)
        result = await client.get_token_security(Chain.BASE, "0xretry")
        assert result is not None
        assert result.holder_count == "500"
        assert call_count == 2

    @respx.mock
    async def test_raises_after_exhausting_retries(self, http_client, mock_cache):
        respx.get("https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses=0xfail").mock(
            return_value=httpx.Response(503)
        )
        client = GoPlusClient(http_client=http_client)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_token_security(Chain.BASE, "0xfail")
