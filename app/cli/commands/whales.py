from __future__ import annotations

import asyncio

import typer

from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.repositories.whale_event_repository import WhaleEventRepository

whales_app = typer.Typer(help="Inspect detected whale activity.")


@whales_app.command("recent")
def recent(limit: int = 20) -> None:
    """Show the most recent whale events across all tokens."""
    configure_logging()
    asyncio.run(_run(limit))


async def _run(limit: int) -> None:
    async with async_session_factory() as session:
        repo = WhaleEventRepository(session)
        events = await repo.list_recent(limit=limit)

    if not events:
        typer.echo("No whale events detected yet.")
        return

    for e in events:
        sign = "+" if e.event_type.value in ("new_position", "increased") else "-"
        usd = f"${abs(e.change_usd):,.0f}" if e.change_usd else "?"
        label = e.wallet.label or e.wallet.address[:12]
        typer.echo(
            f"{e.detected_at.isoformat()}  {e.token.symbol:<10}"
            f" {e.event_type.value:<14} {sign}{usd}  {label}"
        )
