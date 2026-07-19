from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from app.cli.main import app
from app.scheduler.jobs import refresh_dexscreener
from app.scheduler.registry import JobDefinition, job_registry

runner = CliRunner()


def test_cli_help_lists_all_subcommands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "rank" in result.output
    assert "jobs" in result.output
    assert "db" in result.output


def test_jobs_subcommand_help():
    result = runner.invoke(app, ["jobs", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "run" in result.output


def test_db_subcommand_help():
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    assert "upgrade" in result.output


def test_jobs_run_unknown_job_exits_nonzero():
    result = runner.invoke(app, ["jobs", "run", "not-a-real-job-id"])
    assert result.exit_code == 1
    assert "Unknown job" in result.output


@patch("app.cli.commands.jobs.async_session_factory")
def test_jobs_list_shows_last_run(mock_factory):
    job_registry._jobs.clear()
    test_job = JobDefinition(
        id="test-ingest-job",
        name="Test Ingest",
        description="",
        category="test",
        func=refresh_dexscreener,
        interval_seconds=60,
    )
    job_registry.register(test_job)

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_factory.return_value = mock_session

    fake_run = MagicMock(spec=["status", "started_at"])
    fake_run.status = MagicMock(value="success")
    fake_run.started_at = datetime(2026, 7, 19, 12, 0, 0, tzinfo=UTC)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = fake_run
    mock_session.execute.return_value = mock_result

    with patch("app.cli.commands.jobs.register_jobs", lambda: None):
        result = runner.invoke(app, ["jobs", "list"])

    assert result.exit_code == 0
    assert "test-ingest-job" in result.output
    assert "Test Ingest" in result.output
    assert "success" in result.output
    assert "2026-07-19" in result.output
    job_registry._jobs.clear()


def test_jobs_list_shows_never_run_when_no_job_run():
    job_registry._jobs.clear()
    test_job = JobDefinition(
        id="test-never-run-job",
        name="Never Run",
        description="",
        category="test",
        func=refresh_dexscreener,
        interval_seconds=60,
    )
    job_registry.register(test_job)

    with patch("app.cli.commands.jobs.async_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_factory.return_value = mock_session
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.cli.commands.jobs.register_jobs", lambda: None):
            result = runner.invoke(app, ["jobs", "list"])

    assert result.exit_code == 0
    assert "test-never-run-job" in result.output
    assert "Never Run" in result.output
    assert "never run" in result.output
    job_registry._jobs.clear()
