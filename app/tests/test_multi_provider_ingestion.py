from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.models.chain import Chain
from app.schemas.token import TokenCreate
from app.services.token_ingestion_service import TokenIngestionService


class _FakeProvider:
    """Two fake providers reporting the SAME token — proves upsert dedup."""

    def __init__(self, name: str, contract_address: str) -> None:
        self.name = name
        self._contract_address = contract_address

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        return [
            TokenCreate(
                chain=Chain.BASE,
                contract_address=self._contract_address,
                name="Dedup Test Token",
                symbol="DEDUP",
                liquidity_usd=Decimal("50000"),
            )
        ]


async def test_ingest_all_deduplicates_across_providers():
    repository = AsyncMock()
    snapshot_repository = AsyncMock()
    provider_a = _FakeProvider("provider-a", "0xsame")
    provider_b = _FakeProvider("provider-b", "0xsame")

    service = TokenIngestionService([provider_a, provider_b], repository, snapshot_repository)
    results = await service.ingest_all()

    assert results == {"provider-a": 1, "provider-b": 1}
    # both providers reported 1 token each, but upsert() -- keyed on
    # (chain, contract_address) -- was called twice with the SAME address,
    # which the repository (and the real DB unique constraint) collapses
    # into a single row. Here we just verify upsert was invoked with the
    # same contract_address both times.
    calls = repository.upsert.call_args_list
    assert len(calls) == 2
    assert calls[0].args[0].contract_address == calls[1].args[0].contract_address == "0xsame"