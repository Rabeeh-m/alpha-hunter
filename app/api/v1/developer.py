from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.github_client import GitHubClient
from app.core.database import get_db
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.developer import DeveloperActivityRead
from app.services.developer_intelligence_service import (
    DeveloperIntelligenceService, NoRepoLinkAvailable, RepoNotFound,
)

router = APIRouter(prefix="/tokens/{token_id}/developer", tags=["developer"])


@router.get("", response_model=DeveloperActivityRead)
async def get_token_developer_activity(token_id: UUID, db: AsyncSession = Depends(get_db)) -> DeveloperActivityRead:
    repo = DeveloperActivityRepository(db)
    record = await repo.get_by_token_id(token_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No scan yet -- call POST .../developer/scan first")
    return DeveloperActivityRead.model_validate(record)


@router.post("/scan")
async def scan_token_developer_activity(token_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    token_repo = TokenRepository(db)
    token = await token_repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    client = GitHubClient()
    try:
        repo = DeveloperActivityRepository(db)
        service = DeveloperIntelligenceService(client, repo)
        score = await service.scan_token(token)
        await db.commit()
        return {"status": "complete", "score": score}
    except (NoRepoLinkAvailable, RepoNotFound) as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc
    finally:
        await client.close()