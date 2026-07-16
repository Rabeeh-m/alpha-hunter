from __future__ import annotations

import typer

from app.cli.commands import db as db_commands
from app.cli.commands import ingest as ingest_commands
from app.cli.commands import jobs as jobs_commands
from app.cli.commands import rank as rank_commands
from app.cli.commands import wallets as wallets_commands
from app.cli.commands import security as security_commands
from app.cli.commands import whales as whales_commands
from app.cli.commands import social as social_commands


app = typer.Typer(
    name="alpha-hunter",
    help="Alpha Hunter management CLI -- ingestion, ranking, jobs, and database commands.",
    no_args_is_help=True,
)

app.add_typer(jobs_commands.jobs_app, name="jobs")
app.add_typer(db_commands.db_app, name="db")
app.command(name="ingest")(ingest_commands.ingest)
app.command(name="rank")(rank_commands.rank)
app.add_typer(wallets_commands.wallets_app, name="wallets")
app.add_typer(security_commands.security_app, name="security")
app.add_typer(whales_commands.whales_app, name="whales")
app.add_typer(social_commands.social_app, name="social")

if __name__ == "__main__":
    app()