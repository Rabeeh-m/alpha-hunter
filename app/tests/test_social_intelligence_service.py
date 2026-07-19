from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.telegram_client import TelegramClient
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.social_snapshot_repository import SocialSnapshotRepository
from app.repositories.token_repository import TokenRepository
from app.services.social_intelligence_service import (
    NoTelegramLinkAvailable,
    SocialIntelligenceService,
)
from app.social.telegram_parser import TelegramChannelStats


async def test_scan_token_raises_without_telegram_link(db_session: AsyncSession):
    token_repo = TokenRepository(db_session)
    token = await token_repo.add(
        Token(chain=Chain.BASE, contract_address="0xnolink", name="No Link", symbol="NOL")
    )

    client = TelegramClient()
    snapshot_repo = SocialSnapshotRepository(db_session)
    score_repo = SocialScoreRepository(db_session)
    service = SocialIntelligenceService(client, snapshot_repo, score_repo)

    with pytest.raises(NoTelegramLinkAvailable):
        await service.scan_token(token)


async def test_scan_token_persists_score_with_mocked_client(db_session: AsyncSession):
    token_repo = TokenRepository(db_session)
    token = await token_repo.add(
        Token(
            chain=Chain.BASE,
            contract_address="0xsocial",
            name="Social Coin",
            symbol="SOC",
            telegram_url="https://t.me/socialcoin",
        )
    )

    client = AsyncMock(spec=TelegramClient)
    client.get_channel_stats.return_value = TelegramChannelStats(
        member_count=5000, message_count_24h=40
    )

    snapshot_repo = SocialSnapshotRepository(db_session)
    score_repo = SocialScoreRepository(db_session)
    service = SocialIntelligenceService(client, snapshot_repo, score_repo)

    score = await service.scan_token(token)

    assert 0 <= score <= 100
    record = await score_repo.get_by_token_id(token.id)
    assert record is not None
    assert record.possible_inorganic_growth is False
