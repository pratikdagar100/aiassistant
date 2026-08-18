"""The single gateway every computer-tool call must go through.

Combines command_policy (what kind of action is this) with permissions
(what does this entity allow) to decide one of three outcomes: reject
outright, execute immediately, or park as a pending approval the user must
explicitly approve/deny (spec section 29) before it runs.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import AuditLog
from app.security import audit as audit_log
from app.security import command_policy
from app.security.permissions import PermissionMode, get_mode

logger = get_logger("security.approval")


class PermissionDenied(Exception):
    pass


class ApprovalPending(Exception):
    """Raised by request_execution when the action was recorded but must
    wait for explicit user approval — audit_id is where to check/approve it."""

    def __init__(self, audit_id: int, reason: str):
        super().__init__(reason)
        self.audit_id = audit_id


def request_execution(
    db: Session,
    *,
    entity_id: str,
    tool: str,
    parameters: dict,
    user_request: str | None = None,
) -> AuditLog:
    """Returns an AuditLog you may now act on:
    - approval_required=False, approved=True  -> execute immediately, then call record_result()
    - approval_required=True,  approved=None  -> do NOT execute; wait for approve()/deny()
    Raises PermissionDenied if the category is disabled for this entity.
    """
    policy = command_policy.get_policy(tool)
    mode = get_mode(db, entity_id, policy.category)

    if mode == PermissionMode.DISABLED:
        audit_log.log_action(
            db,
            entity_id=entity_id,
            tool=tool,
            parameters=parameters,
            user_request=user_request,
            risk_level=policy.risk,
            approval_required=False,
            approved=False,
            success=False,
            result="Denied: permission category disabled for this entity",
        )
        raise PermissionDenied(f"'{policy.category}' is disabled for entity '{entity_id}'")

    approval_required = mode == PermissionMode.CONFIRMATION
    entry = audit_log.log_action(
        db,
        entity_id=entity_id,
        tool=tool,
        parameters=parameters,
        user_request=user_request,
        risk_level=policy.risk,
        approval_required=approval_required,
        approved=None if approval_required else True,
    )
    return entry


def record_result(db: Session, audit_id: int, *, result: str, success: bool) -> AuditLog:
    entry = audit_log.get_audit_log(db, audit_id)
    if not entry:
        raise ValueError(f"Audit entry {audit_id} not found")
    entry.result = result
    entry.success = success
    db.flush()
    return entry


def approve(db: Session, audit_id: int) -> AuditLog:
    entry = audit_log.get_audit_log(db, audit_id)
    if not entry:
        raise ValueError(f"Audit entry {audit_id} not found")
    if not entry.approval_required or entry.approved is not None:
        raise ValueError(f"Audit entry {audit_id} is not pending approval")
    entry.approved = True
    db.flush()
    return entry


def deny(db: Session, audit_id: int) -> AuditLog:
    entry = audit_log.get_audit_log(db, audit_id)
    if not entry:
        raise ValueError(f"Audit entry {audit_id} not found")
    if not entry.approval_required or entry.approved is not None:
        raise ValueError(f"Audit entry {audit_id} is not pending approval")
    entry.approved = False
    entry.success = False
    entry.result = "Denied by user"
    db.flush()
    return entry
