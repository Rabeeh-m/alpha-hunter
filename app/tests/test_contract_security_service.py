from __future__ import annotations

import httpx
import pytest
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.goplus_client import GoPlusClient
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.token_repository import TokenRepository
from app.services.contract_security_service import (
    ContractSecurityService,
    UnsupportedChainForSecurityScan,
)

MOCK_RESPONSE = {
    "code": 1,
    "message": "OK",
    "result": {"0xsecure": {"is_open_source": "1", "is_honeypot": "0", "is_mintable": "0"}},
}


@pytest.fixture
async def seeded_token(db_session: AsyncSession) -> Token:
    repo = TokenRepository(db_session)
    return await repo.add(
        Token(chain=Chain.BASE, contract_address="0xsecure", name="Secure Coin", symbol="SEC")
    )


@respx.mock
async def test_scan_token_persists_safety_score(db_session, seeded_token):
    respx.get("https://api.gopluslabs.io/api/v1/token_security/8453").mock(
        return_value=httpx.Response(200, json=MOCK_RESPONSE)
    )

    async with httpx.AsyncClient(base_url="https://api.gopluslabs.io/api/v1") as http_client:
        client = GoPlusClient(http_client=http_client)
        repo = ContractSecurityRepository(db_session)
        service = ContractSecurityService(client, repo)

        score = await service.scan_token(seeded_token)

    assert score == 100
    record = await repo.get_by_token_id(seeded_token.id)
    assert record is not None
    assert record.is_honeypot is False


async def test_scan_token_raises_for_unsupported_chain(db_session):
    token_repo = TokenRepository(db_session)
    solana_token = await token_repo.add(
        Token(chain=Chain.SOLANA, contract_address="sol999", name="Sol", symbol="SOL")
    )

    client = GoPlusClient()
    repo = ContractSecurityRepository(db_session)
    service = ContractSecurityService(client, repo)

    with pytest.raises(UnsupportedChainForSecurityScan):
        await service.scan_token(solana_token)
