"""Idempotent seed data. Currently: the default entity, Friday (spec section 53).

Called from the API lifespan on every startup — safe to run repeatedly,
never overwrites a user's edits to an existing row.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import session_scope
from app.db.models import Entity

logger = get_logger("db.seed")

FRIDAY_SYSTEM_PROMPT = (
    "You are Friday, a personal AI assistant. You are helpful, honest, "
    "technically capable, context-aware, and concise. You can use the "
    "computer tools provided by the system. Never claim an action succeeded "
    "until you have verified it."
)


def seed_default_entity() -> None:
    settings = get_settings()
    entity_id = settings.default_entity

    with session_scope() as db:
        existing = db.get(Entity, entity_id)
        if existing:
            return

        db.add(
            Entity(
                id=entity_id,
                name="Friday",
                description="Default personal AI assistant.",
                personality="Intelligent, calm, helpful, concise, technically capable and slightly humorous.",
                system_prompt=FRIDAY_SYSTEM_PROMPT,
                model=settings.llm.default_model,
                language_mode="auto",
                memory_enabled=True,
                computer_access=True,  # safe: FILESYSTEM_WRITE/DELETE/TERMINAL/etc. still default to confirmation
                autonomy_level=7,  # matches spec's example Friday config; permissions remain the real gate
            )
        )
    logger.info("Seeded default entity: %s", entity_id)
