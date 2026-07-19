from __future__ import annotations

import asyncio
from uuid import UUID

import typer

from app.collectors.goplus_client import GoPlusClient
from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.token_repository import TokenRepository
from app.services.contract_security_service import (
    ContractSecurityService,
    UnsupportedChainForSecurityScan,
)

security_app = typer.Typer(help="On-demand contract security scanning.")


@security_app.command("scan")
def scan(token_id: str) -> None:
    """Scan a token's contract for security risk flags."""
    configure_logging()
    asyncio.run(_run(UUID(token_id)))


async def _run(token_id: UUID) -> None:
    client = GoPlusClient()
    try:
        async with async_session_factory() as session:
            token_repo = TokenRepository(session)
            token = await token_repo.get_by_id(token_id)
            if token is None:
                typer.secho(f"Token '{token_id}' not found", fg="red")
                raise typer.Exit(code=1)

            repo = ContractSecurityRepository(session)
            service = ContractSecurityService(client, repo)
            try:
                score = await service.scan_token(token)
                await session.commit()
                color = "green" if score >= 70 else "yellow" if score >= 40 else "red"
                typer.secho(f"Scanned {token.symbol}: safety_score={score}", fg=color)
            except UnsupportedChainForSecurityScan as exc:
                typer.secho(str(exc), fg="red")
                raise typer.Exit(code=1) from exc
    finally:
        await client.close()
