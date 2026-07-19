from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.etherscan_client import EtherscanClient
from app.core.database import get_db
from app.models.wallet import Wallet
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import WalletHoldingRead
from app.services.wallet_discovery_service import UnsupportedChainForWalletScan, WalletDiscoveryService
from app.repositories.whale_event_repository import WhaleEventRepository
from app.schemas.whale_event import WhaleEventRead

router = APIRouter(prefix="/tokens/{token_id}/wallets", tags=["wallets"])
whale_events_router = APIRouter(prefix="/whales", tags=["wallets"])

@router.get("", response_model=list[WalletHoldingRead])
async def list_token_wallets(token_id: UUID, db: AsyncSession = Depends(get_db)) -> list[WalletHoldingRead]:
    """Most recently scanned top holders. Empty list if never scanned --
    call POST .../scan first."""
    holding_repo = WalletHoldingRepository(db)
    holdings = await holding_repo.list_for_token(token_id)

    results = []
    for holding in holdings:
        wallet = await db.get(Wallet, holding.wallet_id)
        results.append(
            WalletHoldingRead(
                address=wallet.address, wallet_type=wallet.wallet_type,
                confidence_score=wallet.confidence_score, approximate_balance=holding.approximate_balance,
                rank=holding.rank, scanned_at=holding.scanned_at,
            )
        )
    return results


@router.post("/scan")
async def scan_token_wallets(token_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    """Triggers an on-demand scan. NOT automatic/scheduled -- see
    WalletDiscoveryService docstring for why."""
    token_repo = TokenRepository(db)
    token = await token_repo.get_by_id(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    client = EtherscanClient()
    try:
        wallet_repo = WalletRepository(db)
        holding_repo = WalletHoldingRepository(db)
        whale_event_repo = WhaleEventRepository(db)
        service = WalletDiscoveryService(client, wallet_repo, holding_repo, whale_event_repo)
        count = await service.scan_token(token)
        await db.commit()
        return {"status": "complete", "holders_found": count}
    except UnsupportedChainForWalletScan as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc
    finally:
        await client.close()
        

@whale_events_router.get("/recent", response_model=list[WhaleEventRead])
async def list_recent_whale_events(limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[WhaleEventRead]:
    """Platform-wide feed, newest first -- powers the Whales sidebar page."""
    repo = WhaleEventRepository(db)
    events = await repo.list_recent(limit=limit)
    return [WhaleEventRead.from_event(e) for e in events]


@router.get("/whale-events", response_model=list[WhaleEventRead])  # note: mounted on the existing `router`, so path is /tokens/{token_id}/wallets/whale-events
async def list_token_whale_events(token_id: UUID, limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[WhaleEventRead]:
    repo = WhaleEventRepository(db)
    events = await repo.list_for_token(token_id, limit=limit)
    return [WhaleEventRead.from_event(e) for e in events]