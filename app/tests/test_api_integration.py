from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from app.collectors.anthropic_client import AnthropicClassifierClient
from app.collectors.github_client import GitHubClient
from app.collectors.telegram_client import TelegramClient
from app.contracts.risk_scoring import compute_contract_risk
from app.core.database import Base, get_db
from app.developer.scoring import compute_developer_activity
from app.models.chain import Chain
from app.models.narrative_classification import Narrative
from app.models.token import Token
from app.models.wallet import WalletType
from app.models.whale_event import WhaleEvent, WhaleEventType
from app.repositories.contract_security_repository import ContractSecurityRepository
from app.repositories.developer_activity_repository import DeveloperActivityRepository
from app.repositories.narrative_repository import NarrativeRepository
from app.repositories.social_score_repository import SocialScoreRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.github import GitHubRepo
from app.schemas.goplus import GoPlusTokenSecurity
from app.social.telegram_parser import TelegramChannelStats

_TMPDIR = tempfile.mkdtemp(prefix="alpha_hunter_integration_")

URI = f"sqlite+aiosqlite:///{_TMPDIR}/integration.db"


@pytest.fixture(scope="session")
def integration_engine():
    engine = create_async_engine(URI, connect_args={"check_same_thread": False}, poolclass=NullPool)
    return engine


@pytest.fixture(scope="session", autouse=True)
async def init_integration_db(integration_engine):
    async with integration_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await integration_engine.dispose()


@pytest.fixture
async def db(integration_engine) -> AsyncIterator[AsyncSession]:
    connection = await integration_engine.connect()
    await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    await session.begin_nested()
    try:
        yield session
    except Exception:
        await session.rollback()
        await connection.rollback()
        raise
    else:
        await session.rollback()
        await connection.rollback()
    finally:
        await session.close()
        await connection.close()


@pytest.fixture
def app_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")


def _build_client(session):
    from collections.abc import AsyncGenerator

    from app.main import create_app

    @asynccontextmanager
    async def noop_lifespan(_app) -> AsyncGenerator[None]:
        yield

    app = create_app()
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides[get_db] = lambda: session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return app, client


# ---------------------------------------------------------------------------
# Wallets Router
# ---------------------------------------------------------------------------


@pytest.fixture
async def wallet_token(db: AsyncSession) -> Token:
    repo = TokenRepository(db)
    return await repo.add(
        Token(
            chain=Chain.BASE,
            contract_address="0xwallettest",
            name="Wallet Token",
            symbol="WLT",
            price_usd=Decimal("1"),
        )
    )


@pytest.fixture
async def seeded_wallet_holdings(db: AsyncSession, wallet_token: Token) -> Token:
    wallet_repo = WalletRepository(db)
    holding_repo = WalletHoldingRepository(db)

    w1 = await wallet_repo.get_or_create(Chain.BASE, "0xwhale1", WalletType.WHALE, Decimal("90"))
    w2 = await wallet_repo.get_or_create(Chain.BASE, "0xwhale2", WalletType.WHALE, Decimal("85"))
    w3 = await wallet_repo.get_or_create(
        Chain.BASE, "0xunknown1", WalletType.UNKNOWN, Decimal("30")
    )
    await db.flush()

    await holding_repo.upsert(wallet_token.id, w1.id, Decimal("50000"), 1)
    await holding_repo.upsert(wallet_token.id, w2.id, Decimal("30000"), 2)
    await holding_repo.upsert(wallet_token.id, w3.id, Decimal("10000"), 3)
    await db.flush()
    return wallet_token


@pytest.mark.usefixtures("app_env")
async def test_wallets_list_returns_top_holders(db, seeded_wallet_holdings):
    _, client = _build_client(db)
    token = seeded_wallet_holdings
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/wallets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["rank"] == 1
    assert data[0]["address"] == "0xwhale1"
    assert data[0]["wallet_type"] == "whale"


