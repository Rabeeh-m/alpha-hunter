from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.models.token import Token
from app.models.token_snapshot import TokenSnapshot
from app.repositories.base import BaseRepository


class TokenSnapshotRepository(BaseRepository[TokenSnapshot]):
    model = TokenSnapshot

    async def add_snapshot(self, token: Token) -> TokenSnapshot:
        """Records the CURRENT state of `token` as a historical point.
        Called once per ingestion cycle, right after upsert -- see
        TokenIngestionService."""
        snapshot = TokenSnapshot(
            token_id=token.id,
            price_usd=token.price_usd,
            liquidity_usd=token.liquidity_usd,
            volume_24h_usd=token.volume_24h_usd,
            market_cap_usd=token.market_cap_usd,
            fdv_usd=token.fdv_usd,
        )
        return await self.add(snapshot)

    async def list_for_token(
        self, token_id, since: datetime, limit: int = 500
    ) -> list[TokenSnapshot]:
        result = await self.session.execute(
            select(TokenSnapshot)
            .where(TokenSnapshot.token_id == token_id, TokenSnapshot.captured_at >= since)
            .order_by(TokenSnapshot.captured_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
