from __future__ import annotations

import asyncio

import typer

from app.collectors.dexscreener_provider import DexScreenerProvider
from app.collectors.geckoterminal_provider import GeckoTerminalProvider
from app.core.database.session import async_session_factory
from app.core.logging import configure_logging, get_logger
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.services.token_ingestion_service import TokenIngestionService

log = get_logger(__name__)


def ingest(
    provider: str = typer.Option(
        "all", help="Which provider to run: 'dexscreener', 'geckoterminal', or 'all'."
    ),
) -> None:
    """Run one ingestion cycle immediately, outside the scheduler.

    Equivalent to what the scheduled jobs do every 90s. Useful for manual
    backfills or verifying a provider works before waiting for the next
    interval. Replaces the old scripts/manual_ingest_check.py.
    """
    configure_logging()
    asyncio.run(_run(provider))


async def _run(provider: str) -> None:
    dexscreener = DexScreenerProvider()
    geckoterminal = GeckoTerminalProvider()
    providers = []
    if provider in ("dexscreener", "all"):
        providers.append(dexscreener)
    if provider in ("geckoterminal", "all"):
        providers.append(geckoterminal)
    if not providers:
        typer.secho(f"Unknown provider '{provider}'. Use dexscreener, geckoterminal, or all.", fg="red")
        raise typer.Exit(code=1)

    try:
        async with async_session_factory() as session:
            repo = TokenRepository(session)
            snapshot_repo = TokenSnapshotRepository(session)
            service = TokenIngestionService(providers, repo, snapshot_repo)
            results = await service.ingest_all()
            await session.commit()

        for name, count in results.items():
            typer.secho(f"{name}: {count} tokens ingested", fg="green")
    finally:
        await dexscreener.close()
        await geckoterminal.close()