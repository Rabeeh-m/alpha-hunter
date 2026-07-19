from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.whale_event import WhaleEvent
from app.repositories.base import BaseRepository


class WhaleEventRepository(BaseRepository[WhaleEvent]):
    model = WhaleEvent

    async def list_recent(self, limit: int = 50) -> list[WhaleEvent]:
        result = await self.session.execute(
            select(WhaleEvent).order_by(WhaleEvent.detected_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_token(self, token_id: UUID, limit: int = 50) -> list[WhaleEvent]:
        result = await self.session.execute(
            select(WhaleEvent)
            .where(WhaleEvent.token_id == token_id)
            .order_by(WhaleEvent.detected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
