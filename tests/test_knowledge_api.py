from fastapi.testclient import TestClient

from app.api.server import create_app
from app.db.database import session_scope
from app.entities import manager as entity_manager


def _client() -> TestClient:
    return TestClient(create_app())


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def test_upload_list_search_delete_document():
    _make_entity("api-kb-a")
    client = _client()

    resp = client.post(
        "/api/knowledge/upload",
        params={"entity_id": "api-kb-a"},
        files={"file": ("notes.txt", b"The project deadline is March 3rd.", "text/plain")},
    )
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["status"] == "indexed"

    resp = client.get("/api/knowledge", params={"entity_id": "api-kb-a"})
    assert resp.status_code == 200
    assert any(d["id"] == doc["id"] for d in resp.json())

    resp = client.post("/api/knowledge/search", json={"entity_id": "api-kb-a", "query": "When is the deadline?"})
    assert resp.status_code == 200
    assert any("March" in r["content"] for r in resp.json())

    resp = client.delete(f"/api/knowledge/{doc['id']}")
    assert resp.status_code == 200


def test_upload_unsupported_type_returns_422():
    _make_entity("api-kb-b")
    client = _client()
    resp = client.post(
        "/api/knowledge/upload",
        params={"entity_id": "api-kb-b"},
        files={"file": ("bad.exe", b"binary", "application/octet-stream")},
    )
    assert resp.status_code == 422


def test_supported_types_endpoint():
    client = _client()
    resp = client.get("/api/knowledge/supported-types")
    assert resp.status_code == 200
    assert ".pdf" in resp.json()
