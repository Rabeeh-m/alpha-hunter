from __future__ import annotations

import re

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.cache import cache_get, cache_set
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.github import GitHubRepo

log = get_logger(__name__)

BASE_URL = "https://api.github.com"
_REPO_PATH_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def extract_owner_repo(github_url: str) -> tuple[str, str] | None:
    match = _REPO_PATH_RE.search(github_url)
    if match is None:
        return None
    owner, repo = match.group(1), match.group(2).removesuffix(".git")
    return owner, repo


class GitHubClient:
    """Real rate limit here (60/hr unauth, 5000/hr with GITHUB_TOKEN) --
    unlike Telegram scraping in M16, caching genuinely protects quota,
    same reasoning as DexScreener/GeckoTerminal (M3/M4). Dev activity
    metrics also change slowly, supporting a long TTL."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token.get_secret_value()}"
        self._client = http_client or httpx.AsyncClient(
            base_url=BASE_URL, headers=headers, timeout=10.0
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TransportError,)),
        reraise=True,
    )
    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        return await self._client.get(path, params=params or {})

    async def get_repo(self, owner: str, repo: str) -> GitHubRepo | None:
        cache_key = f"github:repo:{owner}/{repo}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return GitHubRepo.model_validate(cached) if cached else None

        response = await self._get(f"/repos/{owner}/{repo}")
        if response.status_code == 404:
            await cache_set(cache_key, {}, ttl_seconds=86400)
            return None
        response.raise_for_status()
        parsed = GitHubRepo.model_validate(response.json())
        await cache_set(cache_key, parsed.model_dump(mode="json"), ttl_seconds=86400)
        return parsed

    async def get_contributor_count_estimate(self, owner: str, repo: str) -> int:
        """APPROXIMATION: returns len() of the first page (100 max), not
        the true total -- following pagination fully would cost extra
        API calls for a number only used in a log-scale score where the
        exact value past ~30 barely moves the result anyway."""
        cache_key = f"github:contributors:{owner}/{repo}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached

        response = await self._get(
            f"/repos/{owner}/{repo}/contributors", params={"per_page": 100, "anon": "false"}
        )
        if response.status_code != 200:
            return 0
        count = len(response.json())
        await cache_set(cache_key, count, ttl_seconds=86400)
        return count

    async def get_release_count(self, owner: str, repo: str) -> int:
        cache_key = f"github:releases:{owner}/{repo}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached

        response = await self._get(f"/repos/{owner}/{repo}/releases", params={"per_page": 30})
        if response.status_code != 200:
            return 0
        count = len(response.json())
        await cache_set(cache_key, count, ttl_seconds=86400)
        return count

    async def close(self) -> None:
        await self._client.aclose()
