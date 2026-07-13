from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.logging import get_logger
from app.models.token import Token
from app.ranking.scoring import (
    ScoreBreakdown,
    age_score,
    liquidity_growth_score,
    liquidity_score,
    market_cap_score,
    volume_score,
)
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository

log = get_logger(__name__)


class RankingService:
    """Orchestrates score computation: pulls a token's current state plus
    its 24h snapshot history, runs it through the pure scoring functions,
    and persists the result. Never talks to APIs or the scheduler directly."""

    def __init__(
        self,
        token_repository: TokenRepository,
        snapshot_repository: TokenSnapshotRepository,
        alpha_score_repository: AlphaScoreRepository,
    ) -> None:
        self._token_repo = token_repository
        self._snapshot_repo = snapshot_repository
        self._alpha_score_repo = alpha_score_repository

    async def compute_for_token(self, token: Token) -> Decimal:
        since = datetime.now(UTC) - timedelta(hours=24)
        snapshots = await self._snapshot_repo.list_for_token(token.id, since=since)
        earliest_liquidity = snapshots[0].liquidity_usd if snapshots else None

        breakdown = ScoreBreakdown(
            liquidity=liquidity_score(token.liquidity_usd),
            volume=volume_score(token.volume_24h_usd),
            market_cap=market_cap_score(token.market_cap_usd),
            age=age_score(token.created_at, datetime.now(UTC)),
            liquidity_growth=liquidity_growth_score(earliest_liquidity, token.liquidity_usd),
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