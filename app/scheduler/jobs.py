from __future__ import annotations

from app.collectors.dexscreener_provider import DexScreenerProvider
from app.collectors.geckoterminal_provider import GeckoTerminalProvider
from app.core.database.session import async_session_factory
from app.repositories.token_repository import TokenRepository
from app.services.token_ingestion_service import TokenIngestionService
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.services.ranking_service import RankingService
from app.repositories.contract_security_repository import ContractSecurityRepository


async def refresh_dexscreener() -> dict[str, int]:
    provider = DexScreenerProvider()
    try:
        async with async_session_factory() as session:
            repo = TokenRepository(session)
            snapshot_repo = TokenSnapshotRepository(session)
            service = TokenIngestionService([provider], repo, snapshot_repo)
            results = await service.ingest_all()
            await session.commit()
            return results
    finally:
        await provider.close()


async def refresh_geckoterminal() -> dict[str, int]:
    provider = GeckoTerminalProvider()
    try:
        async with async_session_factory() as session:
            repo = TokenRepository(session)
            snapshot_repo = TokenSnapshotRepository(session)
            service = TokenIngestionService([provider], repo, snapshot_repo)
            results = await service.ingest_all()
            await session.commit()
            return results
    finally:
        await provider.close()
        

async def compute_alpha_scores() -> dict[str, int]:
    async with async_session_factory() as session:
        token_repo = TokenRepository(session)
        snapshot_repo = TokenSnapshotRepository(session)
        alpha_score_repo = AlphaScoreRepository(session)
        contract_security_repo = ContractSecurityRepository(session)
        service = RankingService(token_repo, snapshot_repo, alpha_score_repo, contract_security_repo)
        count = await service.compute_all()
        await session.commit()
        return {"tokens_scored": count}