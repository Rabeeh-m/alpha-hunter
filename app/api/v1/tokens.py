from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InvalidSortField
from app.models.chain import Chain
from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenPage, TokenRead

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=TokenPage)
async def list_tokens(
    search: str | None = Query(default=None, max_length=64),
    chain: Chain | None = Query(default=None),
    min_liquidity: Decimal | None = Query(default=None, ge=0),
    min_volume: Decimal | None = Query(default=None, ge=0),
    sort: str = Query(default="-created_at"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TokenPage:
    """Search/filter/sort/paginate discovered tokens.

    Unknown `sort` fields return 400, not a silent fallback to default
    ordering -- a client relying on a typo'd field deserves an explicit
    error, not quietly-wrong results.
    """
    repo = TokenRepository(db)
    try:
        tokens, total = await repo.search(
            search=search, chain=chain, min_liquidity=min_liquidity,
            min_volume=min_volume, sort=sort, page=page, page_size=page_size,
        )
    except InvalidSortField as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc

    total_pages = (total + page_size - 1) // page_size if total else 0

    return TokenPage(
        items=[TokenRead.model_validate(t) for t in tokens],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )