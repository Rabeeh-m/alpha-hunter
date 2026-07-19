from __future__ import annotations

import asyncio
from uuid import UUID

import typer

from app.collectors.anthropic_client import AnthropicClassifierClient
from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.repositories.narrative_repository import NarrativeRepository
from app.repositories.token_repository import TokenRepository
from app.services.narrative_classification_service import NarrativeClassificationService

narratives_app = typer.Typer(help="Token narrative classification.")


@narratives_app.command("classify")
def classify(token_id: str) -> None:
    configure_logging()
    asyncio.run(_run_single(UUID(token_id)))


async def _run_single(token_id: UUID) -> None:
    async with async_session_factory() as session:
        token_repo = TokenRepository(session)
        token = await token_repo.get_by_id(token_id)
        if token is None:
            typer.secho(f"Token '{token_id}' not found", fg="red")
            raise typer.Exit(code=1)

        client = AnthropicClassifierClient()
        repo = NarrativeRepository(session)
        service = NarrativeClassificationService(client, repo)
        await service.classify_token(token)
        await session.commit()

    typer.secho(f"Classified {token.symbol}", fg="green")


@narratives_app.command("classify-batch")
def classify_batch(limit: int = 20) -> None:
    """Classify up to LIMIT never-classified tokens. Same as the
    scheduled job, run on demand."""
    configure_logging()
    asyncio.run(_run_batch(limit))


async def _run_batch(limit: int) -> None:
    async with async_session_factory() as session:
        client = AnthropicClassifierClient()
        repo = NarrativeRepository(session)
        service = NarrativeClassificationService(client, repo)
        result = await service.classify_unclassified_batch(limit=limit)
        await session.commit()

    typer.secho(f"Classified: {result['classified']}, Failed: {result['failed']}", fg="green")
