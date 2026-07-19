from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

from app.models.chain import Chain
from app.schemas.token import TokenCreate
from app.services.token_ingestion_service import TokenIngestionService


class _PassAllProvider:
    name = "pass-all"

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        return [
            TokenCreate(
                chain=Chain.BASE,
                contract_address="0xgood1",
                name="Good1",
                symbol="GD1",
                liquidity_usd=Decimal("50000"),
                volume_24h_usd=Decimal("1000"),
            ),
        ]


class _JunkProvider:
    name = "junk-only"

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        return [
            TokenCreate(
                chain=Chain.BASE,
                contract_address="0xjunk1",
                name="Junk1",
                symbol="JNK1",
                liquidity_usd=Decimal("1"),
                volume_24h_usd=Decimal("1"),
            ),
            TokenCreate(
                chain=Chain.BASE,
                contract_address="0xjunk2",
                name="Junk2",
                symbol="JNK2",
                liquidity_usd=Decimal("5"),
                volume_24h_usd=None,
            ),
            TokenCreate(
                chain=Chain.BASE,
                contract_address="0xjunk3",
                name="Junk3",
                symbol="JNK3",
                liquidity_usd=None,
                volume_24h_usd=Decimal("2"),
            ),
            TokenCreate(
                chain=Chain.SOLANA,
                contract_address="0xgood3",
                name="Good3",
                symbol="GD3",
                liquidity_usd=Decimal("50000"),
                volume_24h_usd=Decimal("2000"),
            ),
        ]


async def test_ingest_all_skips_tokens_failing_quality_gate():
    repository = AsyncMock()
    snapshot_repository = AsyncMock()
    provider = _JunkProvider()

    service = TokenIngestionService([provider], repository, snapshot_repository)
    results = await service.ingest_all()

    assert results == {"junk-only": 1}
    assert repository.upsert.call_count == 1
    assert repository.upsert.call_args[0][0].contract_address == "0xgood3"


async def test_ingest_all_passes_tokens_above_threshold():
    repository = AsyncMock()
    snapshot_repository = AsyncMock()
    provider = _PassAllProvider()

    service = TokenIngestionService([provider], repository, snapshot_repository)
    results = await service.ingest_all()

    assert results == {"pass-all": 1}
    repository.upsert.assert_awaited_once()


async def test_ingest_all_zero_tokens():
    repository = AsyncMock()
    snapshot_repository = AsyncMock()

    class _EmptyProvider:
        name = "empty"

        async def fetch_latest_tokens(self) -> list[TokenCreate]:
            return []

    service = TokenIngestionService([_EmptyProvider()], repository, snapshot_repository)
    results = await service.ingest_all()

    assert results == {"empty": 0}
    repository.upsert.assert_not_awaited()
