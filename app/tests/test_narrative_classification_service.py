from __future__ import annotations

from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.anthropic_client import AnthropicClassifierClient
from app.models.chain import Chain
from app.models.narrative_classification import Narrative
from app.models.token import Token
from app.narratives.classifier_prompt import NarrativeClassificationResult
from app.repositories.narrative_repository import NarrativeRepository
from app.repositories.token_repository import TokenRepository
from app.services.narrative_classification_service import NarrativeClassificationService


async def test_classify_token_persists_result(db_session: AsyncSession):
    token_repo = TokenRepository(db_session)
    token = await token_repo.add(
        Token(chain=Chain.BASE, contract_address="0xnarr", name="Doge Moon", symbol="DMOON")
    )

    client = AsyncMock(spec=AnthropicClassifierClient)
    client.classify.return_value = NarrativeClassificationResult(
        primary_narrative=Narrative.MEME, confidence=90, reasoning="Dog + moon meme naming pattern"
    )

    repo = NarrativeRepository(db_session)
    service = NarrativeClassificationService(client, repo)
    await service.classify_token(token)

    record = await repo.get_by_token_id(token.id)
    assert record is not None
    assert record.primary_narrative == Narrative.MEME


async def test_classify_unclassified_batch_continues_after_one_failure(db_session: AsyncSession):
    token_repo = TokenRepository(db_session)
    await token_repo.add(
        Token(chain=Chain.BASE, contract_address="0xgood", name="Good Token", symbol="GOOD")
    )
    await token_repo.add(
        Token(chain=Chain.BASE, contract_address="0xbad", name="Bad Token", symbol="BAD")
    )

    client = AsyncMock(spec=AnthropicClassifierClient)
    client.classify.side_effect = [
        ValueError("simulated parse failure"),
        NarrativeClassificationResult(
            primary_narrative=Narrative.OTHER, confidence=20, reasoning="No clear signal"
        ),
    ]

    repo = NarrativeRepository(db_session)
    service = NarrativeClassificationService(client, repo)
    result = await service.classify_unclassified_batch(limit=10)

    assert result == {"classified": 1, "failed": 1}
