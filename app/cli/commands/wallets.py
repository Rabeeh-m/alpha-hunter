from __future__ import annotations

import asyncio
from uuid import UUID

import typer

from app.collectors.etherscan_client import EtherscanClient
from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet_discovery_service import (
    UnsupportedChainForWalletScan,
    WalletDiscoveryService,
)

wallets_app = typer.Typer(help="On-demand wallet/holder scanning.")


@wallets_app.command("scan")
def scan(token_id: str) -> None:
    """Scan a token's recent transfers for top approximate holders.
    NOT automatic -- costs an external API call, run manually per token."""
    configure_logging()
    asyncio.run(_run(UUID(token_id)))


async def _run(token_id: UUID) -> None:
    client = EtherscanClient()
    try:
        async with async_session_factory() as session:
            token_repo = TokenRepository(session)
            token = await token_repo.get_by_id(token_id)
            if token is None:
                typer.secho(f"Token '{token_id}' not found", fg="red")
                raise typer.Exit(code=1)

            wallet_repo = WalletRepository(session)
            holding_repo = WalletHoldingRepository(session)
            service = WalletDiscoveryService(client, wallet_repo, holding_repo)

            try:
                count = await service.scan_token(token)
                await session.commit()
                typer.secho(f"Scanned {token.symbol}: {count} holders found", fg="green")
            except UnsupportedChainForWalletScan as exc:
                typer.secho(str(exc), fg="red")
                raise typer.Exit(code=1) from exc
    finally:
        await client.close()
