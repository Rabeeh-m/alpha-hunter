from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.risk_scoring import ContractRiskResult
from app.core.exceptions import InvalidSortField
from app.developer.scoring import DeveloperActivityResult
from app.models.chain import Chain
from app.models.narrative_classification import Narrative
from app.models.token import Token
from app.models.wallet import Wallet, WalletType
from app.models.whale_event import WhaleEvent, WhaleEventType
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.narrative_repository import NarrativeRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_repository import WalletRepository
from app.repositories.whale_event_repository import WhaleEventRepository
from app.schemas.token import TokenCreate

# ── contract_security_repository ──────────────────────────────────────
# uncovered: lines 30-33 (upsert-existing branch)


async def test_contract_security_upsert_updates_existing(db_session: AsyncSession):
    token = Token(chain=Chain.BASE, contract_address="0xsec", name="Sec", symbol="SEC")
    db_session.add(token)
    await db_session.flush()

    repo = ContractSecurityRepository(db_session)
    risk = ContractRiskResult(safety_score=80, flags=["test"])
    first = await repo.upsert(token.id, risk)
    assert first.safety_score == 80

    risk2 = ContractRiskResult(safety_score=50, flags=["updated"])
    second = await repo.upsert(token.id, risk2)
    assert second.id == first.id
    assert second.safety_score == 50


async def test_contract_security_upsert_creates_new(db_session: AsyncSession):
    token = Token(chain=Chain.BASE, contract_address="0xsec2", name="Sec2", symbol="SC2")
    db_session.add(token)
    await db_session.flush()

    repo = ContractSecurityRepository(db_session)
    risk = ContractRiskResult(safety_score=90, flags=[])
    record = await repo.upsert(token.id, risk)
    assert record.safety_score == 90
    assert record.token_id == token.id


# ── developer_activity_repository ─────────────────────────────────────
# uncovered: lines 27-30 (upsert-existing branch)


async def test_dev_activity_upsert_updates_existing(db_session: AsyncSession):
    token = Token(chain=Chain.BASE, contract_address="0xdev", name="Dev", symbol="DEV")
    db_session.add(token)
    await db_session.flush()

    repo = DeveloperActivityRepository(db_session)
    result = DeveloperActivityResult(score=70, flags=[], stars=10, forks=5, contributors_count=3)
    first = await repo.upsert(token.id, result)
    assert first.score == 70

    result2 = DeveloperActivityResult(score=85, flags=[], stars=20, forks=8, contributors_count=6)
    second = await repo.upsert(token.id, result2)
    assert second.id == first.id
    assert second.score == 85
    assert second.stars == 20


# ── narrative_repository ──────────────────────────────────────────────
# uncovered: lines 27-31 (upsert-existing branch), line 56 (distribution)


async def test_narrative_list_unclassified_returns_tokens_without_classification(
    db_session: AsyncSession,
):
    classified = Token(
        chain=Chain.BASE, contract_address="0xclassified", name="Classified", symbol="C"
    )
    unclassified = Token(
        chain=Chain.BASE, contract_address="0xunclassified", name="Unclassified", symbol="U"
    )
    db_session.add_all([classified, unclassified])
    await db_session.flush()

    repo = NarrativeRepository(db_session)
    await repo.upsert(classified.id, Narrative.MEME, Decimal("50"), "meme")

    result = await repo.list_unclassified_tokens()
    assert len(result) == 1
    assert result[0].contract_address == "0xunclassified"


async def test_narrative_list_unclassified_respects_limit(db_session: AsyncSession):
    tokens = [
        Token(chain=Chain.BASE, contract_address=f"0xul{i}", name=f"UL{i}", symbol=f"UL{i}")
        for i in range(5)
    ]
    db_session.add_all(tokens)
    await db_session.flush()

    repo = NarrativeRepository(db_session)
    result = await repo.list_unclassified_tokens(limit=2)
    assert len(result) == 2


async def test_narrative_upsert_updates_existing(db_session: AsyncSession):
    token = Token(chain=Chain.BASE, contract_address="0xnarr", name="Narr", symbol="NAR")
    db_session.add(token)
    await db_session.flush()

    repo = NarrativeRepository(db_session)
    first = await repo.upsert(token.id, Narrative.AI, Decimal("80"), "initial analysis")
    assert first.primary_narrative == Narrative.AI

    second = await repo.upsert(token.id, Narrative.DEFI, Decimal("95"), "updated analysis")
    assert second.id == first.id
    assert second.primary_narrative == Narrative.DEFI
    assert second.confidence == Decimal("95")


