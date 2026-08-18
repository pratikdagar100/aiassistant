"""Knowledge base API (spec section 14)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import KnowledgeDocument
from app.knowledge import ingest as ingest_module
from app.knowledge.extractor import SUPPORTED_EXTENSIONS
from app.knowledge.retrieval import retrieve_relevant_chunks

router = APIRouter()


class SearchRequest(BaseModel):
    entity_id: str
    query: str
    top_k: int = 5


def _doc_to_dict(doc: KnowledgeDocument) -> dict:
    return {
        "id": doc.id,
        "entity_id": doc.entity_id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "status": doc.status,
        "error_message": doc.error_message,
        "chunk_count": len(doc.chunks),
        "uploaded_at": doc.uploaded_at.isoformat(),
    }


@router.get("/supported-types")
def supported_types() -> list[str]:
    return sorted(SUPPORTED_EXTENSIONS)


@router.get("")
def list_documents(entity_id: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    q = db.query(KnowledgeDocument)
    if entity_id:
        q = q.filter_by(entity_id=entity_id)
    return [_doc_to_dict(d) for d in q.order_by(KnowledgeDocument.uploaded_at.desc()).all()]


@router.post("/upload")
async def upload_document(file: UploadFile, entity_id: str | None = None, db: Session = Depends(get_db)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file upload")

    doc = ingest_module.ingest_document(db, entity_id=entity_id, filename=file.filename or "document", data=data)
    db.commit()

    if doc.status == "error":
        raise HTTPException(422, doc.error_message or "Ingestion failed")
    return _doc_to_dict(doc)


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        ingest_module.delete_document(db, document_id)
        db.commit()
    except ingest_module.IngestError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return {"deleted": document_id}


@router.post("/search")
def search(req: SearchRequest, db: Session = Depends(get_db)) -> list[dict]:
    chunks = retrieve_relevant_chunks(db, req.entity_id, req.query, top_k=req.top_k)
    return [{"chunk_id": c.id, "document_id": c.document_id, "content": c.content} for c in chunks]
