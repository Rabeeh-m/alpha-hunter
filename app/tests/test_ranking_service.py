from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chain import Chain
from app.models.token import Token
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.services.ranking_service import RankingService


@pytest.fixture
async def seeded_token(db_session: AsyncSession) -> Token:
    repo = TokenRepository(db_session)
    token = Token(
        chain=Chain.BASE, contract_address="0xrank", name="Rank Coin", symbol="RANK",
        liquidity_usd=Decimal("50000"), volume_24h_usd=Decimal("20000"),
        market_cap_usd=Decimal("500000"),
    )
    return await repo.add(token)


async def test_compute_for_token_persists_score_and_breakdown(db_session, seeded_token):
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    service = RankingService(token_repo, snapshot_repo, alpha_repo)

    score = await service.compute_for_token(seeded_token)
    await db_session.flush()
    await db_session.refresh(seeded_token, ["alpha_score"])

    assert 0 <= score <= 100
    saved = await alpha_repo.get_by_id(seeded_token.alpha_score.id)
    assert saved is not None
    assert "composite" in saved.factor_breakdown
    assert "liquidity" in saved.factor_breakdown


async def test_compute_for_token_is_idempotent_upsert(db_session, seeded_token):
    """Running the ranking pass twice must update the same row, not
    create a second one -- this is what makes alpha_scores current-state,
    not history."""
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    service = RankingService(token_repo, snapshot_repo, alpha_repo)

    await service.compute_for_token(seeded_token)
    await db_session.refresh(seeded_token, ["alpha_score"])
    first_id = seeded_token.alpha_score.id

    await service.compute_for_token(seeded_token)
    await db_session.flush()
    await db_session.refresh(seeded_token, ["alpha_score"])

    assert seeded_token.alpha_score.id == first_id