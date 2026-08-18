"""Semantic retrieval over indexed knowledge-base chunks."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import KnowledgeChunk
from app.knowledge import vector_store
from app.memory.embeddings import embed_text, is_available

logger = get_logger("knowledge.retrieval")


def retrieve_relevant_chunks(db: Session, entity_id: str, query_text: str, top_k: int | None = None) -> list[KnowledgeChunk]:
    if not is_available():
        return []

    settings = get_settings()
    k = top_k or settings.memory.retrieval_top_k

    try:
        query_embedding = embed_text(query_text)
        hits = vector_store.query(query_embedding, entity_id, top_k=k)
    except Exception:  # noqa: BLE001
        logger.warning("Knowledge vector search failed", exc_info=True)
        return []

    hit_ids = [h["chunk_id"] for h in hits]
    if not hit_ids:
        return []

    rows = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(hit_ids)).all()
    by_id = {c.id: c for c in rows}
    return [by_id[i] for i in hit_ids if i in by_id]
