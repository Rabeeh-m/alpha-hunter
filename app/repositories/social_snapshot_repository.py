from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.social_snapshot import TokenSocialSnapshot
from app.repositories.base import BaseRepository


class SocialSnapshotRepository(BaseRepository[TokenSocialSnapshot]):
    model = TokenSocialSnapshot

    async def get_latest_for_token(self, token_id: UUID) -> TokenSocialSnapshot | None:
        result = await self.session.execute(
            select(TokenSocialSnapshot)
            .where(TokenSocialSnapshot.token_id == token_id)
            .order_by(TokenSocialSnapshot.scanned_at.desc())
            .limit(1)
        )
        return result.scalars().first()
