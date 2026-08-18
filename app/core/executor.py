"""Executes one TaskStep through the same approval gateway/tool registry
computer control uses (app/api/routes/computer.py) — a task never gets a
side channel around permissions just because it's agent-initiated rather
than a direct user click.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from sqlalchemy.orm import Session

from app.computer.registry import get_tool
from app.core.logging import get_logger
from app.db.models import TaskStep
from app.security import approval

logger = get_logger("core.executor")


class StepPendingApproval(Exception):
    def __init__(self, audit_id: int):
        self.audit_id = audit_id


class StepFailed(Exception):
    pass


def _verify(tool: str, parameters: dict) -> str | None:
    """Best-effort observation beyond 'the call didn't raise' — spec section 25
    (don't assume success). Filesystem ops are checked here because they have an
    unambiguous, cheap way to confirm state; other tools rely on the absence of
    an exception as their first-order success signal for now."""
    try:
        if tool in ("filesystem.create_file", "filesystem.write_file", "filesystem.copy", "filesystem.move"):
            path = parameters.get("path") or parameters.get("dst")
            if path and not Path(path).exists():
                return f"Verification failed: expected '{path}' to exist after {tool}, but it does not."
        elif tool == "filesystem.delete":
            path = parameters.get("path")
            if path and Path(path).exists():
                return f"Verification failed: expected '{path}' to be gone after delete, but it still exists."
    except OSError:
        pass
    return None


async def execute_step(db: Session, *, entity_id: str, step: TaskStep) -> None:
    """Mutates `step` in place: status becomes running -> success/failed/pending_approval."""
    step.status = "running"
    db.flush()

    try:
        entry = approval.request_execution(
            db,
            entity_id=entity_id,
            tool=step.tool,
            parameters=step.parameters or {},
            user_request=step.description,
        )
    except approval.PermissionDenied as exc:
        step.status = "failed"
        step.result = f"Permission denied: {exc}"
        db.flush()
        raise StepFailed(str(exc)) from exc

    if entry.approval_required:
        step.status = "pending_approval"
        step.result = f'{{"pending_audit_id": {entry.id}}}'
        db.flush()
        raise StepPendingApproval(entry.id)

    await _run_and_record(db, step, entry.id)


async def resume_step(db: Session, *, step: TaskStep, audit_id: int) -> None:
    """Called once a previously-pending step's approval has been resolved."""
    from app.security.audit import get_audit_log

    entry = get_audit_log(db, audit_id)
    if not entry or entry.approved is None:
        raise StepPendingApproval(audit_id)  # still waiting

    if entry.approved is False:
        step.status = "failed"
        step.result = "Denied by user"
        db.flush()
        raise StepFailed("Denied by user")

    step.status = "running"
    db.flush()
    await _run_and_record(db, step, audit_id)


async def _run_and_record(db: Session, step: TaskStep, audit_id: int) -> None:
    from datetime import datetime, timezone

    from app.security.approval import record_result

    try:
        fn = get_tool(step.tool)
        result = fn(**(step.parameters or {}))
        if inspect.isawaitable(result):
            result = await result
        result_str = str(result)

        verification_issue = _verify(step.tool, step.parameters or {})
        if verification_issue:
            step.status = "failed"
            step.result = verification_issue
            record_result(db, audit_id, result=verification_issue, success=False)
            db.flush()
            raise StepFailed(verification_issue)

        step.status = "success"
        step.result = result_str
        step.observed_at = datetime.now(timezone.utc)
        record_result(db, audit_id, result=result_str, success=True)
        db.flush()
    except StepFailed:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Step execution failed: %s", step.tool, exc_info=True)
        step.status = "failed"
        step.result = str(exc)
        record_result(db, audit_id, result=str(exc), success=False)
        db.flush()
        raise StepFailed(str(exc)) from exc
