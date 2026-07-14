from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.goplus_client import GoPlusClient
from app.core.database import get_db
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.contract_security import ContractSecurityRead
from app.services.contract_security_service import ContractSecurityService, UnsupportedChainForSecurityScan

router = APIRouter(prefix="/tokens/{token_id}/security", tags=["contract-security"])


@router.get("", response_model=ContractSecurityRead)
async def get_token_security(token_id: UUID, db: AsyncSession = Depends(get_db)) -> ContractSecurityRead:
    repo = ContractSecurityRepository(db)
    record = await repo.get_by_token_id(token_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No security scan yet -- call POST .../security/scan first")
    return ContractSecurityRead.model_validate(record)


@router.post("/scan")
async def scan_token_security(token_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    token_repo = TokenRepository(db)
    token = await token_repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    client = GoPlusClient()
    try:
        repo = ContractSecurityRepository(db)
        service = ContractSecurityService(client, repo)
        safety_score = await service.scan_token(token)
        await db.commit()
        return {"status": "complete", "safety_score": safety_score}
    except UnsupportedChainForSecurityScan as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc
    finally:
        await client.close()