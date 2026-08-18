"""Autonomous task API (spec section 35): create, inspect, resume, replan, cancel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import orchestrator
from app.core.planner import PlanningError
from app.db.database import get_db
from app.db.models import Task

router = APIRouter()


class CreateTaskRequest(BaseModel):
    entity_id: str
    description: str
    conversation_id: int | None = None


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "entity_id": task.entity_id,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "steps": [
            {
                "id": s.id,
                "step_index": s.step_index,
                "description": s.description,
                "tool": s.tool,
                "parameters": s.parameters,
                "status": s.status,
                "result": s.result,
            }
            for s in sorted(task.steps, key=lambda s: s.step_index)
        ],
    }


@router.get("")
def list_tasks(entity_id: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    q = db.query(Task)
    if entity_id:
        q = q.filter_by(entity_id=entity_id)
    tasks = q.order_by(Task.created_at.desc()).all()
    return [_task_to_dict(t) for t in tasks]


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return _task_to_dict(task)


@router.post("")
async def create_task(req: CreateTaskRequest, db: Session = Depends(get_db)) -> dict:
    try:
        task = await orchestrator.create_and_run_task(
            db, entity_id=req.entity_id, description=req.description, conversation_id=req.conversation_id
        )
        db.commit()
    except orchestrator.AutonomyTooLow as exc:
        db.rollback()
        raise HTTPException(403, str(exc)) from exc
    except PlanningError as exc:
        db.rollback()
        raise HTTPException(502, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return _task_to_dict(task)


@router.post("/{task_id}/resume")
async def resume_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        task = await orchestrator.resume_task(db, task_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return _task_to_dict(task)


@router.post("/{task_id}/replan")
async def replan_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        task = await orchestrator.replan_task(db, task_id)
        db.commit()
    except PlanningError as exc:
        db.rollback()
        raise HTTPException(502, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return _task_to_dict(task)


@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        task = orchestrator.cancel_task(db, task_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return _task_to_dict(task)
