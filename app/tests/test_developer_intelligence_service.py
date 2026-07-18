from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.collectors.github_client import GitHubClient
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.github import GitHubRepo
from app.services.developer_intelligence_service import DeveloperIntelligenceService, NoRepoLinkAvailable


async def test_scan_token_raises_without_github_link(db_session: AsyncSession):
    token_repo = TokenRepository(db_session)
    token = await token_repo.add(Token(chain=Chain.BASE, contract_address="0xnorepo", name="No Repo", symbol="NOREP"))

    client = GitHubClient()
    repo = DeveloperActivityRepository(db_session)
    service = DeveloperIntelligenceService(client, repo)

    with pytest.raises(NoRepoLinkAvailable):
        await service.scan_token(token)


async def test_scan_token_persists_score_with_mocked_client(db_session: AsyncSession):
    token_repo = TokenRepository(db_session)
    token = await token_repo.add(
        Token(chain=Chain.BASE, contract_address="0xdev", name="Dev Coin", symbol="DEV", github_url="https://github.com/acme/dev-coin")
    )

    client = AsyncMock(spec=GitHubClient)
    client.get_repo.return_value = GitHubRepo(stargazers_count=200, forks_count=20, pushed_at=datetime.now(UTC))
    client.get_contributor_count_estimate.return_value = 8
    client.get_release_count.return_value = 3

    repo = DeveloperActivityRepository(db_session)
    service = DeveloperIntelligenceService(client, repo)
    score = await service.scan_token(token)

    assert 0 <= score <= 100
    record = await repo.get_by_token_id(token.id)
    assert record.is_fork is False