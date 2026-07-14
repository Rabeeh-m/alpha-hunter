from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.wallet_holding import WalletHolding
from app.repositories.base import BaseRepository


class WalletHoldingRepository(BaseRepository[WalletHolding]):
    model = WalletHolding

    async def upsert(self, token_id: UUID, wallet_id: UUID, balance: Decimal, rank: int) -> WalletHolding:
        result = await self.session.execute(
            select(WalletHolding).where(
                WalletHolding.token_id == token_id, WalletHolding.wallet_id == wallet_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.approximate_balance = balance
            existing.rank = rank
            await self.session.flush()
            return existing

        holding = WalletHolding(token_id=token_id, wallet_id=wallet_id, approximate_balance=balance, rank=rank)
        return await self.add(holding)

    async def list_for_token(self, token_id: UUID, limit: int = 20) -> list[WalletHolding]:
        result = await self.session.execute(
            select(WalletHolding)
            .where(WalletHolding.token_id == token_id)
            .order_by(WalletHolding.rank.asc())
            .limit(limit)
        )
        return list(result.scalars().all())