import pytest

from app.db.database import session_scope
from app.entities import manager as entity_manager
from app.security import approval
from app.security.permissions import DEFAULT_PERMISSIONS, PermissionMode, get_mode, get_permissions, set_permissions


def _make_entity(entity_id: str, computer_access: bool = True):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title(), computer_access=computer_access)


def test_default_permissions_are_safe_by_default():
    assert DEFAULT_PERMISSIONS["ADMINISTRATOR"] == PermissionMode.DISABLED
    assert DEFAULT_PERMISSIONS["FILESYSTEM_DELETE"] == PermissionMode.CONFIRMATION


def test_computer_access_off_forces_disabled():
    _make_entity("test-sec-a", computer_access=False)
    with session_scope() as db:
        # even though the category default is ENABLED, computer_access=False overrides everything
        mode = get_mode(db, "test-sec-a", "FILESYSTEM_READ")
    assert mode == PermissionMode.DISABLED


def test_set_permissions_persists_and_merges():
    _make_entity("test-sec-b")
    with session_scope() as db:
        set_permissions(db, "test-sec-b", {"TERMINAL": PermissionMode.ENABLED})

    with session_scope() as db:
        perms = get_permissions(db, "test-sec-b")
    assert perms["TERMINAL"] == PermissionMode.ENABLED
    assert perms["ADMINISTRATOR"] == PermissionMode.DISABLED  # untouched categories keep defaults


def test_set_permissions_rejects_unknown_category():
    _make_entity("test-sec-c")
    with pytest.raises(ValueError):
        with session_scope() as db:
            set_permissions(db, "test-sec-c", {"NOT_A_CATEGORY": "enabled"})


def test_disabled_category_raises_permission_denied():
    _make_entity("test-sec-d")
    with session_scope() as db:
        set_permissions(db, "test-sec-d", {"FILESYSTEM_READ": PermissionMode.DISABLED})

    with pytest.raises(approval.PermissionDenied):
        with session_scope() as db:
            approval.request_execution(
                db, entity_id="test-sec-d", tool="filesystem.list_directory", parameters={"path": "."}
            )


def test_enabled_category_executes_immediately():
    _make_entity("test-sec-e")
    with session_scope() as db:
        set_permissions(db, "test-sec-e", {"FILESYSTEM_READ": PermissionMode.ENABLED})

    with session_scope() as db:
        entry = approval.request_execution(
            db, entity_id="test-sec-e", tool="filesystem.list_directory", parameters={"path": "."}
        )
        assert entry.approval_required is False
        assert entry.approved is True


def test_confirmation_category_requires_explicit_approval():
    _make_entity("test-sec-f")
    with session_scope() as db:
        set_permissions(db, "test-sec-f", {"FILESYSTEM_DELETE": PermissionMode.CONFIRMATION})

    with session_scope() as db:
        entry = approval.request_execution(
            db, entity_id="test-sec-f", tool="filesystem.delete", parameters={"path": "x"}
        )
        assert entry.approval_required is True
        assert entry.approved is None
        audit_id = entry.id

    with session_scope() as db:
        approved = approval.approve(db, audit_id)
        assert approved.approved is True

    # Approving twice should fail — it's no longer pending.
    with pytest.raises(ValueError):
        with session_scope() as db:
            approval.approve(db, audit_id)


def test_deny_marks_failure_without_executing():
    _make_entity("test-sec-g")
    with session_scope() as db:
        set_permissions(db, "test-sec-g", {"TERMINAL": PermissionMode.CONFIRMATION})

    with session_scope() as db:
        entry = approval.request_execution(
            db, entity_id="test-sec-g", tool="terminal.run_cmd", parameters={"command": "echo hi"}
        )
        audit_id = entry.id

    with session_scope() as db:
        denied = approval.deny(db, audit_id)
        assert denied.approved is False
        assert denied.success is False
