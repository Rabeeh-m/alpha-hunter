from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository


@pytest.fixture
async def db_session():
    from app.core.database.session import async_session_factory

    async with async_session_factory() as session:
        yield session
        await session.rollback()  # never persist test data


async def test_add_and_fetch_token(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    token = Token(
        chain=Chain.BASE,
        contract_address="0xabc123",
        name="Test Token",
        symbol="TEST",
    )
    await repo.add(token)
    await db_session.flush()

    fetched = await repo.get_by_chain_and_address(Chain.BASE, "0xabc123")
    assert fetched is not None
    assert fetched.symbol == "TEST"
