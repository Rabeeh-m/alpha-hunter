from __future__ import annotations

from typing import Protocol

from app.schemas.token import TokenCreate


class TokenProvider(Protocol):
    """Every collector adapter implements this. TokenIngestionService
    depends on this Protocol, not on any concrete client class — that's
    what lets us add a third, fourth, fifth provider later without
    touching the ingestion service at all."""

    name: str

    async def fetch_latest_tokens(self) -> list[TokenCreate]: ...
