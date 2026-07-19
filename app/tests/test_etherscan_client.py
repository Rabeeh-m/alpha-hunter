from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.collectors.etherscan_client import EtherscanClient
from app.models.chain import Chain

BASE = "https://api.etherscan.io/v2/api"


@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    monkeypatch.setattr("app.collectors.etherscan_client.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.collectors.etherscan_client.cache_set", AsyncMock())


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url=BASE) as client:
        yield client


@respx.mock
async def test_get_recent_transfers_parses_successful_response(http_client):
    mock_result = [
        {"from": "0xsender", "to": "0xreceiver", "value": "1000000000000000000"},
        {"from": "0xreceiver", "to": "0xthird", "value": "2000000000000000000"},
    ]
    respx.get(url__startswith=BASE).mock(
        return_value=httpx.Response(
            200, json={"status": "1", "message": "OK", "result": mock_result}
        )
    )

    client = EtherscanClient(http_client=http_client)
    transfers = await client.get_recent_transfers(Chain.ETHEREUM, "0xcontract")

    assert len(transfers) == 2
    assert transfers[0].from_address == "0xsender"
    assert transfers[0].to_address == "0xreceiver"
    assert transfers[1].value == "2000000000000000000"


@respx.mock
async def test_get_recent_transfers_raises_for_unsupported_chain(http_client):
    client = EtherscanClient(http_client=http_client)
    with pytest.raises(ValueError, match="not supported"):
        await client.get_recent_transfers(Chain.SOLANA, "0xcontract")


@respx.mock
async def test_get_recent_transfers_returns_empty_when_api_returns_error_string(http_client):
    respx.get(url__startswith=BASE).mock(
        return_value=httpx.Response(
            200, json={"status": "0", "message": "NOTOK", "result": "Something happened"}
        )
    )

    client = EtherscanClient(http_client=http_client)
    transfers = await client.get_recent_transfers(Chain.ETHEREUM, "0xcontract")

    assert transfers == []


@respx.mock
async def test_close(http_client):
    client = EtherscanClient(http_client=http_client)
    await client.close()
