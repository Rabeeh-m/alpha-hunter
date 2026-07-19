from __future__ import annotations

from pydantic import BaseModel, ValidationError

from app.models.narrative_classification import Narrative

_NARRATIVE_LIST = ", ".join(n.value for n in Narrative)

SYSTEM_PROMPT = f"""You classify cryptocurrency tokens into ONE primary narrative
category based ONLY on the token's name, symbol, and DEX. You have no
other information -- no whitepaper, no website, no team info.

Valid categories: {_NARRATIVE_LIST}

Respond with ONLY a JSON object, no markdown fences, no other text:
{{"primary_narrative": "<category>", "confidence": <0-100>, "reasoning": "<under 15 words>"}}

Use "other" when the name/symbol gives no clear signal, or when it could
plausibly be several categories at once. Do not guess confidently from
a name alone -- most tokens with vague names should get LOW confidence
(under 40), not a forced high-confidence guess. Meme-styled names
(animal names, jokes, "inu", "moon", "pepe"-style) should generally be
classified as "meme" regardless of any buzzword also present in the
name -- a deceptive name using an unrelated buzzword is common and
should not be taken at face value."""


class NarrativeClassificationResult(BaseModel):
    primary_narrative: Narrative
    confidence: int
    reasoning: str


def build_user_prompt(symbol: str, name: str, dex: str | None) -> str:
    return f"Token symbol: {symbol}\nToken name: {name}\nDEX: {dex or 'unknown'}"


def parse_classification_response(raw_text: str) -> NarrativeClassificationResult:
    """Raises ValueError on any parse failure -- the caller (service
    layer) decides what to do with that, rather than this function
    silently returning a fabricated default. Unlike the Telegram
    parser (M16), which degrades gracefully because partial/absent data
    is expected and normal, a malformed LLM response here is genuinely
    unexpected and worth surfacing as an error, not masking."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return NarrativeClassificationResult.model_validate_json(cleaned.strip())
    except ValidationError as exc:
        raise ValueError(f"Could not parse LLM classification response: {exc}") from exc
