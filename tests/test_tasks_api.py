import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app
from app.db.database import session_scope
from app.entities import manager as entity_manager


def _client() -> TestClient:
    return TestClient(create_app())


def _make_entity(entity_id: str, autonomy: int = 6):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title(), autonomy_level=autonomy, computer_access=True)


def test_create_task_autonomy_too_low_403():
    _make_entity("api-task-low", autonomy=1)
    client = _client()
    resp = client.post("/api/tasks", json={"entity_id": "api-task-low", "description": "do something"})
    assert resp.status_code == 403


def test_create_task_unknown_entity_404():
    client = _client()
    resp = client.post("/api/tasks", json={"entity_id": "does-not-exist", "description": "do something"})
    assert resp.status_code == 404


@pytest.mark.slow
def test_create_and_list_task(tmp_path):
    _make_entity("api-task-ok")
    client = _client()
    client.put("/api/permissions/api-task-ok", json={"permissions": {"FILESYSTEM_READ": "enabled"}})

    resp = client.post("/api/tasks", json={"entity_id": "api-task-ok", "description": f"List files in {tmp_path}"})
    assert resp.status_code == 200
    task = resp.json()
    assert task["status"] in ("completed", "failed")
    assert len(task["steps"]) >= 1

    resp = client.get("/api/tasks", params={"entity_id": "api-task-ok"})
    assert resp.status_code == 200
    assert any(t["id"] == task["id"] for t in resp.json())


def test_cancel_task(tmp_path):
    _make_entity("api-task-cancel")
    client = _client()
    # low read-only permission so it completes fast without needing approval
    client.put("/api/permissions/api-task-cancel", json={"permissions": {"FILESYSTEM_READ": "enabled"}})
    resp = client.post("/api/tasks", json={"entity_id": "api-task-cancel", "description": f"List files in {tmp_path}"})
    task_id = resp.json()["id"]

    resp = client.post(f"/api/tasks/{task_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
