from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.alpha_score import AlphaScore
from app.repositories.base import BaseRepository


class AlphaScoreRepository(BaseRepository[AlphaScore]):
    model = AlphaScore

    async def upsert(self, token_id: UUID, score: Decimal, factor_breakdown: dict) -> AlphaScore:
        result = await self.session.execute(
            select(AlphaScore).where(AlphaScore.token_id == token_id)
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            alpha_score = AlphaScore(
                token_id=token_id, score=score, factor_breakdown=factor_breakdown
            )
            return await self.add(alpha_score)

        existing.score = score
        existing.factor_breakdown = factor_breakdown
        await self.session.flush()
        return existing
