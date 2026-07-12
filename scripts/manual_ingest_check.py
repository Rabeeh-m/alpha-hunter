import asyncio

from app.collectors.dexscreener_provider import DexScreenerProvider
from app.collectors.geckoterminal_provider import GeckoTerminalProvider
from app.core.database.session import async_session_factory
from app.repositories.token_repository import TokenRepository
from app.services.token_ingestion_service import TokenIngestionService


async def main() -> None:
    dexscreener = DexScreenerProvider()
    geckoterminal = GeckoTerminalProvider()

    async with async_session_factory() as session:
        repo = TokenRepository(session)
        service = TokenIngestionService([dexscreener, geckoterminal], repo)
        results = await service.ingest_all()
        await session.commit()
        print(f"Ingestion results: {results}")

    await dexscreener.close()
    await geckoterminal.close()


asyncio.run(main())