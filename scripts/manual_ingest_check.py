# scripts/manual_ingest_check.py
import asyncio
from app.collectors.dexscreener_client import DexScreenerClient
from app.core.database.session import async_session_factory
from app.repositories.token_repository import TokenRepository
from app.services.token_ingestion_service import TokenIngestionService

async def main():
    client = DexScreenerClient()
    async with async_session_factory() as session:
        repo = TokenRepository(session)
        service = TokenIngestionService(client, repo)
        count = await service.ingest_latest_tokens()
        await session.commit()
        print(f"Ingested {count} tokens")
    await client.close()

asyncio.run(main())