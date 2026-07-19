from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository


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
