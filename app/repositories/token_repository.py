from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select

from app.core.exceptions import InvalidSortField
from app.models.alpha_score import AlphaScore
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.base import BaseRepository
from app.schemas.token import TokenCreate

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

# Whitelisted sort fields -- a client-supplied sort string is NEVER
# interpolated into ORDER BY. Only keys listed here are reachable;
# anything else raises InvalidSortField, which the API turns into a 400.
SORTABLE_FIELDS: dict[str, ColumnElement] = {
    "symbol": Token.symbol,
    "price_usd": Token.price_usd,
    "liquidity_usd": Token.liquidity_usd,
    "volume_24h_usd": Token.volume_24h_usd,
    "market_cap_usd": Token.market_cap_usd,
    "fdv_usd": Token.fdv_usd,
    "created_at": Token.created_at,
    "pair_created_at": Token.pair_created_at,
    "alpha_score": AlphaScore.score,
}

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

    async def search(
        self,
        *,
        search: str | None = None,
        chain: Chain | None = None,
        min_liquidity: Decimal | None = None,
        min_volume: Decimal | None = None,
        created_within_hours: int | None = None,
        sort: str = "-volume_24h_usd",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Token], int]:
        """Search/filter/sort/paginate tokens.

        `sort` is public-facing, e.g. '-liquidity_usd' (desc) or
        'liquidity_usd' (asc). The leading '-' is the only parsing done on
        client input -- the field name is looked up in SORTABLE_FIELDS,
        never interpolated into SQL.

        `created_within_hours` filters to tokens whose pair was created
        on-chain within the last N hours. Uses `pair_created_at`.
        """
        descending = sort.startswith("-")
        field_key = sort[1:] if descending else sort

        column = SORTABLE_FIELDS.get(field_key)
        if column is None:
            raise InvalidSortField(
                f"Cannot sort by '{field_key}'. Allowed: {', '.join(SORTABLE_FIELDS)}",
                details={"field": field_key, "allowed": list(SORTABLE_FIELDS)},
            )

        order_column = column.desc() if descending else column.asc()
        order_clause = order_column.nulls_last()

        conditions = []
        if search:
            like = f"%{search}%"
            conditions.append(or_(Token.symbol.ilike(like), Token.name.ilike(like)))
        if chain is not None:
            conditions.append(Token.chain == chain)
        if min_liquidity is not None:
            conditions.append(Token.liquidity_usd >= min_liquidity)
        if min_volume is not None:
            conditions.append(Token.volume_24h_usd >= min_volume)
        if created_within_hours is not None:
            cutoff = datetime.now(UTC) - timedelta(hours=created_within_hours)
            conditions.append(Token.pair_created_at >= cutoff)

        base_query = select(Token).outerjoin(AlphaScore, Token.id == AlphaScore.token_id)
        count_query = select(func.count()).select_from(Token).outerjoin(AlphaScore, Token.id == AlphaScore.token_id)
        for condition in conditions:
            base_query = base_query.where(condition)
            count_query = count_query.where(condition)

        total = (await self.session.execute(count_query)).scalar_one()

        paged_query = (
            base_query.order_by(order_clause)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        tokens = list((await self.session.execute(paged_query)).scalars().all())

        return tokens, total
