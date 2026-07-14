from __future__ import annotations

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
from app.services.wallet_discovery_service import UnsupportedChainForWalletScan, WalletDiscoveryService

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
    respx.get(url__startswith="https://api.etherscan.io/v2/api").mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))

    async with httpx.AsyncClient(base_url="https://api.etherscan.io/v2/api") as http_client:
        client = EtherscanClient(http_client=http_client)
        wallet_repo = WalletRepository(db_session)
        holding_repo = WalletHoldingRepository(db_session)
        service = WalletDiscoveryService(client, wallet_repo, holding_repo)

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
    service = WalletDiscoveryService(client, wallet_repo, holding_repo)

    with pytest.raises(UnsupportedChainForWalletScan):
        await service.scan_token(solana_token)