from __future__ import annotations

import asyncio

import typer

from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.services.ranking_service import RankingService


def rank() -> None:
    """Run one alpha-scoring pass immediately, outside the scheduler."""
    configure_logging()
    asyncio.run(_run())


async def _run() -> None:
    async with async_session_factory() as session:
        token_repo = TokenRepository(session)
        snapshot_repo = TokenSnapshotRepository(session)
        alpha_repo = AlphaScoreRepository(session)
        service = RankingService(token_repo, snapshot_repo, alpha_repo)
        count = await service.compute_all()
        await session.commit()

    typer.secho(f"Scored {count} tokens", fg="green")