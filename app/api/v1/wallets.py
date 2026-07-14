from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.etherscan_client import EtherscanClient
from app.core.database import get_db
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import WalletHoldingRead
from app.services.wallet_discovery_service import UnsupportedChainForWalletScan, WalletDiscoveryService

router = APIRouter(prefix="/tokens/{token_id}/wallets", tags=["wallets"])


@router.get("", response_model=list[WalletHoldingRead])
async def list_token_wallets(token_id: UUID, db: AsyncSession = Depends(get_db)) -> list[WalletHoldingRead]:
    """Most recently scanned top holders. Empty list if never scanned --
    call POST .../scan first."""
    holding_repo = WalletHoldingRepository(db)
    holdings = await holding_repo.list_for_token(token_id)

    results = []
    for holding in holdings:
        wallet = await holding_repo.session.get(holding.__class__.wallet_id.property.mapper.class_, holding.wallet_id)
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
        service = WalletDiscoveryService(client, wallet_repo, holding_repo)
        count = await service.scan_token(token)
        await db.commit()
        return {"status": "complete", "holders_found": count}
    except UnsupportedChainForWalletScan as exc:
        raise HTTPException(status_code=400, detail=exc.to_dict()) from exc
    finally:
        await client.close()