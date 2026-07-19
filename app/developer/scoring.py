from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime

WEIGHTS: dict[str, float] = {
    "popularity": 0.25,
    "freshness": 0.35,  # highest weight -- "actively worked on right now" is
    "contributors": 0.25,  # more actionable for scam-detection than raw star count
    "releases": 0.15,
}

FORK_PENALTY_MULTIPLIER = 0.5  # flat penalty, not zero -- a fork CAN still have
# real original work; the flag alone isn't proof of nothing
ARCHIVED_PENALTY_MULTIPLIER = (
    0.3  # much harsher -- archived means development has definitively stopped
)


def repo_popularity_score(stars: int, forks: int) -> float:
    """1 -> 0, 1000 -> 100. Forks weighted 2x stars -- a fork implies
    someone valued the code enough to build on it, a stronger signal
    than a star click."""
    weighted = stars + forks * 2
    if weighted <= 0:
        return 0.0
    normalized = (math.log10(max(weighted, 1)) - math.log10(1)) / (math.log10(1000) - math.log10(1))
    return max(0.0, min(100.0, normalized * 100))


def repo_freshness_score(pushed_at: datetime | None, now: datetime) -> float:
    """100 at 0 days since last push, 0 at 180+ days. A longer decay
    window than age_score's 30 days (M8) -- code development naturally
    happens on a slower cadence than token price/liquidity."""
    if pushed_at is None:
        return 0.0
    days_since = (now - pushed_at).total_seconds() / 86400
    return max(0.0, min(100.0, 100.0 * (1 - days_since / 180)))


def contributor_count_score(count: int) -> float:
    """1 -> 0, 50 -> 100. See GitHubClient.get_contributor_count_estimate
    docstring -- this is fed an approximation, capped at 100."""
    if count <= 0:
        return 0.0
    normalized = (math.log10(count) - math.log10(1)) / (math.log10(50) - math.log10(1))
    return max(0.0, min(100.0, normalized * 100))


def release_activity_score(release_count: int) -> float:
    """0 -> 0, 10+ -> 100. Linear, not log -- release counts are
    naturally small numbers where log-scaling would compress too
    aggressively to be useful."""
    return max(0.0, min(100.0, (release_count / 10) * 100))


@dataclass
class DeveloperActivityResult:
    score: int
    flags: list[str] = field(default_factory=list)
    stars: int = 0
    forks: int = 0
    contributors_count: int = 0
    last_commit_at: datetime | None = None
    is_fork: bool = False
    is_archived: bool = False


def compute_developer_activity(
    repo, contributor_count: int, release_count: int, now: datetime | None = None
) -> DeveloperActivityResult:
    now = now or datetime.now(UTC)
    flags: list[str] = []

    raw_score = (
        repo_popularity_score(repo.stargazers_count, repo.forks_count) * WEIGHTS["popularity"]
        + repo_freshness_score(repo.pushed_at, now) * WEIGHTS["freshness"]
        + contributor_count_score(contributor_count) * WEIGHTS["contributors"]
        + release_activity_score(release_count) * WEIGHTS["releases"]
    )

    if repo.fork:
        raw_score *= FORK_PENALTY_MULTIPLIER
        flags.append(
            "Repository is a fork -- GitHub API does not cheaply expose how much "
            "original work diverges from the parent (not implemented); treat as a "
            "flag worth manual review, not proof of an unmodified template"
        )

    if repo.archived:
        raw_score *= ARCHIVED_PENALTY_MULTIPLIER
        flags.append("Repository is archived -- no further development is possible")

    if not flags:
        flags.append("No significant developer-activity concerns detected")

    return DeveloperActivityResult(
        score=round(max(0.0, min(100.0, raw_score))),
        flags=flags,
        stars=repo.stargazers_count,
        forks=repo.forks_count,
        contributors_count=contributor_count,
        last_commit_at=repo.pushed_at,
        is_fork=repo.fork,
        is_archived=repo.archived,
    )
