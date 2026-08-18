"""CRUD for the Memory table, kept in sync with the vector store.

Every write here goes through this module rather than touching
app.db.models.Memory directly, so the SQL row and its embedding never drift
apart — see app.memory.retrieval, which depends on both existing together.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import Memory
from app.memory import vector_store
from app.memory.embeddings import embed_text, is_available

logger = get_logger("memory.database")

VALID_MEMORY_TYPES = {"short_term", "episodic", "semantic", "profile", "project", "global", "entity"}
VALID_CATEGORIES = {
    "temporary",
    "preference",
    "fact",
    "project",
    "personal_context",
    "explicit_memory",
    "task",
    "other",
}


class MemoryError(ValueError):
    pass


def create_memory(
    db: Session,
    *,
    entity_id: str | None,
    content: str,
    memory_type: str = "semantic",
    category: str = "other",
    importance: float = 0.5,
    confidence: float = 1.0,
    source: str | None = None,
    conversation_id: int | None = None,
    pinned: bool = False,
) -> Memory:
    if memory_type not in VALID_MEMORY_TYPES:
        raise MemoryError(f"Invalid memory_type '{memory_type}'")
    if category not in VALID_CATEGORIES:
        raise MemoryError(f"Invalid category '{category}'")

    memory = Memory(
        entity_id=entity_id,
        content=content,
        memory_type=memory_type,
        category=category,
        importance=importance,
        confidence=confidence,
        source=source,
        conversation_id=conversation_id,
        pinned=pinned,
    )
    db.add(memory)
    db.flush()  # need memory.id before embedding

    if is_available():
        try:
            embedding = embed_text(content)
            vector_store.upsert_memory(
                memory.id,
                entity_id,
                content,
                embedding,
                {"category": category, "memory_type": memory_type},
            )
            memory.vector_id = str(memory.id)
        except Exception:  # noqa: BLE001
            logger.warning("Embedding failed for memory %s — stored without vector index", memory.id, exc_info=True)
    else:
        logger.warning("Embedding model unavailable — memory %s stored without vector index", memory.id)

    return memory


def list_memories(
    db: Session,
    entity_id: str | None,
    *,
    category: str | None = None,
    pinned_only: bool = False,
    search: str | None = None,
) -> list[Memory]:
    q = db.query(Memory).filter(Memory.entity_id == entity_id)
    if category:
        q = q.filter(Memory.category == category)
    if pinned_only:
        q = q.filter(Memory.pinned.is_(True))
    if search:
        q = q.filter(Memory.content.ilike(f"%{search}%"))
    return q.order_by(Memory.created_at.desc()).all()


def update_memory(db: Session, memory_id: int, **fields) -> Memory:
    memory = db.get(Memory, memory_id)
    if not memory:
        raise MemoryError(f"Memory {memory_id} not found")

    allowed = {"content", "category", "importance", "confidence", "pinned"}
    for key, value in fields.items():
        if key not in allowed:
            raise MemoryError(f"Cannot set field '{key}'")
        setattr(memory, key, value)
    db.flush()

    if "content" in fields and is_available():
        try:
            embedding = embed_text(memory.content)
            vector_store.upsert_memory(
                memory.id,
                memory.entity_id,
                memory.content,
                embedding,
                {"category": memory.category, "memory_type": memory.memory_type},
            )
        except Exception:  # noqa: BLE001
            logger.warning("Re-embedding failed for memory %s", memory.id, exc_info=True)

    return memory


def delete_memory(db: Session, memory_id: int) -> None:
    memory = db.get(Memory, memory_id)
    if not memory:
        raise MemoryError(f"Memory {memory_id} not found")
    db.delete(memory)
    db.flush()
    try:
        vector_store.delete_memory(memory_id)
    except Exception:  # noqa: BLE001
        logger.warning("Vector store delete failed for memory %s", memory_id, exc_info=True)


def pin_memory(db: Session, memory_id: int, pinned: bool = True) -> Memory:
    return update_memory(db, memory_id, pinned=pinned)


def clear_entity_memory(db: Session, entity_id: str) -> int:
    """Deletes every memory for one entity. Global memories are untouched."""
    memories = db.query(Memory).filter(Memory.entity_id == entity_id).all()
    count = len(memories)
    for m in memories:
        db.delete(m)
        try:
            vector_store.delete_memory(m.id)
        except Exception:  # noqa: BLE001
            logger.warning("Vector store delete failed for memory %s", m.id, exc_info=True)
    db.flush()
    return count
