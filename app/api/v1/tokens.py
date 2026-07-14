from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InvalidSortField
from app.models.chain import Chain
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.schemas.token import TokenPage, TokenRead, TokenSnapshotRead

if TYPE_CHECKING:
    pass

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=TokenPage)
async def list_tokens(
    search: str | None = Query(default=None, max_length=64),
    chain: Chain | None = Query(default=None),
    min_liquidity: Decimal | None = Query(default=None, ge=0),
    min_volume: Decimal | None = Query(default=None, ge=0),
    created_within_hours: int | None = Query(default=None, ge=1, le=720),
    sort: str = Query(default="-volume_24h_usd"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TokenPage:
    """Search/filter/sort/paginate discovered tokens.

    Unknown `sort` fields return 400, not a silent fallback to default
    ordering -- a client relying on a typo'd field deserves an explicit
    error, not quietly-wrong results.

    `created_within_hours` filters to tokens whose pair was created
    on-chain within the last N hours (uses `pair_created_at`).
    """
    repo = TokenRepository(db)
    try:
        tokens, total = await repo.search(
            search=search, chain=chain, min_liquidity=min_liquidity,
            min_volume=min_volume, created_within_hours=created_within_hours,
            sort=sort, page=page, page_size=page_size,
        )
    except InvalidSortField as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc

    total_pages = (total + page_size - 1) // page_size if total else 0

    return TokenPage(
        items=[TokenRead.from_token(t) for t in tokens],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/{token_id}", response_model=TokenRead)
async def get_token(token_id: UUID, db: AsyncSession = Depends(get_db)) -> TokenRead:
    repo = TokenRepository(db)
    token = await repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")
    return TokenRead.from_token(token)


@router.get("/{token_id}/snapshots", response_model=list[TokenSnapshotRead])
async def get_token_snapshots(
    token_id: UUID,
    hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
) -> list[TokenSnapshotRead]:
    """Historical readings for charting. Empty list (not 404) if the
    token exists but has no snapshots yet -- e.g. discovered less than
    one ingestion cycle ago."""
    token_repo = TokenRepository(db)
    token = await token_repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    snapshot_repo = TokenSnapshotRepository(db)
    since = datetime.now(UTC) - timedelta(hours=hours)
    snapshots = await snapshot_repo.list_for_token(token_id, since=since, limit=limit)
    return [TokenSnapshotRead.model_validate(s) for s in snapshots]
