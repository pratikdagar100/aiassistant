"""Ties extraction -> chunking -> embedding -> vector store -> DB together
(spec section 14 pipeline). Reuses the same embedding model as conversational
memory (app/memory/embeddings.py) — one model loaded, not two.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.logging import get_logger
from app.db.models import KnowledgeChunk, KnowledgeDocument
from app.entities.manager import entity_dir
from app.knowledge import vector_store
from app.knowledge.chunker import chunk_text
from app.knowledge.extractor import ExtractionError, extract_text
from app.memory.embeddings import embed_texts, is_available as embeddings_available

logger = get_logger("knowledge.ingest")

GLOBAL_KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge_global"


class IngestError(RuntimeError):
    pass


def _storage_dir(entity_id: str | None) -> Path:
    if entity_id:
        return entity_dir(entity_id) / "knowledge"
    GLOBAL_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    return GLOBAL_KNOWLEDGE_DIR


def ingest_document(db: Session, *, entity_id: str | None, filename: str, data: bytes) -> KnowledgeDocument:
    storage_dir = _storage_dir(entity_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / filename
    file_path.write_bytes(data)

    doc = KnowledgeDocument(
        entity_id=entity_id,
        filename=filename,
        file_type=file_path.suffix.lower().lstrip("."),
        file_path=str(file_path),
        status="processing",
    )
    db.add(doc)
    db.flush()

    try:
        text = extract_text(file_path)
        chunks = chunk_text(text)
        if not chunks:
            raise IngestError("No extractable text found in document")

        if not embeddings_available():
            raise IngestError("Embedding model unavailable — cannot index this document")

        vectors = embed_texts(chunks)

        for i, (chunk_content, vector) in enumerate(zip(chunks, vectors)):
            chunk_row = KnowledgeChunk(document_id=doc.id, chunk_index=i, content=chunk_content)
            db.add(chunk_row)
            db.flush()
            vector_store.upsert_chunk(chunk_row.id, entity_id, doc.id, chunk_content, vector)
            chunk_row.vector_id = str(chunk_row.id)

        doc.status = "indexed"
        db.flush()
        logger.info("Indexed document '%s' (%d chunks)", filename, len(chunks))
    except (ExtractionError, IngestError) as exc:
        doc.status = "error"
        doc.error_message = str(exc)
        db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error indexing '%s'", filename, exc_info=True)
        doc.status = "error"
        doc.error_message = str(exc)
        db.flush()

    return doc


def delete_document(db: Session, document_id: int) -> None:
    doc = db.get(KnowledgeDocument, document_id)
    if not doc:
        raise IngestError(f"Document {document_id} not found")

    chunk_ids = [c.id for c in doc.chunks]
    vector_store.delete_document_chunks(chunk_ids)

    path = Path(doc.file_path)
    if path.exists():
        path.unlink()

    db.delete(doc)
    db.flush()
