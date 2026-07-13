from __future__ import annotations

import typer
from alembic import command
from alembic.config import Config

db_app = typer.Typer(help="Database migration commands (thin wrapper over Alembic).")


def _alembic_config() -> Config:
    return Config("alembic.ini")


@db_app.command("upgrade")
def upgrade(revision: str = typer.Argument("head")) -> None:
    """Apply migrations up to REVISION (default: head)."""
    command.upgrade(_alembic_config(), revision)
    typer.secho(f"Database upgraded to '{revision}'", fg="green")


@db_app.command("downgrade")
def downgrade(
    revision: str = typer.Argument(..., help="Revision to downgrade to, e.g. '-1'."),
) -> None:
    """Downgrade to REVISION. No default target -- downgrading is
    destructive enough that it shouldn't have an implicit one."""
    if not typer.confirm(f"This will downgrade the database to '{revision}'. Continue?"):
        raise typer.Abort()
    command.downgrade(_alembic_config(), revision)
    typer.secho(f"Database downgraded to '{revision}'", fg="yellow")


@db_app.command("current")
def current() -> None:
    """Show the current migration revision."""
    command.current(_alembic_config(), verbose=True)