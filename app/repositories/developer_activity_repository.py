from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.developer.scoring import DeveloperActivityResult
from app.models.developer_activity import DeveloperActivity
from app.repositories.base import BaseRepository


class DeveloperActivityRepository(BaseRepository[DeveloperActivity]):
    model = DeveloperActivity

    async def get_by_token_id(self, token_id: UUID) -> DeveloperActivity | None:
        result = await self.session.execute(
            select(DeveloperActivity).where(DeveloperActivity.token_id == token_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, token_id: UUID, result: DeveloperActivityResult) -> DeveloperActivity:
        existing = await self.get_by_token_id(token_id)
        fields = {
            "score": result.score,
            "flags": result.flags,
            "stars": result.stars,
            "forks": result.forks,
            "contributors_count": result.contributors_count,
            "last_commit_at": result.last_commit_at,
            "is_fork": result.is_fork,
            "is_archived": result.is_archived,
        }
        if existing is not None:
            for key, value in fields.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing
        return await self.add(DeveloperActivity(token_id=token_id, **fields))
