from __future__ import annotations

from app.collectors.telegram_client import TelegramClient
from app.core.exceptions import AlphaHunterError
from app.core.logging import get_logger
from app.models.token import Token
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.social_snapshot_repository import SocialSnapshotRepository
from app.social.scoring import SocialBreakdown, activity_score, member_growth_signal, member_size_score

log = get_logger(__name__)


class NoTelegramLinkAvailable(AlphaHunterError):
    error_code = "NO_TELEGRAM_LINK_AVAILABLE"
    recoverable = False


class SocialIntelligenceService:
    """On-demand, like WalletDiscoveryService/ContractSecurityService --
    consistent with the established rate-limit-conscious pattern, even
    though scraping a public page has no formal quota to protect. The
    consistency itself has value: every 'scan' feature in this codebase
    behaves the same way from the caller's perspective."""

    def __init__(
        self,
        client: TelegramClient,
        snapshot_repository: SocialSnapshotRepository,
        score_repository: SocialScoreRepository,
    ) -> None:
        self._client = client
        self._snapshot_repo = snapshot_repository
        self._score_repo = score_repository

    async def scan_token(self, token: Token) -> int:
        if not token.telegram_url:
            raise NoTelegramLinkAvailable(
                f"Token '{token.symbol}' has no known Telegram link", details={"token_id": str(token.id)}
            )

        previous = await self._snapshot_repo.get_latest_for_token(token.id)
        stats = await self._client.get_channel_stats(token.telegram_url)

        member_count = stats.member_count if stats else None
        message_count = stats.message_count_24h if stats else None

        snapshot = self._snapshot_repo.model(
            token_id=token.id, member_count=member_count, message_count_24h=message_count
        )
        await self._snapshot_repo.add(snapshot)

        growth_score, inorganic_flag = member_growth_signal(
            previous.member_count if previous else None, member_count
        )
        breakdown = SocialBreakdown(
            member_size=member_size_score(member_count),
            activity=activity_score(message_count),
            member_growth=growth_score,
            possible_inorganic_growth=inorganic_flag,
        )

        await self._score_repo.upsert(token.id, breakdown.composite, breakdown.to_dict(), inorganic_flag)

        log.info(
            "social_scan_complete", token_id=str(token.id), symbol=token.symbol,
            member_count=member_count, score=breakdown.composite, inorganic_flag=inorganic_flag,
        )
        return breakdown.composite