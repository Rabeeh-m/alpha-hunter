from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.logging import get_logger
from app.models.token import Token
from app.ranking.scoring import (
    ScoreBreakdown,
    age_score,
    contract_safety_score,
    developer_activity_score,
    liquidity_growth_score,
    liquidity_score,
    market_cap_score,
    social_signal_score,
    volume_score,
)
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository

log = get_logger(__name__)


class RankingService:
    def __init__(
        self,
        token_repository: TokenRepository,
        snapshot_repository: TokenSnapshotRepository,
        alpha_score_repository: AlphaScoreRepository,
        contract_security_repository: ContractSecurityRepository,
        social_score_repository: SocialScoreRepository,
        developer_activity_repository: DeveloperActivityRepository,
    ) -> None:
        self._token_repo = token_repository
        self._snapshot_repo = snapshot_repository
        self._alpha_score_repo = alpha_score_repository
        self._contract_security_repo = contract_security_repository
        self._social_score_repo = social_score_repository
        self._developer_activity_repo = developer_activity_repository

    async def compute_for_token(self, token: Token) -> Decimal:
        since = datetime.now(UTC) - timedelta(hours=24)
        snapshots = await self._snapshot_repo.list_for_token(token.id, since=since)
        earliest_liquidity = snapshots[0].liquidity_usd if snapshots else None

        security = await self._contract_security_repo.get_by_token_id(token.id)
        safety_score = security.safety_score if security is not None else None

        social = await self._social_score_repo.get_by_token_id(token.id)
        social_score_value = social.score if social is not None else None
        inorganic_flag = social.possible_inorganic_growth if social is not None else False

        dev_activity = await self._developer_activity_repo.get_by_token_id(token.id)
        dev_score_value = dev_activity.score if dev_activity is not None else None

        breakdown = ScoreBreakdown(
            liquidity=liquidity_score(token.liquidity_usd),
            volume=volume_score(token.volume_24h_usd),
            market_cap=market_cap_score(token.market_cap_usd),
            age=age_score(token.created_at, datetime.now(UTC)),
            liquidity_growth=liquidity_growth_score(earliest_liquidity, token.liquidity_usd),
            contract_safety=contract_safety_score(safety_score),
            social_signal=social_signal_score(social_score_value, inorganic_flag),
            developer_activity=developer_activity_score(dev_score_value),
        )

        score = Decimal(str(breakdown.composite))
        await self._alpha_score_repo.upsert(token.id, score, breakdown.to_dict())
        return score

    async def compute_all(self) -> int:
        # V1 scale limit: no batching/pagination yet. Fine up to roughly
        # a few thousand tokens; revisit once real volume shows this
        # single-pass approach is too slow for the 120s job interval.
        tokens = await self._token_repo.list_all(limit=1000)
        for token in tokens:
            await self.compute_for_token(token)
        log.info("ranking_pass_complete", tokens_scored=len(tokens))
        return len(tokens)
