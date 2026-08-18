"""Memory management API (spec section 12): view/search/edit/delete/pin/clear."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.memory import database as memory_db

router = APIRouter()


class CreateMemoryRequest(BaseModel):
    entity_id: str
    content: str
    memory_type: str = "entity"
    category: str = "explicit_memory"
    importance: float = 0.7
    pinned: bool = False


class UpdateMemoryRequest(BaseModel):
    content: str | None = None
    category: str | None = None
    importance: float | None = None
    pinned: bool | None = None


def _memory_to_dict(m) -> dict:
    return {
        "id": m.id,
        "entity_id": m.entity_id,
        "memory_type": m.memory_type,
        "category": m.category,
        "content": m.content,
        "importance": m.importance,
        "confidence": m.confidence,
        "source": m.source,
        "pinned": m.pinned,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat(),
    }


@router.get("")
def list_memories(
    entity_id: str,
    category: str | None = None,
    pinned_only: bool = False,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    memories = memory_db.list_memories(db, entity_id, category=category, pinned_only=pinned_only, search=search)
    return [_memory_to_dict(m) for m in memories]


@router.post("")
def create_memory(req: CreateMemoryRequest, db: Session = Depends(get_db)) -> dict:
    try:
        memory = memory_db.create_memory(
            db,
            entity_id=req.entity_id,
            content=req.content,
            memory_type=req.memory_type,
            category=req.category,
            importance=req.importance,
            source="manual",
            pinned=req.pinned,
        )
        db.commit()
    except memory_db.MemoryError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return _memory_to_dict(memory)


@router.patch("/{memory_id}")
def update_memory(memory_id: int, req: UpdateMemoryRequest, db: Session = Depends(get_db)) -> dict:
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    try:
        memory = memory_db.update_memory(db, memory_id, **fields)
        db.commit()
    except memory_db.MemoryError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return _memory_to_dict(memory)


@router.post("/{memory_id}/pin")
def pin_memory(memory_id: int, pinned: bool = True, db: Session = Depends(get_db)) -> dict:
    try:
        memory = memory_db.pin_memory(db, memory_id, pinned=pinned)
        db.commit()
    except memory_db.MemoryError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return _memory_to_dict(memory)


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        memory_db.delete_memory(db, memory_id)
        db.commit()
    except memory_db.MemoryError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return {"deleted": memory_id}


@router.delete("")
def clear_entity_memory(entity_id: str, db: Session = Depends(get_db)) -> dict:
    count = memory_db.clear_entity_memory(db, entity_id)
    db.commit()
    return {"entity_id": entity_id, "deleted_count": count}
