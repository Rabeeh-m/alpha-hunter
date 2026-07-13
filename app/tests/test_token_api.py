from __future__ import annotations

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidSortField
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository


@pytest.fixture
async def seeded_tokens(db_session: AsyncSession) -> list[Token]:
    tokens = [
        Token(chain=Chain.BASE, contract_address="0xaaa", name="Alpha Coin", symbol="ALPHA", liquidity_usd=50000),
        Token(chain=Chain.BASE, contract_address="0xbbb", name="Beta Coin", symbol="BETA", liquidity_usd=None),
        Token(chain=Chain.ETHEREUM, contract_address="0xccc", name="Gamma Token", symbol="GAMMA", liquidity_usd=10000),
    ]
    for t in tokens:
        db_session.add(t)
    await db_session.flush()
    return tokens


async def test_search_filters_by_symbol(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, total = await repo.search(search="ALPHA")
    assert total == 1
    assert results[0].symbol == "ALPHA"


async def test_search_filters_by_chain(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, total = await repo.search(chain=Chain.ETHEREUM)
    assert total == 1
    assert results[0].chain == Chain.ETHEREUM


async def test_search_sorts_with_nulls_last(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, _ = await repo.search(sort="-liquidity_usd")
    assert results[0].symbol == "ALPHA"   # highest liquidity, first
    assert results[-1].symbol == "BETA"   # NULL liquidity, always last


async def test_search_raises_on_unknown_sort_field(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    with pytest.raises(InvalidSortField):
        await repo.search(sort="not_a_real_field; DROP TABLE tokens;")


async def test_search_pagination(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, total = await repo.search(page=1, page_size=2)
    assert total == 3
    assert len(results) == 2


@pytest.mark.usefixtures("app_env")
async def test_list_tokens_invalid_sort_returns_400():
    from app.main import create_app

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tokens", params={"sort": "malicious_field"})

    assert response.status_code == 400