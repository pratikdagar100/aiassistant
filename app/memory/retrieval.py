"""Semantic memory retrieval — the piece that lets the LLM see relevant past
context without the entire conversation history being replayed every turn
(explicit spec requirement, section 11).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import Memory
from app.memory import vector_store
from app.memory.embeddings import embed_text, is_available

logger = get_logger("memory.retrieval")


def retrieve_relevant_memories(
    db: Session,
    entity_id: str,
    query_text: str,
    top_k: int | None = None,
    include_global: bool = True,
) -> list[Memory]:
    """Semantic search, always including pinned memories regardless of relevance score."""
    settings = get_settings()
    k = top_k or settings.memory.retrieval_top_k

    pinned = db.query(Memory).filter(Memory.entity_id == entity_id, Memory.pinned.is_(True)).all()

    if not is_available():
        logger.warning("Embedding model unavailable — falling back to pinned memories only")
        return pinned

    try:
        query_embedding = embed_text(query_text)
        hits = vector_store.query(query_embedding, entity_id, top_k=k, include_global=include_global)
    except Exception:  # noqa: BLE001
        logger.warning("Vector search failed — falling back to pinned memories only", exc_info=True)
        return pinned

    hit_ids = [h["memory_id"] for h in hits]
    if not hit_ids:
        return pinned

    rows = db.query(Memory).filter(Memory.id.in_(hit_ids)).all()
    by_id = {m.id: m for m in rows}
    ordered = [by_id[i] for i in hit_ids if i in by_id]

    # Merge, pinned first, de-duplicated, preserving relevance order for the rest.
    seen = {m.id for m in pinned}
    merged = list(pinned) + [m for m in ordered if m.id not in seen]
    return merged
