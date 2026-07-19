from __future__ import annotations

from app.collectors.dexscreener_provider import DexScreenerProvider
from app.collectors.geckoterminal_provider import GeckoTerminalProvider
from app.collectors.github_client import GitHubClient
from app.core.database.session import async_session_factory
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.token_repository import TokenRepository
from app.services.developer_intelligence_service import DeveloperIntelligenceService, NoRepoLinkAvailable, RepoNotFound
from app.services.token_ingestion_service import TokenIngestionService
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.services.ranking_service import RankingService
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.blockchain.chain_ids import is_evm_chain
from app.collectors.etherscan_client import EtherscanClient
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.repositories.whale_event_repository import WhaleEventRepository
from app.services.wallet_discovery_service import WalletDiscoveryService
from app.collectors.telegram_client import TelegramClient
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.social_snapshot_repository import SocialSnapshotRepository
from app.services.social_intelligence_service import NoTelegramLinkAvailable, SocialIntelligenceService
from app.repositories.social_score_repository import SocialScoreRepository
from app.collectors.anthropic_client import AnthropicClassifierClient
from app.repositories.narrative_repository import NarrativeRepository
from app.services.narrative_classification_service import NarrativeClassificationService
from app.repositories.developer_activity_repository import DeveloperActivityRepository


NARRATIVE_CLASSIFICATION_BATCH_SIZE = 20
TOP_N_TOKENS_FOR_SOCIAL_MONITORING = 10
TOP_N_TOKENS_FOR_WHALE_MONITORING = 10  # bounded scope -- see milestone note on rate limits
TOP_N_TOKENS_FOR_DEVELOPER_MONITORING = 10

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
        

async def compute_alpha_scores() -> dict[str, int]:
    async with async_session_factory() as session:
        token_repo = TokenRepository(session)
        snapshot_repo = TokenSnapshotRepository(session)
        alpha_score_repo = AlphaScoreRepository(session)
        contract_security_repo = ContractSecurityRepository(session)
        social_score_repo = SocialScoreRepository(session)
        developer_activity_repo = DeveloperActivityRepository(session)
        service = RankingService(
            token_repo, snapshot_repo, alpha_score_repo, contract_security_repo,
            social_score_repo, developer_activity_repo,
        )
        count = await service.compute_all()
        await session.commit()
        return {"tokens_scored": count}
    

async def scan_top_tokens_for_whale_activity() -> dict[str, int]:
    """Automatic whale monitoring, DELIBERATELY BOUNDED to the top N
    tokens by alpha_score, not the full token universe -- unlimited
    scheduled scanning would scale Etherscan API usage with total token
    count, which the free tier can't sustain. This is the compromise
    between 'no automation at all' (M11's original stance) and 'true
    real-time for everything' (would need a paid tier)."""
    client = EtherscanClient()
    scanned = 0
    try:
        async with async_session_factory() as session:
            token_repo = TokenRepository(session)
            tokens, _ = await token_repo.search(sort="-alpha_score", page=1, page_size=TOP_N_TOKENS_FOR_WHALE_MONITORING)

            wallet_repo = WalletRepository(session)
            holding_repo = WalletHoldingRepository(session)
            whale_event_repo = WhaleEventRepository(session)
            service = WalletDiscoveryService(client, wallet_repo, holding_repo, whale_event_repo)

            for token in tokens:
                if not is_evm_chain(token.chain):
                    continue  # Solana still out of scope, see M11
                await service.scan_token(token)
                scanned += 1

            await session.commit()
    finally:
        await client.close()

    return {"tokens_scanned": scanned}


async def scan_top_tokens_for_social_activity() -> dict[str, int]:
    """Same bounded-top-10 compromise as M15's whale monitoring, applied
    here for consistency even though scraping has no formal rate limit
    to protect -- unbounded scanning of every token's Telegram channel
    every interval is still needlessly heavy traffic against a page not
    designed to serve that."""
    client = TelegramClient()
    scanned, skipped = 0, 0
    try:
        async with async_session_factory() as session:
            token_repo = TokenRepository(session)
            tokens, _ = await token_repo.search(sort="-alpha_score", page=1, page_size=TOP_N_TOKENS_FOR_SOCIAL_MONITORING)

            snapshot_repo = SocialSnapshotRepository(session)
            score_repo = SocialScoreRepository(session)
            service = SocialIntelligenceService(client, snapshot_repo, score_repo)

            for token in tokens:
                try:
                    await service.scan_token(token)
                    scanned += 1
                except NoTelegramLinkAvailable:
                    skipped += 1

            await session.commit()
    finally:
        await client.close()

    return {"tokens_scanned": scanned, "tokens_skipped_no_link": skipped}


async def classify_unclassified_narratives() -> dict[str, int]:
    """Bounded per-run batch, not top-N-rescan -- see the model/service
    docstrings for why this job's shape differs from every other
    scheduled scan in this codebase."""
    async with async_session_factory() as session:
        client = AnthropicClassifierClient()
        repo = NarrativeRepository(session)
        service = NarrativeClassificationService(client, repo)
        result = await service.classify_unclassified_batch(limit=NARRATIVE_CLASSIFICATION_BATCH_SIZE)
        await session.commit()
        return result


async def scan_top_tokens_for_developer_activity() -> dict[str, int]:
    client = GitHubClient()
    scanned, skipped = 0, 0
    try:
        async with async_session_factory() as session:
            token_repo = TokenRepository(session)
            tokens, _ = await token_repo.search(sort="-alpha_score", page=1, page_size=TOP_N_TOKENS_FOR_DEVELOPER_MONITORING)
            repo = DeveloperActivityRepository(session)
            service = DeveloperIntelligenceService(client, repo)
            for token in tokens:
                try:
                    await service.scan_token(token)
                    scanned += 1
                except (NoRepoLinkAvailable, RepoNotFound):
                    skipped += 1
            await session.commit()
    finally:
        await client.close()
    return {"tokens_scanned": scanned, "tokens_skipped": skipped}