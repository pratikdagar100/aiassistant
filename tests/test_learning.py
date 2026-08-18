"""Uses the real Qwen3 8B model to classify correction signals — no mocking."""

import pytest

from app.db.database import session_scope
from app.entities import manager as entity_manager
from app.memory.learning import detect_and_queue


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


@pytest.mark.slow
async def test_correction_is_detected_and_queued():
    _make_entity("test-learn-a")
    with session_scope() as db:
        example = await detect_and_queue(
            db,
            entity_id="test-learn-a",
            model="qwen3:8b",
            conversation_id=None,
            prior_assistant_reply="Python was first released in 1989.",
            user_message="That's wrong, Python was released in 1991, not 1989.",
        )
        assert example is not None
        assert example.category in ("correction", "factual_fix")
        assert "1991" in example.output_text


@pytest.mark.slow
async def test_ordinary_followup_is_not_queued():
    _make_entity("test-learn-b")
    with session_scope() as db:
        example = await detect_and_queue(
            db,
            entity_id="test-learn-b",
            model="qwen3:8b",
            conversation_id=None,
            prior_assistant_reply="Sure, I can help you open Chrome.",
            user_message="Great, thanks! Now can you also open VS Code?",
        )
        assert example is None
