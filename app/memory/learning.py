"""Continuous learning (spec section 13): detect corrections/preferences in
a conversation turn and stage them as review-queue candidates. Nothing here
ever trains anything automatically — a human approves each example before
it can become part of a dataset (app/api/routes/learning.py).
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import TrainingExample
from app.llm.ollama import OllamaClient, OllamaError

logger = get_logger("memory.learning")

VALID_CATEGORIES = {"correction", "preference", "style", "factual_fix", "other"}

_SYSTEM_PROMPT = """You detect whether the user's latest message is CORRECTING or
expressing a durable PREFERENCE about the assistant's immediately preceding reply —
not just continuing the conversation or asking a new question.

Examples that ARE worth capturing:
- "No, I meant the other file" (correction)
- "Don't use bullet points, I prefer plain paragraphs" (style preference)
- "That's wrong, Python was released in 1991 not 1989" (factual_fix)

Examples that are NOT:
- A new unrelated question
- Ordinary follow-up ("okay, now do X")
- Small talk

Respond with strict JSON only:
{"is_correction": boolean, "category": one of ["correction","preference","style","factual_fix","other"], "ideal_response": "what the assistant should have said instead, written as a complete reply"}

If is_correction is false, ideal_response can be empty."""


async def detect_and_queue(
    db: Session,
    *,
    entity_id: str,
    model: str,
    conversation_id: int | None,
    prior_assistant_reply: str,
    user_message: str,
) -> TrainingExample | None:
    client = OllamaClient()
    if not await client.is_available():
        return None

    try:
        result = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Assistant said: {prior_assistant_reply}\n\nUser replied: {user_message}"},
            ],
            format="json",
        )
    except OllamaError:
        logger.warning("Learning-signal classification call failed", exc_info=True)
        return None

    raw = result.get("message", {}).get("content", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Learning classifier returned non-JSON: %r", raw[:200])
        return None

    if not parsed.get("is_correction"):
        return None

    ideal = (parsed.get("ideal_response") or "").strip()
    if not ideal:
        return None

    category = parsed.get("category", "other")
    if category not in VALID_CATEGORIES:
        category = "other"

    example = TrainingExample(
        entity_id=entity_id,
        conversation_id=conversation_id,
        input_text=user_message,
        output_text=ideal,
        category=category,
        status="pending",
    )
    db.add(example)
    db.flush()
    logger.info("Queued training example candidate for entity '%s' (%s)", entity_id, category)
    return example
