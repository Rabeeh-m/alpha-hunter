from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.narrative_classification import Narrative, NarrativeClassification
from app.models.token import Token
from app.repositories.base import BaseRepository


class NarrativeRepository(BaseRepository[NarrativeClassification]):
    model = NarrativeClassification

    async def get_by_token_id(self, token_id: UUID) -> NarrativeClassification | None:
        result = await self.session.execute(
            select(NarrativeClassification).where(NarrativeClassification.token_id == token_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, token_id: UUID, narrative: Narrative, confidence: Decimal, reasoning: str
    ) -> NarrativeClassification:
        existing = await self.get_by_token_id(token_id)
        if existing is not None:
            existing.primary_narrative = narrative
            existing.confidence = confidence
            existing.reasoning = reasoning
            await self.session.flush()
            return existing

        record = NarrativeClassification(
            token_id=token_id,
            primary_narrative=narrative,
            confidence=confidence,
            reasoning=reasoning,
        )
        return await self.add(record)

    async def list_unclassified_tokens(self, limit: int = 20) -> list[Token]:
        """LEFT JOIN, WHERE classification IS NULL -- this is the query
        that makes the scheduled job's 'clear the backlog' behavior
        work, distinct from every prior *_score/security table's
        'refresh the top N' pattern."""
        result = await self.session.execute(
            select(Token)
            .outerjoin(NarrativeClassification, Token.id == NarrativeClassification.token_id)
            .where(NarrativeClassification.id.is_(None))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def distribution(self) -> dict[str, int]:
        result = await self.session.execute(
            select(NarrativeClassification.primary_narrative, func_count()).group_by(
                NarrativeClassification.primary_narrative
            )
        )
        return {row[0].value: row[1] for row in result.all()}


def func_count():
    from sqlalchemy import func

    return func.count()
