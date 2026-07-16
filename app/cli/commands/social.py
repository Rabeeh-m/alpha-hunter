from __future__ import annotations

import asyncio
from uuid import UUID

import typer

from app.collectors.telegram_client import TelegramClient
from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.social_snapshot_repository import SocialSnapshotRepository
from app.repositories.token_repository import TokenRepository
from app.services.social_intelligence_service import NoTelegramLinkAvailable, SocialIntelligenceService

social_app = typer.Typer(help="On-demand social signal scanning (Telegram only -- see docs on Twitter/X exclusion).")


@social_app.command("scan")
def scan(token_id: str) -> None:
    configure_logging()
    asyncio.run(_run(UUID(token_id)))


async def _run(token_id: UUID) -> None:
    client = TelegramClient()
    try:
        async with async_session_factory() as session:
            token_repo = TokenRepository(session)
            token = await token_repo.get_by_id(token_id)
            if token is None:
                typer.secho(f"Token '{token_id}' not found", fg="red")
                raise typer.Exit(code=1)

            snapshot_repo = SocialSnapshotRepository(session)
            score_repo = SocialScoreRepository(session)
            service = SocialIntelligenceService(client, snapshot_repo, score_repo)
            try:
                score = await service.scan_token(token)
                await session.commit()
                typer.secho(f"Scanned {token.symbol}: social_score={score}", fg="green")
            except NoTelegramLinkAvailable as exc:
                typer.secho(str(exc), fg="red")
                raise typer.Exit(code=1) from exc
    finally:
        await client.close()