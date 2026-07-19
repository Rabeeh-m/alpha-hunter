from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.models.chain import Chain
from app.models.wallet import Wallet, WalletType
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    model = Wallet

    async def get_or_create(
        self, chain: Chain, address: str, wallet_type: WalletType, confidence: Decimal | None
    ) -> Wallet:
        result = await self.session.execute(
            select(Wallet).where(Wallet.chain == chain, Wallet.address == address)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            # Only upgrade the tag if this scan found stronger evidence
            # (higher confidence) -- never silently downgrade a wallet
            # from a prior, more confident classification.
            if confidence is not None and (
                existing.confidence_score is None or confidence > existing.confidence_score
            ):
                existing.wallet_type = wallet_type
                existing.confidence_score = confidence
            return existing

        wallet = Wallet(
            chain=chain, address=address, wallet_type=wallet_type, confidence_score=confidence
        )
        return await self.add(wallet)
