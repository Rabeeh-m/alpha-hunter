from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.telegram_client import TelegramClient
from app.core.database import get_db
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.social_snapshot_repository import SocialSnapshotRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.social import SocialScoreRead
from app.services.social_intelligence_service import NoTelegramLinkAvailable, SocialIntelligenceService

router = APIRouter(prefix="/tokens/{token_id}/social", tags=["social"])


@router.get("", response_model=SocialScoreRead)
async def get_token_social(token_id: UUID, db: AsyncSession = Depends(get_db)) -> SocialScoreRead:
    repo = SocialScoreRepository(db)
    record = await repo.get_by_token_id(token_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No social scan yet -- call POST .../social/scan first")
    return SocialScoreRead.model_validate(record)


@router.post("/scan")
async def scan_token_social(token_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    token_repo = TokenRepository(db)
    token = await token_repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    client = TelegramClient()
    try:
        snapshot_repo = SocialSnapshotRepository(db)
        score_repo = SocialScoreRepository(db)
        service = SocialIntelligenceService(client, snapshot_repo, score_repo)
        score = await service.scan_token(token)
        await db.commit()
        return {"status": "complete", "score": score}
    except NoTelegramLinkAvailable as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc
    finally:
        await client.close()