@pytest.mark.usefixtures("app_env")
async def test_wallets_list_returns_empty_when_never_scanned(db, wallet_token):
    _, client = _build_client(db)
    token = wallet_token
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/wallets")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.usefixtures("app_env")
async def test_wallets_scan_persists_holders(db, wallet_token):
    token = wallet_token

    mock_response = {
        "status": "1",
        "result": [
            {
                "from": "0xmint",
                "to": "0xfound",
                "value": "1000000000000000000000",
                "tokenDecimal": "18",
            },
            {
                "from": "0xmint",
                "to": "0xfound2",
                "value": "500000000000000000000",
                "tokenDecimal": "18",
            },
        ],
    }

    with respx.mock:
        respx.get(url__startswith="https://api.etherscan.io/v2/api").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        _, client = _build_client(db)
        async with client:
            resp = await client.post(f"/api/v1/tokens/{token.id}/wallets/scan")

    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"
    assert resp.json()["holders_found"] == 2

    holding_repo = WalletHoldingRepository(db)
    holdings = await holding_repo.list_for_token(token.id)
    assert len(holdings) == 2


@pytest.mark.usefixtures("app_env")
async def test_wallets_scan_returns_404_for_missing_token(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.post(f"/api/v1/tokens/{fake_id}/wallets/scan")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_wallets_scan_returns_400_for_unsupported_chain(db):
    repo = TokenRepository(db)
    sol_token = await repo.add(
        Token(chain=Chain.SOLANA, contract_address="soltest", name="Sol Test", symbol="SOLT")
    )
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.post(f"/api/v1/tokens/{sol_token.id}/wallets/scan")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Whale Events
# ---------------------------------------------------------------------------


@pytest.fixture
async def seeded_whale_event(db: AsyncSession) -> Token:
    token_repo = TokenRepository(db)
    token = await token_repo.add(
        Token(chain=Chain.BASE, contract_address="0xwhaleevt", name="Whale Evt", symbol="WHE")
    )
    wallet_repo = WalletRepository(db)
    wallet = await wallet_repo.get_or_create(
        Chain.BASE, "0xbigfish", WalletType.WHALE, Decimal("95")
    )
    await db.flush()

    event = WhaleEvent(
        token_id=token.id,
        wallet_id=wallet.id,
        event_type=WhaleEventType.NEW_POSITION,
        previous_balance=None,
        new_balance=Decimal("100000"),
        change_pct=None,
        change_usd=Decimal("100000"),
    )
    db.add(event)

    event2 = WhaleEvent(
        token_id=token.id,
        wallet_id=wallet.id,
        event_type=WhaleEventType.INCREASED,
        previous_balance=Decimal("100000"),
        new_balance=Decimal("200000"),
        change_pct=Decimal("100"),
        change_usd=Decimal("100000"),
    )
    db.add(event2)
    await db.flush()
    return token


@pytest.mark.usefixtures("app_env")
async def test_whales_recent_returns_events(db, seeded_whale_event):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/whales/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["event_type"] in ("new_position", "increased", "decreased")
    assert data[0]["token_symbol"] == "WHE"


@pytest.mark.usefixtures("app_env")
async def test_whales_recent_respects_limit(db, seeded_whale_event):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/whales/recent", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.usefixtures("app_env")
async def test_whales_recent_returns_empty_when_no_events(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/whales/recent")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.usefixtures("app_env")
async def test_token_whale_events_returns_events_for_token(db, seeded_whale_event):
    token = seeded_whale_event
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/wallets/whale-events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(e["token_symbol"] == "WHE" for e in data)


@pytest.mark.usefixtures("app_env")
async def test_token_whale_events_returns_empty_for_token_without_events(db):
    repo = TokenRepository(db)
    token = await repo.add(
        Token(
            chain=Chain.ETHEREUM, contract_address="0xwhaleempty", name="No Whale", symbol="NOWHALE"
        )
    )
    await db.flush()
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/wallets/whale-events")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Social Router
# ---------------------------------------------------------------------------


@pytest.fixture
async def social_token(db: AsyncSession) -> Token:
    repo = TokenRepository(db)
    return await repo.add(
        Token(
            chain=Chain.BASE,
            contract_address="0xsocialapi",
            name="Social API",
            symbol="SOCAPI",
            telegram_url="https://t.me/socialapitest",
        )
    )


@pytest.fixture
async def seeded_social_score(db: AsyncSession, social_token: Token) -> Token:
    repo = SocialScoreRepository(db)
    await repo.upsert(
        social_token.id,
        score=78,
        factor_breakdown={"member_size": 60, "activity": 18},
        possible_inorganic_growth=False,
    )
    await db.flush()
    return social_token


@pytest.mark.usefixtures("app_env")
async def test_social_get_returns_score(db, seeded_social_score):
    _, client = _build_client(db)
    token = seeded_social_score
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/social")
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 78
    assert data["possible_inorganic_growth"] is False
    assert "factor_breakdown" in data


@pytest.mark.usefixtures("app_env")
async def test_social_get_returns_404_when_not_scanned(db, social_token):
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{social_token.id}/social")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_social_scan_persists_score(db, social_token):
    token = social_token

    mock_client = AsyncMock(spec=TelegramClient)
    mock_client.get_channel_stats.return_value = TelegramChannelStats(
        member_count=5000, message_count_24h=40
    )
    mock_client.close = AsyncMock()

    import app.api.v1.social as social_module

    original_client = social_module.TelegramClient
    social_module.TelegramClient = lambda: mock_client

    try:
        _, client = _build_client(db)
        async with client:
            resp = await client.post(f"/api/v1/tokens/{token.id}/social/scan")
        assert resp.status_code == 200
        assert resp.json()["status"] == "complete"

        repo = SocialScoreRepository(db)
        record = await repo.get_by_token_id(token.id)
        assert record is not None
        assert record.score > 0
    finally:
        social_module.TelegramClient = original_client


@pytest.mark.usefixtures("app_env")
async def test_social_scan_returns_404_for_missing_token(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.post(f"/api/v1/tokens/{fake_id}/social/scan")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_social_scan_returns_400_when_no_telegram_link(db):
    repo = TokenRepository(db)
    token = await repo.add(
        Token(chain=Chain.BASE, contract_address="0xnosocial", name="No Social", symbol="NOSOC")
    )
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.post(f"/api/v1/tokens/{token.id}/social/scan")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Developer Router
# ---------------------------------------------------------------------------


@pytest.fixture
async def dev_token(db: AsyncSession) -> Token:
    repo = TokenRepository(db)
    return await repo.add(
        Token(
            chain=Chain.BASE,
            contract_address="0xdevapi",
            name="Dev API",
            symbol="DEVAPI",
            github_url="https://github.com/test/repo",
        )
    )


@pytest.fixture
async def seeded_dev_activity(db: AsyncSession, dev_token: Token) -> Token:
    repo = DeveloperActivityRepository(db)
    github_repo = GitHubRepo(
        stargazers_count=150,
        forks_count=30,
        pushed_at=datetime.now(UTC),
        fork=False,
        archived=False,
    )
    result = compute_developer_activity(github_repo, contributor_count=8, release_count=5)
    await repo.upsert(dev_token.id, result)
    await db.flush()
    return dev_token


@pytest.mark.usefixtures("app_env")
async def test_developer_get_returns_activity(db, seeded_dev_activity):
    _, client = _build_client(db)
    token = seeded_dev_activity
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/developer")
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] > 0
    assert data["stars"] == 150
    assert data["is_archived"] is False
    assert data["is_fork"] is False


@pytest.mark.usefixtures("app_env")
async def test_developer_get_returns_404_when_not_scanned(db, dev_token):
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{dev_token.id}/developer")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_developer_scan_persists_score(db, dev_token):
    token = dev_token

    mock_client = AsyncMock(spec=GitHubClient)
    mock_client.get_repo.return_value = GitHubRepo(
        stargazers_count=200,
        forks_count=40,
        pushed_at=datetime.now(UTC),
        fork=False,
        archived=False,
    )
    mock_client.get_contributor_count_estimate.return_value = 10
    mock_client.get_release_count.return_value = 8
    mock_client.close = AsyncMock()

    import app.api.v1.developer as dev_module

    original_client = dev_module.GitHubClient
    dev_module.GitHubClient = lambda: mock_client

    try:
        _, client = _build_client(db)
        async with client:
            resp = await client.post(f"/api/v1/tokens/{token.id}/developer/scan")
        assert resp.status_code == 200
        assert resp.json()["status"] == "complete"

        repo = DeveloperActivityRepository(db)
        record = await repo.get_by_token_id(token.id)
        assert record is not None
        assert record.score > 0
    finally:
        dev_module.GitHubClient = original_client


@pytest.mark.usefixtures("app_env")
async def test_developer_scan_returns_404_for_missing_token(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.post(f"/api/v1/tokens/{fake_id}/developer/scan")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_developer_scan_returns_400_when_no_github_link(db):
    repo = TokenRepository(db)
    token = await repo.add(
        Token(chain=Chain.BASE, contract_address="0xnodev", name="No Dev", symbol="NODEV")
    )
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.post(f"/api/v1/tokens/{token.id}/developer/scan")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Contract Security Router
# ---------------------------------------------------------------------------


@pytest.fixture
async def security_token(db: AsyncSession) -> Token:
    repo = TokenRepository(db)
    return await repo.add(
        Token(chain=Chain.BASE, contract_address="0xsecapi", name="Sec API", symbol="SECAPI")
    )


@pytest.fixture
async def seeded_security(db: AsyncSession, security_token: Token) -> Token:
    risk = compute_contract_risk(GoPlusTokenSecurity(is_open_source="1"))
    repo = ContractSecurityRepository(db)
    await repo.upsert(security_token.id, risk)
    await db.flush()
    return security_token


@pytest.mark.usefixtures("app_env")
async def test_security_get_returns_analysis(db, seeded_security):
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{seeded_security.id}/security")
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety_score"] >= 90
    assert data["is_open_source"] is True
    assert isinstance(data["flags"], list)


@pytest.mark.usefixtures("app_env")
async def test_security_get_returns_404_when_not_scanned(db, security_token):
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{security_token.id}/security")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_security_scan_persists_analysis(db, security_token):
    token = security_token

    mock_response = {
        "code": 1,
        "message": "OK",
        "result": {token.contract_address.lower(): {"is_open_source": "1"}},
    }

    with respx.mock:
        respx.get(url__startswith="https://api.gopluslabs.io").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        _, client = _build_client(db)
        async with client:
            resp = await client.post(f"/api/v1/tokens/{token.id}/security/scan")

    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"

    repo = ContractSecurityRepository(db)
    record = await repo.get_by_token_id(token.id)
    assert record is not None
    assert record.safety_score > 0


@pytest.mark.usefixtures("app_env")
async def test_security_scan_returns_404_for_missing_token(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.post(f"/api/v1/tokens/{fake_id}/security/scan")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_security_scan_returns_400_for_unsupported_chain(db):
    repo = TokenRepository(db)
    sol_token = await repo.add(
        Token(chain=Chain.SOLANA, contract_address="solnosec", name="Sol No Sec", symbol="SOLNS")
    )
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.post(f"/api/v1/tokens/{sol_token.id}/security/scan")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Narratives Router
# ---------------------------------------------------------------------------


def _unique_contract(prefix: str = "0x") -> str:
    return f"{prefix}{uuid4().hex[:16]}"


@pytest.fixture
async def narrative_token(db: AsyncSession) -> Token:
    repo = TokenRepository(db)
    return await repo.add(
        Token(
            chain=Chain.BASE, contract_address=_unique_contract(), name="Narr API", symbol="NARRAPI"
        )
    )


@pytest.fixture
async def seeded_narrative(db: AsyncSession, narrative_token: Token) -> Token:
    repo = NarrativeRepository(db)
    await repo.upsert(
        narrative_token.id, Narrative.DEFI, Decimal("0.92"), "Strong DeFi patterns detected"
    )
    await db.flush()
    return narrative_token


@pytest.mark.usefixtures("app_env")
async def test_narrative_get_returns_classification(db, seeded_narrative):
    _, client = _build_client(db)
    token = seeded_narrative
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/narrative")
    assert resp.status_code == 200
    data = resp.json()
    assert data["primary_narrative"] == "defi"
    assert float(data["confidence"]) == 0.92
    assert "reasoning" in data


@pytest.mark.usefixtures("app_env")
async def test_narrative_get_returns_404_when_not_classified(db, narrative_token):
    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{narrative_token.id}/narrative")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_narrative_classify_persists_result(db):
    repo = TokenRepository(db)
    token = await repo.add(
        Token(
            chain=Chain.BASE, contract_address=_unique_contract(), name="Narr API", symbol="NARRAPI"
        )
    )
    await db.flush()

    mock_client = AsyncMock(spec=AnthropicClassifierClient)
    mock_client.classify.return_value = type(
        "NarrativeResult",
        (),
        {"primary_narrative": Narrative.AI, "confidence": 85, "reasoning": "AI narrative detected"},
    )()
    mock_client.close = AsyncMock()

    import app.api.v1.narratives as narr_module

    original_client = narr_module.AnthropicClassifierClient
    narr_module.AnthropicClassifierClient = lambda: mock_client

    try:
        _, client = _build_client(db)
        async with client:
            resp = await client.post(f"/api/v1/tokens/{token.id}/narrative/classify")
        assert resp.status_code == 200
        assert resp.json()["status"] == "complete"

        record = await NarrativeRepository(db).get_by_token_id(token.id)
        assert record is not None
        assert record.primary_narrative == Narrative.AI
    finally:
        narr_module.AnthropicClassifierClient = original_client


@pytest.mark.usefixtures("app_env")
async def test_narrative_classify_returns_404_for_missing_token(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.post(f"/api/v1/tokens/{fake_id}/narrative/classify")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_narrative_classify_returns_502_on_classification_failure(db):
    repo = TokenRepository(db)
    token = await repo.add(
        Token(
            chain=Chain.ETHEREUM,
            contract_address=_unique_contract(),
            name="Fail Token",
            symbol="FAIL",
        )
    )
    await db.flush()

    mock_client = AsyncMock(spec=AnthropicClassifierClient)
    mock_client.classify.side_effect = ValueError("API error")
    mock_client.close = AsyncMock()

    import app.api.v1.narratives as narr_module

    original_client = narr_module.AnthropicClassifierClient
    narr_module.AnthropicClassifierClient = lambda: mock_client

    try:
        _, client = _build_client(db)
        async with client:
            resp = await client.post(f"/api/v1/tokens/{token.id}/narrative/classify")
        assert resp.status_code == 502
    finally:
        narr_module.AnthropicClassifierClient = original_client


@pytest.mark.usefixtures("app_env")
async def test_narrative_distribution_returns_counts(db):
    repo = NarrativeRepository(db)
    token_repo = TokenRepository(db)
    token1 = await token_repo.add(
        Token(chain=Chain.BASE, contract_address=_unique_contract(), name="Narr1", symbol="NR1")
    )
    token2 = await token_repo.add(
        Token(chain=Chain.ETHEREUM, contract_address=_unique_contract(), name="Narr2", symbol="NR2")
    )
    await db.flush()
    await repo.upsert(token1.id, Narrative.DEFI, Decimal("0.92"), "Defi patterns")
    await repo.upsert(token2.id, Narrative.MEME, Decimal("0.88"), "Meme patterns")
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/narratives/distribution")
    assert resp.status_code == 200
    data = resp.json()
    assert data["defi"] == 1
    assert data["meme"] == 1


@pytest.mark.usefixtures("app_env")
async def test_narrative_distribution_returns_empty_when_none_classified(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/narratives/distribution")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)
