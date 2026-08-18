"""Learning Dashboard API (spec section 13): review queue for training-example
candidates, plus the counts the dashboard shows."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Conversation, Memory, TrainingExample

router = APIRouter()


class UpdateExampleRequest(BaseModel):
    input_text: str | None = None
    output_text: str | None = None
    category: str | None = None


def _example_to_dict(e: TrainingExample) -> dict:
    return {
        "id": e.id,
        "entity_id": e.entity_id,
        "conversation_id": e.conversation_id,
        "input_text": e.input_text,
        "output_text": e.output_text,
        "category": e.category,
        "status": e.status,
        "created_at": e.created_at.isoformat(),
        "reviewed_at": e.reviewed_at.isoformat() if e.reviewed_at else None,
    }


@router.get("/dashboard")
def dashboard(entity_id: str | None = None, db: Session = Depends(get_db)) -> dict:
    convo_q = db.query(func.count(Conversation.id))
    mem_q = db.query(func.count(Memory.id))
    ex_q = db.query(TrainingExample)
    if entity_id:
        convo_q = convo_q.filter(Conversation.entity_id == entity_id)
        mem_q = mem_q.filter(Memory.entity_id == entity_id)
        ex_q = ex_q.filter(TrainingExample.entity_id == entity_id)

    examples = ex_q.all()
    pending = [e for e in examples if e.status == "pending"]
    approved = [e for e in examples if e.status == "approved"]
    rejected = [e for e in examples if e.status == "rejected"]

    return {
        "total_conversations": convo_q.scalar() or 0,
        "total_memories": mem_q.scalar() or 0,
        "potential_training_examples": len(pending),
        "approved_examples": len(approved),
        "rejected_examples": len(rejected),
        "dataset_size": len(approved),
        "last_training": None,  # Phase 12 fills this in once a training run has actually happened
        "model_adapter_status": "none",
    }


@router.get("/examples")
def list_examples(entity_id: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    q = db.query(TrainingExample)
    if entity_id:
        q = q.filter_by(entity_id=entity_id)
    if status:
        q = q.filter_by(status=status)
    return [_example_to_dict(e) for e in q.order_by(TrainingExample.created_at.desc()).all()]


def _get_or_404(db: Session, example_id: int) -> TrainingExample:
    example = db.get(TrainingExample, example_id)
    if not example:
        raise HTTPException(404, f"Training example {example_id} not found")
    return example


@router.post("/examples/{example_id}/approve")
def approve_example(example_id: int, db: Session = Depends(get_db)) -> dict:
    example = _get_or_404(db, example_id)
    example.status = "approved"
    example.reviewed_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return _example_to_dict(example)


@router.post("/examples/{example_id}/reject")
def reject_example(example_id: int, db: Session = Depends(get_db)) -> dict:
    example = _get_or_404(db, example_id)
    example.status = "rejected"
    example.reviewed_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return _example_to_dict(example)


@router.patch("/examples/{example_id}")
def edit_example(example_id: int, req: UpdateExampleRequest, db: Session = Depends(get_db)) -> dict:
    example = _get_or_404(db, example_id)
    if req.input_text is not None:
        example.input_text = req.input_text
    if req.output_text is not None:
        example.output_text = req.output_text
    if req.category is not None:
        example.category = req.category
    db.commit()
    return _example_to_dict(example)


@router.delete("/examples/{example_id}")
def delete_example(example_id: int, db: Session = Depends(get_db)) -> dict:
    example = _get_or_404(db, example_id)
    db.delete(example)
    db.commit()
    return {"deleted": example_id}
