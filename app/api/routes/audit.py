"""Audit log API (spec section 30)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.security import audit as audit_log

router = APIRouter()


def _to_dict(entry) -> dict:
    return {
        "id": entry.id,
        "entity_id": entry.entity_id,
        "timestamp": entry.timestamp.isoformat(),
        "user_request": entry.user_request,
        "tool": entry.tool,
        "parameters": entry.parameters,
        "result": entry.result,
        "risk_level": entry.risk_level,
        "approval_required": entry.approval_required,
        "approved": entry.approved,
        "success": entry.success,
    }


@router.get("")
def list_audit(entity_id: str | None = None, pending_only: bool = False, limit: int = 200, db: Session = Depends(get_db)) -> list[dict]:
    entries = audit_log.list_audit_logs(db, entity_id=entity_id, pending_only=pending_only, limit=limit)
    return [_to_dict(e) for e in entries]


@router.get("/{audit_id}")
def get_audit(audit_id: int, db: Session = Depends(get_db)) -> dict:
    entry = audit_log.get_audit_log(db, audit_id)
    if not entry:
        raise HTTPException(404, f"Audit entry {audit_id} not found")
    return _to_dict(entry)
