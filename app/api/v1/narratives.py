from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.anthropic_client import AnthropicClassifierClient
from app.core.database import get_db
from app.repositories.narrative_repository import NarrativeRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.narrative import NarrativeClassificationRead
from app.services.narrative_classification_service import NarrativeClassificationService

router = APIRouter(tags=["narratives"])


@router.get("/tokens/{token_id}/narrative", response_model=NarrativeClassificationRead)
async def get_token_narrative(
    token_id: UUID, db: AsyncSession = Depends(get_db)
) -> NarrativeClassificationRead:
    repo = NarrativeRepository(db)
    record = await repo.get_by_token_id(token_id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="Not classified yet -- call POST .../narrative/classify"
        )
    return NarrativeClassificationRead.model_validate(record)


@router.post("/tokens/{token_id}/narrative/classify")
async def classify_token_narrative(token_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    token_repo = TokenRepository(db)
    token = await token_repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    client = AnthropicClassifierClient()
    repo = NarrativeRepository(db)
    service = NarrativeClassificationService(client, repo)
    try:
        await service.classify_token(token)
        await db.commit()
        return {"status": "complete"}
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Classification failed: {exc}") from exc


@router.get("/narratives/distribution")
async def get_narrative_distribution(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Powers the Narratives sidebar page -- count of classified tokens per category."""
    repo = NarrativeRepository(db)
    return await repo.distribution()
