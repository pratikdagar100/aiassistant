from fastapi.testclient import TestClient

from app.api.server import create_app
from app.db.database import session_scope
from app.entities import manager as entity_manager


def _client() -> TestClient:
    return TestClient(create_app())


def _make_entity(entity_id: str, computer_access: bool = True):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title(), computer_access=computer_access)


def test_list_tools():
    client = _client()
    resp = client.get("/api/computer/tools")
    assert resp.status_code == 200
    tools = [t["tool"] for t in resp.json()]
    assert "filesystem.read_file" in tools
    assert "terminal.run_powershell" in tools


def test_execute_unknown_tool_404():
    _make_entity("api-comp-unknown")
    client = _client()
    resp = client.post("/api/computer/execute", json={"entity_id": "api-comp-unknown", "tool": "not.a.tool", "parameters": {}})
    assert resp.status_code == 404


def test_execute_disabled_category_403():
    _make_entity("api-comp-disabled", computer_access=False)
    client = _client()
    resp = client.post(
        "/api/computer/execute",
        json={"entity_id": "api-comp-disabled", "tool": "filesystem.list_directory", "parameters": {"path": "."}},
    )
    assert resp.status_code == 403


def test_execute_enabled_tool_runs_immediately(tmp_path):
    _make_entity("api-comp-enabled")
    client = _client()
    client.put("/api/permissions/api-comp-enabled", json={"permissions": {"FILESYSTEM_READ": "enabled"}})

    resp = client.post(
        "/api/computer/execute",
        json={"entity_id": "api-comp-enabled", "tool": "filesystem.list_directory", "parameters": {"path": str(tmp_path)}},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_execute_confirmation_tool_pends_then_approves(tmp_path):
    _make_entity("api-comp-confirm")
    client = _client()
    client.put("/api/permissions/api-comp-confirm", json={"permissions": {"FILESYSTEM_WRITE": "confirmation"}})

    target = str(tmp_path / "note.txt")
    resp = client.post(
        "/api/computer/execute",
        json={
            "entity_id": "api-comp-confirm",
            "tool": "filesystem.write_file",
            "parameters": {"path": target, "content": "hello"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending_approval"
    audit_id = body["audit_id"]

    import os

    assert not os.path.exists(target)  # must NOT have executed yet

    resp = client.post(f"/api/computer/approve/{audit_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert os.path.exists(target)


def test_execute_confirmation_tool_deny_never_executes(tmp_path):
    _make_entity("api-comp-deny")
    client = _client()
    client.put("/api/permissions/api-comp-deny", json={"permissions": {"FILESYSTEM_WRITE": "confirmation"}})

    target = str(tmp_path / "denied.txt")
    resp = client.post(
        "/api/computer/execute",
        json={"entity_id": "api-comp-deny", "tool": "filesystem.write_file", "parameters": {"path": target, "content": "x"}},
    )
    audit_id = resp.json()["audit_id"]

    resp = client.post(f"/api/computer/deny/{audit_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "denied"

    import os

    assert not os.path.exists(target)


def test_permissions_get_and_set():
    _make_entity("api-perm-a")
    client = _client()
    resp = client.get("/api/permissions/api-perm-a")
    assert resp.status_code == 200
    assert resp.json()["ADMINISTRATOR"] == "disabled"

    resp = client.put("/api/permissions/api-perm-a", json={"permissions": {"TERMINAL": "enabled"}})
    assert resp.status_code == 200
    assert resp.json()["TERMINAL"] == "enabled"


def test_audit_log_records_execution(tmp_path):
    _make_entity("api-audit-a")
    client = _client()
    client.put("/api/permissions/api-audit-a", json={"permissions": {"FILESYSTEM_READ": "enabled"}})
    client.post(
        "/api/computer/execute",
        json={"entity_id": "api-audit-a", "tool": "filesystem.list_directory", "parameters": {"path": str(tmp_path)}},
    )

    resp = client.get("/api/audit", params={"entity_id": "api-audit-a"})
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 1
    assert entries[0]["tool"] == "filesystem.list_directory"
    assert entries[0]["success"] is True
