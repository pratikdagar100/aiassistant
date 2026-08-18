"""Audit logging (spec section 30) — every significant tool execution is
recorded here, whether it ran immediately or needed approval first.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def log_action(
    db: Session,
    *,
    entity_id: str | None,
    tool: str,
    parameters: dict,
    user_request: str | None = None,
    risk_level: str = "low",
    approval_required: bool = False,
    approved: bool | None = None,
    result: str | None = None,
    success: bool | None = None,
) -> AuditLog:
    entry = AuditLog(
        entity_id=entity_id,
        user_request=user_request,
        tool=tool,
        parameters=parameters,
        risk_level=risk_level,
        approval_required=approval_required,
        approved=approved,
        result=result,
        success=success,
    )
    db.add(entry)
    db.flush()
    return entry


def list_audit_logs(
    db: Session,
    *,
    entity_id: str | None = None,
    pending_only: bool = False,
    limit: int = 200,
) -> list[AuditLog]:
    q = db.query(AuditLog)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if pending_only:
        q = q.filter(AuditLog.approval_required.is_(True), AuditLog.approved.is_(None))
    return q.order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_audit_log(db: Session, audit_id: int) -> AuditLog | None:
    return db.get(AuditLog, audit_id)
