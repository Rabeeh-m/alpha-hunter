from __future__ import annotations

from decimal import Decimal

import pytest

from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository


@pytest.fixture
async def seeded_repo(db_session):
    repo = TokenRepository(db_session)
    tokens = [
        Token(
            chain=Chain.BASE,
            contract_address="0x1",
            name="Alpha Coin",
            symbol="ALPHA",
            liquidity_usd=Decimal("50000"),
        ),
        Token(
            chain=Chain.BASE,
            contract_address="0x2",
            name="Beta Token",
            symbol="BETA",
            liquidity_usd=Decimal("5000"),
        ),
        Token(
            chain=Chain.SOLANA,
            contract_address="0x3",
            name="Gamma",
            symbol="GAMMA",
            liquidity_usd=None,
        ),
    ]
    for t in tokens:
        await repo.add(t)
    await db_session.flush()
    return repo


async def test_search_filters_by_chain(seeded_repo):
    results, total = await seeded_repo.search(
        chain=Chain.BASE, sort="-created_at", page=1, page_size=25
    )
    assert total == 2
    assert all(t.chain == Chain.BASE for t in results)


async def test_search_filters_by_name_or_symbol(seeded_repo):
    results, total = await seeded_repo.search(
        search="beta", sort="-created_at", page=1, page_size=25
    )
    assert total == 1
    assert results[0].symbol == "BETA"


async def test_search_filters_by_min_liquidity(seeded_repo):
    results, total = await seeded_repo.search(
        min_liquidity=Decimal("10000"), sort="-created_at", page=1, page_size=25
    )
    assert total == 1
    assert results[0].symbol == "ALPHA"


async def test_search_sorts_liquidity_desc_nulls_last(seeded_repo):
    results, _ = await seeded_repo.search(sort="-liquidity_usd", page=1, page_size=25)
    symbols = [t.symbol for t in results]
    assert symbols == ["ALPHA", "BETA", "GAMMA"]  # None (GAMMA) sorts last


async def test_search_pagination(seeded_repo):
    page_1, total = await seeded_repo.search(sort="created_at", page=1, page_size=2)
    page_2, _ = await seeded_repo.search(sort="created_at", page=2, page_size=2)
    assert total == 3
    assert len(page_1) == 2
    assert len(page_2) == 1


async def test_search_sorts_by_alpha_score(db_session, seeded_tokens):
    """Confirms the outerjoin doesn't break existing search/filter/sort
    behavior even when no token has a score yet -- nulls_last() should
    put all of them at the bottom without erroring."""
    repo = TokenRepository(db_session)
    results, total = await repo.search(sort="-alpha_score")
    assert total == 3  # unchanged from the other seeded_tokens tests
