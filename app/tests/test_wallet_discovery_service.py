from __future__ import annotations
from decimal import Decimal

import httpx
import pytest
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.etherscan_client import EtherscanClient
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.repositories.whale_event_repository import WhaleEventRepository
from app.services.wallet_discovery_service import UnsupportedChainForWalletScan, WalletDiscoveryService
from app.core.cache import get_redis

MOCK_RESPONSE = {
    "status": "1",
    "result": [
        {"from": "0xmint", "to": "0xwhale", "value": "1000000000000000000000", "tokenDecimal": "18"},
        {"from": "0xmint", "to": "0xsmall", "value": "10000000000000000000", "tokenDecimal": "18"},
    ],
}


@pytest.fixture
async def seeded_token(db_session: AsyncSession) -> Token:
    repo = TokenRepository(db_session)
    return await repo.add(Token(chain=Chain.BASE, contract_address="0xscan", name="Scan Coin", symbol="SCAN"))


@respx.mock
async def test_scan_token_persists_ranked_wallets(db_session, seeded_token):
    # Clear any cached data from prior test runs
    cache_key = f"etherscan:tokentx:{seeded_token.chain.value}:{seeded_token.contract_address}"
    await get_redis().delete(cache_key)
    respx.get(url__startswith="https://api.etherscan.io/v2/api").mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))

    async with httpx.AsyncClient(base_url="https://api.etherscan.io/v2/api") as http_client:
        client = EtherscanClient(http_client=http_client)
        wallet_repo = WalletRepository(db_session)
        holding_repo = WalletHoldingRepository(db_session)
        whale_event_repo = WhaleEventRepository(db_session)
        service = WalletDiscoveryService(client, wallet_repo, holding_repo, whale_event_repo)

        count = await service.scan_token(seeded_token)

    assert count == 2
    holdings = await holding_repo.list_for_token(seeded_token.id)
    assert holdings[0].rank == 1
    assert holdings[0].approximate_balance == 1000


async def test_scan_token_raises_for_unsupported_chain(db_session):
    token_repo = TokenRepository(db_session)
    solana_token = await token_repo.add(
        Token(chain=Chain.SOLANA, contract_address="sol123", name="Sol Coin", symbol="SOL")
    )

    client = EtherscanClient()
    wallet_repo = WalletRepository(db_session)
    holding_repo = WalletHoldingRepository(db_session)
    whale_event_repo = WhaleEventRepository(db_session)
    service = WalletDiscoveryService(client, wallet_repo, holding_repo, whale_event_repo)

    with pytest.raises(UnsupportedChainForWalletScan):
        await service.scan_token(solana_token)
        
@respx.mock
async def test_scan_token_second_pass_detects_increase(db_session, seeded_token):
    """Proves the full loop: scan -> upsert reports previous_balance ->
    classify_balance_change fires -> WhaleEvent persisted."""
    seeded_token.price_usd = Decimal("1")
    await db_session.flush()

    first_response = {
        "status": "1",
        "result": [{"from": "0xmint", "to": "0xgrowingwhale", "value": "5000000000000000000000", "tokenDecimal": "18"}],
    }
    second_response = {
        "status": "1",
        "result": [
            {"from": "0xmint", "to": "0xgrowingwhale", "value": "5000000000000000000000", "tokenDecimal": "18"},
            {"from": "0xmint", "to": "0xgrowingwhale", "value": "5000000000000000000000", "tokenDecimal": "18"},
        ],
    }

    seeded_token.contract_address = "0xuniquegrowingwhale"
    await db_session.flush()

    async with httpx.AsyncClient(base_url="https://api.etherscan.io/v2/api") as http_client:
        client = EtherscanClient(http_client=http_client)
        wallet_repo = WalletRepository(db_session)
        holding_repo = WalletHoldingRepository(db_session)
        whale_event_repo = WhaleEventRepository(db_session)
        service = WalletDiscoveryService(client, wallet_repo, holding_repo, whale_event_repo)

        cache_key = f"etherscan:tokentx:{seeded_token.chain.value}:{seeded_token.contract_address}"

        # Clear any leftover cache from prior runs
        await get_redis().delete(cache_key)

        # First scan — register mock for first response
        respx.get(url__startswith="https://api.etherscan.io/v2/api").mock(return_value=httpx.Response(200, json=first_response))
        await service.scan_token(seeded_token)
        await db_session.flush()

        # Clear cache so second scan makes a real HTTP call
        await get_redis().delete(cache_key)

        # Second scan — replace the mock with the second response
        respx.get(url__startswith="https://api.etherscan.io/v2/api").mock(return_value=httpx.Response(200, json=second_response))
        await service.scan_token(seeded_token)
        await db_session.flush()

        events = await whale_event_repo.list_for_token(seeded_token.id)
        increase_events = [e for e in events if e.event_type.value == "increased"]
        assert len(increase_events) == 1