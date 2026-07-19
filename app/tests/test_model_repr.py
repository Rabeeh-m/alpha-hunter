from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.models.alpha_score import AlphaScore
from app.models.chain import Chain
from app.models.contract_security import ContractSecurity
from app.models.job_run import JobRun, JobStatus
from app.models.narrative_classification import Narrative, NarrativeClassification
from app.models.social_score import SocialScore
from app.models.token import Token
from app.models.token_snapshot import TokenSnapshot
from app.models.wallet import Wallet, WalletType
from app.models.whale_event import WhaleEvent, WhaleEventType


def test_token_repr_contains_symbol_chain_and_address():
    t = Token(symbol="WETH", chain=Chain.ETHEREUM, contract_address="0x12345678901234567890")
    r = repr(t)
    assert "Token" in r
    assert "WETH" in r
    assert "ethereum" in r.lower()
    assert "0x12345678" in r


def test_wallet_repr_contains_address_chain_and_type():
    w = Wallet(
        chain=Chain.BASE,
        address="0xabcdef1234567890abcdef1234567890abcdef12",
        wallet_type=WalletType.WHALE,
    )
    r = repr(w)
    assert "Wallet" in r
    assert "0xabcdef12" in r
    assert "base" in r.lower()
    assert "whale" in r.lower()


def test_whale_event_repr_contains_type_token_id_and_wallet_id():
    tid = uuid4()
    wid = uuid4()
    e = WhaleEvent(
        token_id=tid,
        wallet_id=wid,
        event_type=WhaleEventType.NEW_POSITION,
        new_balance=Decimal("1000000"),
    )
    r = repr(e)
    assert "WhaleEvent" in r
    assert str(tid) in r
    assert str(wid) in r
    assert "new_position" in r.lower()


def test_alpha_score_repr_contains_token_id_and_score():
    tid = uuid4()
    a = AlphaScore(token_id=tid, score=Decimal("85.50"))
    r = repr(a)
    assert "AlphaScore" in r
    assert str(tid) in r
    assert "85.5" in r


def test_social_score_repr_contains_token_id_and_score():
    tid = uuid4()
    s = SocialScore(token_id=tid, score=72)
    r = repr(s)
    assert "SocialScore" in r
    assert str(tid) in r
    assert "72" in r


def test_contract_security_repr_contains_token_id_and_safety_score():
    tid = uuid4()
    c = ContractSecurity(token_id=tid, safety_score=95)
    r = repr(c)
    assert "ContractSecurity" in r
    assert str(tid) in r
    assert "95" in r


def test_job_run_repr_contains_job_id_status_and_time():
    now = datetime(2026, 7, 19, 12, 0, 0, tzinfo=UTC)
    j = JobRun(
        job_id="fetch_prices", correlation_id="corr-1", status=JobStatus.SUCCESS, started_at=now
    )
    r = repr(j)
    assert "JobRun" in r
    assert "fetch_prices" in r
    assert "success" in r.lower()


def test_narrative_classification_repr_contains_token_id_and_narrative():
    tid = uuid4()
    n = NarrativeClassification(
        token_id=tid,
        primary_narrative=Narrative.AI,
        confidence=Decimal("0.85"),
        reasoning="test",
    )
    r = repr(n)
    assert "NarrativeClassification" in r
    assert str(tid) in r
    assert "ai" in r.lower()


def test_token_snapshot_repr_contains_token_id_and_timestamp():
    tid = uuid4()
    now = datetime(2026, 7, 19, 12, 0, 0, tzinfo=UTC)
    s = TokenSnapshot(token_id=tid, captured_at=now)
    r = repr(s)
    assert "TokenSnapshot" in r
    assert str(tid) in r
