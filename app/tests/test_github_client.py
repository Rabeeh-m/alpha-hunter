from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.collectors.github_client import GitHubClient, extract_owner_repo


class TestExtractOwnerRepo:
    def test_standard_url(self):
        assert extract_owner_repo("https://github.com/owner/repo") == ("owner", "repo")

    def test_with_git_suffix(self):
        assert extract_owner_repo("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_with_subdomain(self):
        assert extract_owner_repo("https://github.com/owner/repo/issues") == ("owner", "repo")

    def test_non_github_url(self):
        assert extract_owner_repo("https://gitlab.com/owner/repo") is None

    def test_empty_string(self):
        assert extract_owner_repo("") is None


@pytest.fixture
def mock_cache(monkeypatch):
    monkeypatch.setattr("app.collectors.github_client.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.collectors.github_client.cache_set", AsyncMock())


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url="https://api.github.com") as client:
        yield client


class TestGitHubClient:
    @respx.mock
    async def test_get_repo_parses_response(self, http_client, mock_cache):
        respx.get("https://api.github.com/repos/owner/repo").mock(
            return_value=httpx.Response(
                200,
                json={
                    "stargazers_count": 42,
                    "forks_count": 7,
                    "open_issues_count": 2,
                    "fork": False,
                    "archived": False,
                    "pushed_at": None,
                },
            )
        )
        client = GitHubClient(http_client=http_client)
        repo = await client.get_repo("owner", "repo")
        assert repo is not None
        assert repo.stargazers_count == 42
        assert repo.forks_count == 7
        assert repo.open_issues_count == 2

    @respx.mock
    async def test_get_repo_returns_none_on_404(self, http_client, mock_cache):
        respx.get("https://api.github.com/repos/owner/repo").mock(return_value=httpx.Response(404))
        client = GitHubClient(http_client=http_client)
        repo = await client.get_repo("owner", "repo")
        assert repo is None

    @respx.mock
    async def test_get_repo_raises_on_other_http_error(self, http_client, mock_cache):
        respx.get("https://api.github.com/repos/owner/repo").mock(return_value=httpx.Response(403))
        client = GitHubClient(http_client=http_client)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_repo("owner", "repo")

    @respx.mock
    async def test_get_contributor_count_estimate(self, http_client, mock_cache):
        respx.get(
            "https://api.github.com/repos/owner/repo/contributors?per_page=100&anon=false"
        ).mock(return_value=httpx.Response(200, json=[{}, {}, {}]))
        client = GitHubClient(http_client=http_client)
        count = await client.get_contributor_count_estimate("owner", "repo")
        assert count == 3

    @respx.mock
    async def test_get_contributor_count_returns_zero_on_non_200(self, http_client, mock_cache):
        respx.get(
            "https://api.github.com/repos/owner/repo/contributors?per_page=100&anon=false"
        ).mock(return_value=httpx.Response(403))
        client = GitHubClient(http_client=http_client)
        count = await client.get_contributor_count_estimate("owner", "repo")
        assert count == 0

    @respx.mock
    async def test_get_release_count(self, http_client, mock_cache):
        respx.get("https://api.github.com/repos/owner/repo/releases?per_page=30").mock(
            return_value=httpx.Response(200, json=[{}, {}])
        )
        client = GitHubClient(http_client=http_client)
        count = await client.get_release_count("owner", "repo")
        assert count == 2

    @respx.mock
    async def test_get_release_count_returns_zero_on_non_200(self, http_client, mock_cache):
        respx.get("https://api.github.com/repos/owner/repo/releases?per_page=30").mock(
            return_value=httpx.Response(403)
        )
        client = GitHubClient(http_client=http_client)
        count = await client.get_release_count("owner", "repo")
        assert count == 0

    @respx.mock
    async def test_retry_then_succeeds_after_transient_error(self, http_client, mock_cache):
        call_count = 0

        def _handler(request):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TransportError("connection reset")
            return httpx.Response(
                200, json={"stargazers_count": 1, "forks_count": 0, "open_issues_count": 0}
            )

        respx.get("https://api.github.com/repos/owner/repo").mock(side_effect=_handler)
        client = GitHubClient(http_client=http_client)
        repo = await client.get_repo("owner", "repo")
        assert repo is not None
        assert call_count == 2
