from fastapi.testclient import TestClient

from app.api.server import create_app
from app.db.database import session_scope
from app.entities import manager as entity_manager


def _client() -> TestClient:
    return TestClient(create_app())


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def test_create_and_list_memory_via_api():
    _make_entity("api-mem-a")
    client = _client()

    resp = client.post("/api/memory", json={"entity_id": "api-mem-a", "content": "Remember I like tea."})
    assert resp.status_code == 200
    mem_id = resp.json()["id"]

    resp = client.get("/api/memory", params={"entity_id": "api-mem-a"})
    assert resp.status_code == 200
    assert any(m["id"] == mem_id for m in resp.json())


def test_pin_update_delete_memory_via_api():
    _make_entity("api-mem-b")
    client = _client()

    resp = client.post("/api/memory", json={"entity_id": "api-mem-b", "content": "original"})
    mem_id = resp.json()["id"]

    resp = client.post(f"/api/memory/{mem_id}/pin", params={"pinned": True})
    assert resp.status_code == 200
    assert resp.json()["pinned"] is True

    resp = client.patch(f"/api/memory/{mem_id}", json={"content": "updated"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "updated"

    resp = client.delete(f"/api/memory/{mem_id}")
    assert resp.status_code == 200

    resp = client.get("/api/memory", params={"entity_id": "api-mem-b"})
    assert not any(m["id"] == mem_id for m in resp.json())


def test_clear_entity_memory_via_api():
    _make_entity("api-mem-c")
    client = _client()
    client.post("/api/memory", json={"entity_id": "api-mem-c", "content": "one"})
    client.post("/api/memory", json={"entity_id": "api-mem-c", "content": "two"})

    resp = client.delete("/api/memory", params={"entity_id": "api-mem-c"})
    assert resp.status_code == 200
    assert resp.json()["deleted_count"] == 2
