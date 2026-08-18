"""Ties planner + executor together into the plan -> execute -> observe ->
verify -> replan loop (spec section 24-26), and keeps Task/TaskStep in the
database in sync so the frontend Tasks page can show live progress.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.executor import StepFailed, StepPendingApproval, execute_step, resume_step
from app.core.logging import get_logger
from app.core.planner import generate_plan
from app.db.models import Entity, Task, TaskStep
from app.entities.loader import load_entity_profile

logger = get_logger("core.orchestrator")

MIN_AUTONOMY_FOR_TASKS = 6  # spec section 27: "6 = autonomous task execution"


class AutonomyTooLow(Exception):
    pass


async def create_and_run_task(db: Session, *, entity_id: str, description: str, conversation_id: int | None = None) -> Task:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise ValueError(f"Entity '{entity_id}' not found")
    if entity.autonomy_level < MIN_AUTONOMY_FOR_TASKS:
        raise AutonomyTooLow(
            f"Entity '{entity_id}' has autonomy_level={entity.autonomy_level}; "
            f"autonomous tasks require >= {MIN_AUTONOMY_FOR_TASKS}."
        )

    task = Task(entity_id=entity_id, conversation_id=conversation_id, description=description, status="planning")
    db.add(task)
    db.flush()

    profile = load_entity_profile(db, entity_id)
    steps_data = await generate_plan(profile, description)

    for i, step in enumerate(steps_data):
        db.add(
            TaskStep(
                task_id=task.id,
                step_index=i,
                description=step["description"],
                tool=step["tool"],
                parameters=step["parameters"],
                status="pending",
            )
        )
    task.status = "running"
    db.flush()

    return await run_task(db, task.id)


async def run_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    pending = sorted((s for s in task.steps if s.status == "pending"), key=lambda s: s.step_index)
    for step in pending:
        try:
            await execute_step(db, entity_id=task.entity_id, step=step)
        except StepPendingApproval:
            task.status = "paused"
            db.flush()
            return task
        except StepFailed:
            task.status = "failed"
            db.flush()
            return task

    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    db.flush()
    return task


async def resume_task(db: Session, task_id: int) -> Task:
    """Call after approving/denying the audit entry a paused step is waiting on."""
    task = db.get(Task, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    waiting = [s for s in task.steps if s.status == "pending_approval"]
    for step in waiting:
        audit_id = json.loads(step.result)["pending_audit_id"]
        try:
            await resume_step(db, step=step, audit_id=audit_id)
        except StepPendingApproval:
            return task  # approval still not resolved
        except StepFailed:
            task.status = "failed"
            db.flush()
            return task

    task.status = "running"
    db.flush()
    return await run_task(db, task_id)


async def replan_task(db: Session, task_id: int) -> Task:
    """Generates new steps to append after a failure and resumes execution —
    the one genuine 'replan' path in this phase; there is no automatic retry
    loop, so a failure always surfaces to the user first (spec: never hide
    failures behind silent retries)."""
    task = db.get(Task, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    if task.status != "failed":
        raise ValueError(f"Task {task_id} is '{task.status}', not 'failed' — nothing to replan")

    failed_step = next((s for s in sorted(task.steps, key=lambda s: s.step_index) if s.status == "failed"), None)
    context = None
    if failed_step:
        context = (
            f"A previous attempt failed at step '{failed_step.description}' "
            f"(tool: {failed_step.tool}): {failed_step.result}. Propose an alternative approach."
        )

    profile = load_entity_profile(db, task.entity_id)
    new_steps = await generate_plan(profile, task.description, context=context)

    max_index = max((s.step_index for s in task.steps), default=-1)
    for i, step in enumerate(new_steps):
        db.add(
            TaskStep(
                task_id=task.id,
                step_index=max_index + 1 + i,
                description=step["description"],
                tool=step["tool"],
                parameters=step["parameters"],
                status="pending",
            )
        )
    task.status = "running"
    db.flush()
    return await run_task(db, task.id)


def cancel_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    task.status = "cancelled"
    db.flush()
    return task
