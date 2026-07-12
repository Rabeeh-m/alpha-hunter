from __future__ import annotations

from sqlalchemy import select

from app.models.chain import Chain
from app.models.token import Token
from app.repositories.base import BaseRepository
from app.schemas.token import TokenCreate


class TokenRepository(BaseRepository[Token]):
    model = Token

    async def get_by_chain_and_address(self, chain: Chain, contract_address: str) -> Token | None:
        result = await self.session.execute(
            select(Token).where(Token.chain == chain, Token.contract_address == contract_address)
        )
        return result.scalar_one_or_none()

    async def upsert(self, data: TokenCreate) -> Token:
        """Insert a new token, or update mutable fields if it already exists.
        Existence is keyed on (chain, contract_address) — see the unique
        constraint on the Token model."""

        existing = await self.get_by_chain_and_address(data.chain, data.contract_address)
        if existing is None:
            token = Token(**data.model_dump())
            return await self.add(token)

        for field in (
            "pair_address", "dex", "liquidity_usd", "market_cap_usd",
            "fdv_usd", "volume_24h_usd", "price_usd",
        ):
            setattr(existing, field, getattr(data, field))
        await self.session.flush()
        return existing
