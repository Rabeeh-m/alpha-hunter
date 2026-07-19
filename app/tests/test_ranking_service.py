from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.risk_scoring import compute_contract_risk
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.alpha_score_repository import AlphaScoreRepository
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository
from app.schemas.goplus import GoPlusTokenSecurity
from app.services.ranking_service import RankingService


@pytest.fixture
def mock_token() -> Token:
    return Token(
        chain=Chain.BASE,
        contract_address="0xcompute_all",
        name="All",
        symbol="ALL",
        liquidity_usd=Decimal("50000"),
        volume_24h_usd=Decimal("20000"),
        market_cap_usd=Decimal("500000"),
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_repos(mock_token):
    token_repo = AsyncMock(spec=TokenRepository)
    token_repo.list_all = AsyncMock(return_value=[mock_token, mock_token])

    snapshot_repo = AsyncMock(spec=TokenSnapshotRepository)
    snapshot_repo.list_for_token = AsyncMock(return_value=[])

    alpha_repo = AsyncMock(spec=AlphaScoreRepository)
    alpha_repo.upsert = AsyncMock()

    contract_security_repo = AsyncMock(spec=ContractSecurityRepository)
    contract_security_repo.get_by_token_id = AsyncMock(return_value=None)

    social_repo = AsyncMock(spec=SocialScoreRepository)
    social_repo.get_by_token_id = AsyncMock(return_value=None)

    dev_repo = AsyncMock(spec=DeveloperActivityRepository)
    dev_repo.get_by_token_id = AsyncMock(return_value=None)

    return {
        "token_repo": token_repo,
        "snapshot_repo": snapshot_repo,
        "alpha_repo": alpha_repo,
        "contract_security_repo": contract_security_repo,
        "social_repo": social_repo,
        "dev_repo": dev_repo,
    }


@pytest.fixture
async def seeded_token(db_session: AsyncSession) -> Token:
    repo = TokenRepository(db_session)
    token = Token(
        chain=Chain.BASE,
        contract_address="0xrank",
        name="Rank Coin",
        symbol="RANK",
        liquidity_usd=Decimal("50000"),
        volume_24h_usd=Decimal("20000"),
        market_cap_usd=Decimal("500000"),
    )
    return await repo.add(token)


async def test_compute_for_token_persists_score_and_breakdown(db_session, seeded_token):
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    contract_security_repo = ContractSecurityRepository(db_session)
    social_repo = SocialScoreRepository(db_session)
    dev_repo = DeveloperActivityRepository(db_session)
    service = RankingService(
        token_repo, snapshot_repo, alpha_repo, contract_security_repo, social_repo, dev_repo
    )

    score = await service.compute_for_token(seeded_token)
    await db_session.flush()
    await db_session.refresh(seeded_token, ["alpha_score"])

    assert 0 <= score <= 100
    saved = await alpha_repo.get_by_id(seeded_token.alpha_score.id)
    assert saved is not None
    assert "composite" in saved.factor_breakdown
    assert "liquidity" in saved.factor_breakdown


async def test_compute_for_token_is_idempotent_upsert(db_session, seeded_token):
    """Running the ranking pass twice must update the same row, not
    create a second one -- this is what makes alpha_scores current-state,
    not history."""
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    contract_security_repo = ContractSecurityRepository(db_session)
    social_repo = SocialScoreRepository(db_session)
    dev_repo = DeveloperActivityRepository(db_session)
    service = RankingService(
        token_repo, snapshot_repo, alpha_repo, contract_security_repo, social_repo, dev_repo
    )

    await service.compute_for_token(seeded_token)
    await db_session.refresh(seeded_token, ["alpha_score"])
    first_id = seeded_token.alpha_score.id

    await service.compute_for_token(seeded_token)
    await db_session.flush()
    await db_session.refresh(seeded_token, ["alpha_score"])

    assert seeded_token.alpha_score.id == first_id


async def test_honeypot_contract_drags_down_composite_score(db_session, seeded_token):
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    contract_security_repo = ContractSecurityRepository(db_session)
    social_repo = SocialScoreRepository(db_session)
    dev_repo = DeveloperActivityRepository(db_session)
    service = RankingService(
        token_repo, snapshot_repo, alpha_repo, contract_security_repo, social_repo, dev_repo
    )

    # Baseline: no security scan yet -> neutral 50 contract_safety factor
    baseline_score = await service.compute_for_token(seeded_token)

    # Now scan reveals a honeypot
    risk = compute_contract_risk(GoPlusTokenSecurity(is_honeypot="1", is_open_source="1"))
    await contract_security_repo.upsert(seeded_token.id, risk)
    await db_session.flush()

    honeypot_score = await service.compute_for_token(seeded_token)

    assert honeypot_score < baseline_score


async def test_inorganic_growth_flag_halves_social_contribution(db_session, seeded_token):
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    contract_security_repo = ContractSecurityRepository(db_session)
    social_repo = SocialScoreRepository(db_session)
    dev_repo = DeveloperActivityRepository(db_session)
    service = RankingService(
        token_repo, snapshot_repo, alpha_repo, contract_security_repo, social_repo, dev_repo
    )

    # Clean social score, no flag
    await social_repo.upsert(
        seeded_token.id, score=90, factor_breakdown={}, possible_inorganic_growth=False
    )
    await db_session.flush()
    clean_score = await service.compute_for_token(seeded_token)

    # Same raw score, but flagged as possibly inorganic
    await social_repo.upsert(
        seeded_token.id, score=90, factor_breakdown={}, possible_inorganic_growth=True
    )
    await db_session.flush()
    flagged_score = await service.compute_for_token(seeded_token)

    assert flagged_score < clean_score


async def test_developer_activity_none_defaults_to_neutral_without_crashing(
    db_session, seeded_token
):
    """A token with no developer scan at all (the common case per M19's
    coverage note) must still produce a valid composite score, not
    crash on a missing lookup."""
    token_repo = TokenRepository(db_session)
    snapshot_repo = TokenSnapshotRepository(db_session)
    alpha_repo = AlphaScoreRepository(db_session)
    contract_security_repo = ContractSecurityRepository(db_session)
    social_repo = SocialScoreRepository(db_session)
    dev_repo = DeveloperActivityRepository(db_session)
    service = RankingService(
        token_repo, snapshot_repo, alpha_repo, contract_security_repo, social_repo, dev_repo
    )

    score = await service.compute_for_token(seeded_token)
    await db_session.flush()
    await db_session.refresh(seeded_token, ["alpha_score"])

    assert 0 <= score <= 100
    saved = await alpha_repo.get_by_id(seeded_token.alpha_score.id)
    assert saved.factor_breakdown["developer_activity"]["score"] == 50.0


async def test_compute_all_with_tokens_returns_count(mock_repos):
    service = RankingService(
        mock_repos["token_repo"],
        mock_repos["snapshot_repo"],
        mock_repos["alpha_repo"],
        mock_repos["contract_security_repo"],
        mock_repos["social_repo"],
        mock_repos["dev_repo"],
    )
    count = await service.compute_all()

    assert count == 2
    mock_repos["token_repo"].list_all.assert_awaited_once_with(limit=1000)
    assert mock_repos["alpha_repo"].upsert.call_count == 2


async def test_compute_all_with_no_tokens_returns_zero(mock_repos):
    mock_repos["token_repo"].list_all = AsyncMock(return_value=[])

    service = RankingService(
        mock_repos["token_repo"],
        mock_repos["snapshot_repo"],
        mock_repos["alpha_repo"],
        mock_repos["contract_security_repo"],
        mock_repos["social_repo"],
        mock_repos["dev_repo"],
    )
    count = await service.compute_all()

    assert count == 0
    mock_repos["alpha_repo"].upsert.assert_not_awaited()
