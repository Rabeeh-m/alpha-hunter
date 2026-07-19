from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.developer.scoring import compute_developer_activity
from app.schemas.github import GitHubRepo


def test_fresh_active_repo_scores_well():
    repo = GitHubRepo(stargazers_count=500, forks_count=50, pushed_at=datetime.now(UTC))
    result = compute_developer_activity(repo, contributor_count=10, release_count=5)
    assert result.score > 50


def test_stale_repo_scores_poorly():
    repo = GitHubRepo(
        stargazers_count=500, forks_count=50, pushed_at=datetime.now(UTC) - timedelta(days=400)
    )
    result = compute_developer_activity(repo, contributor_count=10, release_count=5)
    assert result.score < 50


def test_fork_flag_applies_penalty_not_zero():
    base_repo = GitHubRepo(
        stargazers_count=100, forks_count=10, pushed_at=datetime.now(UTC), fork=False
    )
    forked_repo = GitHubRepo(
        stargazers_count=100, forks_count=10, pushed_at=datetime.now(UTC), fork=True
    )

    base_result = compute_developer_activity(base_repo, contributor_count=5, release_count=2)
    fork_result = compute_developer_activity(forked_repo, contributor_count=5, release_count=2)

    assert 0 < fork_result.score < base_result.score
    assert fork_result.is_fork is True


def test_archived_repo_penalized_harder_than_fork():
    archived = GitHubRepo(
        stargazers_count=100, forks_count=10, pushed_at=datetime.now(UTC), archived=True
    )
    forked = GitHubRepo(
        stargazers_count=100, forks_count=10, pushed_at=datetime.now(UTC), fork=True
    )

    archived_result = compute_developer_activity(archived, contributor_count=5, release_count=2)
    fork_result = compute_developer_activity(forked, contributor_count=5, release_count=2)

    assert archived_result.score < fork_result.score


def test_no_push_date_scores_zero_freshness():
    repo = GitHubRepo(stargazers_count=0, forks_count=0, pushed_at=None)
    result = compute_developer_activity(repo, contributor_count=0, release_count=0)
    assert result.score == 0
