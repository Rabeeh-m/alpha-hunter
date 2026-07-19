from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.database.session import get_db
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.base import BaseRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate


class TokenBaseRepo(BaseRepository[Token]):
    model = Token


async def test_list_all_returns_paginated_tokens(db_session: AsyncSession):
    repo = TokenBaseRepo(db_session)
    for i in range(5):
        token = Token(
            chain=Chain.BASE, contract_address=f"0xlist{i}", name=f"Token{i}", symbol=f"T{i}",
            liquidity_usd=Decimal("1000"),
        )
        db_session.add(token)
    await db_session.flush()

    result = await repo.list_all(limit=3, offset=0)
    assert len(result) == 3

    result2 = await repo.list_all(limit=3, offset=3)
    assert len(result2) == 2


async def test_list_all_returns_empty_when_no_tokens(db_session: AsyncSession):
    repo = TokenBaseRepo(db_session)
    result = await repo.list_all()
    assert result == []


async def test_upsert_updates_existing_token_gracefully(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    original = TokenCreate(
        chain=Chain.BASE, contract_address="0xgrace", name="Original", symbol="ORG",
        liquidity_usd=Decimal("50000"),
    )
    first = await repo.upsert(original)
    assert first.name == "Original"

    update = TokenCreate(
        chain=Chain.BASE, contract_address="0xgrace", name="Updated", symbol="UPD",
        liquidity_usd=Decimal("100"),
    )
    second = await repo.upsert(update)
    assert second.id == first.id
    assert second.liquidity_usd == Decimal("100")


async def test_concurrent_insert_raises_integrity_error(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    await repo.upsert(TokenCreate(
        chain=Chain.BASE, contract_address="0xconcurrent", name="First", symbol="1ST",
        liquidity_usd=Decimal("50000"),
    ))
    await db_session.flush()

    with pytest.raises(IntegrityError):
        duplicate = Token(
            chain=Chain.BASE, contract_address="0xconcurrent", name="Second", symbol="2ND",
            liquidity_usd=Decimal("100"),
        )
        db_session.add(duplicate)
        await db_session.flush()
