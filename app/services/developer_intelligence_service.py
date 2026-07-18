from __future__ import annotations

from app.collectors.github_client import GitHubClient, extract_owner_repo
from app.core.exceptions import AlphaHunterError
from app.core.logging import get_logger
from app.developer.scoring import compute_developer_activity
from app.models.token import Token
from app.repositories.developer_activity_repository import DeveloperActivityRepository

log = get_logger(__name__)


class NoRepoLinkAvailable(AlphaHunterError):
    error_code = "NO_REPO_LINK_AVAILABLE"
    recoverable = False


class RepoNotFound(AlphaHunterError):
    error_code = "REPO_NOT_FOUND"
    recoverable = False


class DeveloperIntelligenceService:
    """On-demand, same pattern as every scan-triggered service since M11."""

    def __init__(self, client: GitHubClient, repository: DeveloperActivityRepository) -> None:
        self._client = client
        self._repository = repository

    async def scan_token(self, token: Token) -> int:
        if not token.github_url:
            raise NoRepoLinkAvailable(f"Token '{token.symbol}' has no known GitHub link", details={"token_id": str(token.id)})

        parsed = extract_owner_repo(token.github_url)
        if parsed is None:
            raise NoRepoLinkAvailable(f"Could not parse a repo path from '{token.github_url}'")
        owner, repo_name = parsed

        repo = await self._client.get_repo(owner, repo_name)
        if repo is None:
            raise RepoNotFound(f"GitHub repo '{owner}/{repo_name}' not found or inaccessible")

        contributor_count = await self._client.get_contributor_count_estimate(owner, repo_name)
        release_count = await self._client.get_release_count(owner, repo_name)

        result = compute_developer_activity(repo, contributor_count, release_count)
        await self._repository.upsert(token.id, result)

        log.info("developer_activity_scan_complete", token_id=str(token.id), symbol=token.symbol, score=result.score)
        return result.score