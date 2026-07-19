from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.social_score import SocialScore
from app.repositories.base import BaseRepository


class SocialScoreRepository(BaseRepository[SocialScore]):
    model = SocialScore

    async def get_by_token_id(self, token_id: UUID) -> SocialScore | None:
        result = await self.session.execute(
            select(SocialScore).where(SocialScore.token_id == token_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, token_id: UUID, score: int, factor_breakdown: dict, possible_inorganic_growth: bool
    ) -> SocialScore:
        existing = await self.get_by_token_id(token_id)
        if existing is not None:
            existing.score = score
            existing.factor_breakdown = factor_breakdown
            existing.possible_inorganic_growth = possible_inorganic_growth
            await self.session.flush()
            return existing

        record = SocialScore(
            token_id=token_id,
            score=score,
            factor_breakdown=factor_breakdown,
            possible_inorganic_growth=possible_inorganic_growth,
        )
        return await self.add(record)
