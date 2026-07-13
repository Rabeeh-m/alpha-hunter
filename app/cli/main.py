from __future__ import annotations

import typer

from app.cli.commands import db as db_commands
from app.cli.commands import ingest as ingest_commands
from app.cli.commands import jobs as jobs_commands
from app.cli.commands import rank as rank_commands

app = typer.Typer(
    name="alpha-hunter",
    help="Alpha Hunter management CLI -- ingestion, ranking, jobs, and database commands.",
    no_args_is_help=True,
)

app.add_typer(jobs_commands.jobs_app, name="jobs")
app.add_typer(db_commands.db_app, name="db")
app.command(name="ingest")(ingest_commands.ingest)
app.command(name="rank")(rank_commands.rank)


if __name__ == "__main__":
    app()