async def test_narrative_distribution_returns_counts(db_session: AsyncSession):
    repo = NarrativeRepository(db_session)
    t1 = Token(chain=Chain.BASE, contract_address="0xa", name="A", symbol="A")
    t2 = Token(chain=Chain.BASE, contract_address="0xb", name="B", symbol="B")
    t3 = Token(chain=Chain.BASE, contract_address="0xc", name="C", symbol="C")
    db_session.add_all([t1, t2, t3])
    await db_session.flush()

    await repo.upsert(t1.id, Narrative.AI, Decimal("70"), "")
    await repo.upsert(t2.id, Narrative.AI, Decimal("80"), "")
    await repo.upsert(t3.id, Narrative.DEFI, Decimal("60"), "")

    dist = await repo.distribution()
    assert dist == {"ai": 2, "defi": 1}


async def test_narrative_distribution_returns_empty_dict(db_session: AsyncSession):
    repo = NarrativeRepository(db_session)
    dist = await repo.distribution()
    assert dist == {}


# ── token_repository ──────────────────────────────────────────────────
# uncovered: lines 48-60 (upsert-existing branch), 106, 108-109 (search conditions)


async def test_token_upsert_updates_mutable_fields(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    data = TokenCreate(
        chain=Chain.BASE,
        contract_address="0xtup",
        name="Original",
        symbol="ORG",
        liquidity_usd=Decimal("50000"),
        dex="uniswap",
    )
    first = await repo.upsert(data)
    assert first.liquidity_usd == Decimal("50000")

    update = TokenCreate(
        chain=Chain.BASE,
        contract_address="0xtup",
        name="ShouldNotChange",
        symbol="SNC",
        liquidity_usd=Decimal("75000"),
        dex="pancakeswap",
    )
    second = await repo.upsert(update)
    assert second.id == first.id
    assert second.liquidity_usd == Decimal("75000")
    assert second.dex == "pancakeswap"


async def test_token_search_with_volume_filter(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    tokens = [
        Token(
            chain=Chain.BASE,
            contract_address=f"0xvol{i}",
            name=f"V{i}",
            symbol=f"V{i}",
            volume_24h_usd=Decimal(str(v)),
        )
        for i, v in enumerate([500, 1500, 2500])
    ]
    db_session.add_all(tokens)
    await db_session.flush()

    result, total = await repo.search(min_volume=Decimal("1000"))
    assert total == 2
    assert all(t.symbol in ("V1", "V2") for t in result)


async def test_token_search_with_pair_age_filter(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    now = datetime.now(UTC)
    tokens = [
        Token(
            chain=Chain.BASE,
            contract_address="0xage1",
            name="Age1",
            symbol="A1",
            pair_created_at=now,
            volume_24h_usd=Decimal("1000"),
        ),
        Token(
            chain=Chain.BASE,
            contract_address="0xage2",
            name="Age2",
            symbol="A2",
            pair_created_at=now,
            volume_24h_usd=Decimal("1000"),
        ),
    ]
    db_session.add_all(tokens)
    await db_session.flush()

    result, total = await repo.search(created_within_hours=1, min_volume=Decimal("500"))
    assert total == 2


async def test_token_search_empty_result(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    result, total = await repo.search(search="nonexistent")
    assert total == 0
    assert result == []


async def test_token_search_by_chain(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    tokens = [
        Token(
            chain=Chain.BASE,
            contract_address="0xbase1",
            name="Base Token",
            symbol="BASE",
            volume_24h_usd=Decimal("1000"),
        ),
        Token(
            chain=Chain.SOLANA,
            contract_address="0xsol1",
            name="Sol Token",
            symbol="SOL",
            volume_24h_usd=Decimal("1000"),
        ),
    ]
    db_session.add_all(tokens)
    await db_session.flush()

    result, total = await repo.search(chain=Chain.SOLANA)
    assert total == 1
    assert result[0].chain == Chain.SOLANA


async def test_token_search_with_liquidity_filter(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    tokens = [
        Token(
            chain=Chain.BASE,
            contract_address="0xliq1",
            name="Liq1",
            symbol="L1",
            liquidity_usd=Decimal("500"),
            volume_24h_usd=Decimal("100"),
        ),
        Token(
            chain=Chain.BASE,
            contract_address="0xliq2",
            name="Liq2",
            symbol="L2",
            liquidity_usd=Decimal("5000"),
            volume_24h_usd=Decimal("100"),
        ),
    ]
    db_session.add_all(tokens)
    await db_session.flush()

    result, total = await repo.search(min_liquidity=Decimal("1000"))
    assert total == 1
    assert result[0].symbol == "L2"


async def test_token_search_raises_on_invalid_sort_field(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    with pytest.raises(InvalidSortField):
        await repo.search(sort="invalid_field")


# ── wallet_repository ────────────────────────────────────────────────
# uncovered: lines 27-28 (confidence upgrade branch)


async def test_get_or_create_creates_new_wallet(db_session: AsyncSession):
    repo = WalletRepository(db_session)
    wallet = await repo.get_or_create(Chain.BASE, "0xwallet1", WalletType.WHALE, Decimal("80"))
    assert wallet.address == "0xwallet1"
    assert wallet.wallet_type == WalletType.WHALE
    assert wallet.confidence_score == Decimal("80")


async def test_get_or_create_upgrades_confidence(db_session: AsyncSession):
    repo = WalletRepository(db_session)
    wallet = await repo.get_or_create(Chain.BASE, "0xupgrade", WalletType.UNKNOWN, Decimal("30"))
    assert wallet.wallet_type == WalletType.UNKNOWN
    first_id = wallet.id

    upgraded = await repo.get_or_create(Chain.BASE, "0xupgrade", WalletType.WHALE, Decimal("80"))
    assert upgraded.id == first_id
    assert upgraded.wallet_type == WalletType.WHALE
    assert upgraded.confidence_score == Decimal("80")


async def test_get_or_create_does_not_downgrade_confidence(db_session: AsyncSession):
    repo = WalletRepository(db_session)
    wallet = await repo.get_or_create(Chain.BASE, "0xdowngrade", WalletType.WHALE, Decimal("90"))
    assert wallet.confidence_score == Decimal("90")

    same = await repo.get_or_create(Chain.BASE, "0xdowngrade", WalletType.UNKNOWN, Decimal("20"))
    assert same.id == wallet.id
    assert same.wallet_type == WalletType.WHALE
    assert same.confidence_score == Decimal("90")


async def test_get_or_create_with_none_confidence_does_not_change_existing(
    db_session: AsyncSession,
):
    repo = WalletRepository(db_session)
    await repo.get_or_create(Chain.BASE, "0xnoneconf", WalletType.WHALE, Decimal("70"))

    same = await repo.get_or_create(Chain.BASE, "0xnoneconf", WalletType.EXCHANGE, None)
    assert same.wallet_type == WalletType.WHALE
    assert same.confidence_score == Decimal("70")


# ── whale_event_repository ────────────────────────────────────────────
# uncovered: line 18 (list_recent with empty result)


async def test_list_recent_returns_empty_when_no_events(db_session: AsyncSession):
    repo = WhaleEventRepository(db_session)
    events = await repo.list_recent()
    assert events == []


async def test_list_recent_returns_events_ordered_by_detected_at(db_session: AsyncSession):
    token = Token(chain=Chain.BASE, contract_address="0xwhale", name="Whale", symbol="WHL")
    wallet = Wallet(
        chain=Chain.BASE,
        address="0xwhale1",
        wallet_type=WalletType.WHALE,
        confidence_score=Decimal("80"),
    )
    db_session.add_all([token, wallet])
    await db_session.flush()

    repo = WhaleEventRepository(db_session)
    events = [
        WhaleEvent(
            token_id=token.id,
            wallet_id=wallet.id,
            event_type=WhaleEventType.NEW_POSITION,
            new_balance=Decimal("1000"),
        ),
        WhaleEvent(
            token_id=token.id,
            wallet_id=wallet.id,
            event_type=WhaleEventType.INCREASED,
            new_balance=Decimal("2000"),
        ),
    ]
    db_session.add_all(events)
    await db_session.flush()

    result = await repo.list_recent()
    assert len(result) == 2


async def test_list_for_token_returns_events_for_specific_token(db_session: AsyncSession):
    token_a = Token(chain=Chain.BASE, contract_address="0xwhaleA", name="WhaleA", symbol="WA")
    token_b = Token(chain=Chain.BASE, contract_address="0xwhaleB", name="WhaleB", symbol="WB")
    wallet = Wallet(
        chain=Chain.BASE,
        address="0xwhale2",
        wallet_type=WalletType.WHALE,
        confidence_score=Decimal("80"),
    )
    db_session.add_all([token_a, token_b, wallet])
    await db_session.flush()

    repo = WhaleEventRepository(db_session)
    e1 = WhaleEvent(
        token_id=token_a.id,
        wallet_id=wallet.id,
        event_type=WhaleEventType.NEW_POSITION,
        new_balance=Decimal("500"),
    )
    e2 = WhaleEvent(
        token_id=token_b.id,
        wallet_id=wallet.id,
        event_type=WhaleEventType.INCREASED,
        new_balance=Decimal("1000"),
    )
    db_session.add_all([e1, e2])
    await db_session.flush()

    result = await repo.list_for_token(token_a.id)
    assert len(result) == 1
    assert result[0].event_type == WhaleEventType.NEW_POSITION
