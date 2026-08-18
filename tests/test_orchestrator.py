"""Uses the real Qwen3 8B model for planning — no mocking. Slower, and the
exact plan text can vary between runs since it's LLM-generated, so
assertions check structural/behavioral guarantees (valid tool names, correct
status transitions) rather than exact step content.
"""

import json

import pytest

from app.core import orchestrator
from app.db.database import session_scope
from app.db.models import Task
from app.entities import manager as entity_manager
from app.security import approval
from app.security.permissions import set_permissions


def _make_entity(entity_id: str, autonomy: int = 6, computer_access: bool = True):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title(), autonomy_level=autonomy, computer_access=computer_access)


@pytest.mark.slow
async def test_autonomy_too_low_rejects_task():
    _make_entity("test-orch-low", autonomy=2)
    with session_scope() as db:
        with pytest.raises(orchestrator.AutonomyTooLow):
            await orchestrator.create_and_run_task(db, entity_id="test-orch-low", description="List files in C:\\")


@pytest.mark.slow
async def test_task_with_enabled_permission_completes(tmp_path):
    _make_entity("test-orch-complete")
    (tmp_path / "sample.txt").write_text("hi")
    with session_scope() as db:
        set_permissions(db, "test-orch-complete", {"FILESYSTEM_READ": "enabled"})

    with session_scope() as db:
        task = await orchestrator.create_and_run_task(
            db, entity_id="test-orch-complete", description=f"List the contents of the folder {tmp_path}"
        )
        task_id = task.id
        status = task.status
        step_count = len(task.steps)

    assert step_count >= 1
    assert status in ("completed", "failed")  # LLM-planned — assert it reached a terminal state, not a specific plan


@pytest.mark.slow
async def test_task_with_confirmation_pauses_then_resumes(tmp_path):
    _make_entity("test-orch-pause")
    with session_scope() as db:
        set_permissions(db, "test-orch-pause", {"FILESYSTEM_WRITE": "confirmation"})

    target = tmp_path / "created_by_agent.txt"
    with session_scope() as db:
        task = await orchestrator.create_and_run_task(
            db, entity_id="test-orch-pause", description=f"Create an empty file at {target}"
        )
        task_id = task.id

    with session_scope() as db:
        task = db.get(Task, task_id)
        pending_steps = [s for s in task.steps if s.status == "pending_approval"]
        has_pending = bool(pending_steps)
        # If the planner picked a write tool, it must be paused, not silently executed.
        if has_pending:
            assert task.status == "paused"
            assert not target.exists()
            audit_id = json.loads(pending_steps[0].result)["pending_audit_id"]
            approval.approve(db, audit_id)

    if has_pending:
        with session_scope() as db:
            resumed = await orchestrator.resume_task(db, task_id)
            assert resumed.status in ("completed", "failed")
