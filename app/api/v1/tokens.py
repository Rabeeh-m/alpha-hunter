from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenRead

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=list[TokenRead])
async def list_tokens(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TokenRead]:
    """List discovered tokens, newest first.

    NOTE: search/filter/sort-by-column are NOT implemented here — that's
    Milestone 6's scope. This endpoint exists only so the frontend has a
    real data source instead of mocked data while the UI foundation is
    being built.
    """
    repo = TokenRepository(db)
    tokens = await repo.list_all(limit=limit, offset=offset)
    return [TokenRead.model_validate(t) for t in tokens]