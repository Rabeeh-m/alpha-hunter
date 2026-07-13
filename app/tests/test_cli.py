from __future__ import annotations

from typer.testing import CliRunner

from app.cli.main import app

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