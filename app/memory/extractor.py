"""Decides whether a user message contains something worth remembering
long-term, and if so, stores it (spec section 12).

"Open Chrome." -> not memory-worthy.
"I prefer VS Code over PyCharm." -> PREFERENCE.
"Remember that my main AI project is called PratikAI." -> EXPLICIT_MEMORY.

Uses the entity's own LLM with Ollama's constrained JSON output rather than
a separate classifier model — good enough accuracy for Phase 4, and keeps
VRAM usage to the one model already loaded.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.llm.ollama import OllamaClient, OllamaError
from app.memory import database as memory_db

logger = get_logger("memory.extractor")

_CLASSIFIER_SYSTEM_PROMPT = """You extract long-term memories from a single user chat message.

Decide whether this message contains information worth remembering across future
conversations (a fact, stated preference, project detail, personal context, an explicit
"remember this" instruction, or a task to track). Simple commands, greetings, and
one-off questions with no lasting information are NOT memory-worthy.

Respond with strict JSON only, matching this shape:
{"should_remember": boolean, "category": one of ["preference","fact","project","personal_context","explicit_memory","task","other"], "content": "a short third-person statement of the fact, e.g. 'User prefers VS Code over PyCharm.'", "importance": a number from 0.0 to 1.0}

If should_remember is false, category/content/importance can be empty/zero."""


async def classify_and_store(
    db: Session,
    *,
    entity_id: str,
    model: str,
    user_message: str,
    conversation_id: int | None,
) -> memory_db.Memory | None:
    client = OllamaClient()
    if not await client.is_available():
        logger.debug("Ollama unavailable — skipping memory extraction")
        return None

    try:
        result = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": _CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            format="json",
        )
    except OllamaError:
        logger.warning("Memory classification call failed", exc_info=True)
        return None

    raw = result.get("message", {}).get("content", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Memory classifier returned non-JSON: %r", raw[:200])
        return None

    if not parsed.get("should_remember"):
        return None

    content = (parsed.get("content") or "").strip()
    if not content:
        return None

    category = parsed.get("category", "other")
    if category not in memory_db.VALID_CATEGORIES:
        category = "other"

    importance = parsed.get("importance", 0.5)
    try:
        importance = max(0.0, min(1.0, float(importance)))
    except (TypeError, ValueError):
        importance = 0.5

    memory = memory_db.create_memory(
        db,
        entity_id=entity_id,
        content=content,
        memory_type="episodic",
        category=category,
        importance=importance,
        source="conversation_extraction",
        conversation_id=conversation_id,
    )
    logger.info("Extracted memory for entity '%s': %s", entity_id, content)
    return memory
