from __future__ import annotations

from app.collectors.dexscreener_provider import DexScreenerProvider
from app.collectors.geckoterminal_provider import GeckoTerminalProvider
from app.core.database.session import async_session_factory
from app.repositories.token_repository import TokenRepository
from app.services.token_ingestion_service import TokenIngestionService
from app.repositories.token_snapshot_repository import TokenSnapshotRepository


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