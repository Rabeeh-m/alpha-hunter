from __future__ import annotations

import pytest

from app.narratives.classifier_prompt import parse_classification_response


def test_parses_clean_json():
    raw = '{"primary_narrative": "meme", "confidence": 85, "reasoning": "Dog-themed name"}'
    result = parse_classification_response(raw)
    assert result.primary_narrative.value == "meme"
    assert result.confidence == 85


def test_strips_markdown_fences():
    raw = '```json\n{"primary_narrative": "ai", "confidence": 60, "reasoning": "AI in name"}\n```'
    result = parse_classification_response(raw)
    assert result.primary_narrative.value == "ai"


def test_raises_on_malformed_json():
    with pytest.raises(ValueError):
        parse_classification_response("not json at all")


def test_raises_on_invalid_narrative_value():
    raw = '{"primary_narrative": "not_a_real_category", "confidence": 50, "reasoning": "x"}'
    with pytest.raises(ValueError):
        parse_classification_response(raw)
