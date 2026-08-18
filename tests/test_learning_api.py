from fastapi.testclient import TestClient

from app.api.server import create_app
from app.db.database import session_scope
from app.db.models import TrainingExample
from app.entities import manager as entity_manager


def _client() -> TestClient:
    return TestClient(create_app())


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def _make_example(entity_id: str, status: str = "pending") -> int:
    with session_scope() as db:
        ex = TrainingExample(
            entity_id=entity_id, input_text="in", output_text="out", category="correction", status=status
        )
        db.add(ex)
        db.flush()
        return ex.id


def test_dashboard_counts():
    _make_entity("api-learn-a")
    _make_example("api-learn-a", "pending")
    _make_example("api-learn-a", "approved")

    client = _client()
    resp = client.get("/api/learning/dashboard", params={"entity_id": "api-learn-a"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["potential_training_examples"] == 1
    assert body["approved_examples"] == 1
    assert body["dataset_size"] == 1


def test_approve_reject_edit_delete_example():
    _make_entity("api-learn-b")
    example_id = _make_example("api-learn-b", "pending")
    client = _client()

    resp = client.post(f"/api/learning/examples/{example_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    resp = client.patch(f"/api/learning/examples/{example_id}", json={"output_text": "edited"})
    assert resp.status_code == 200
    assert resp.json()["output_text"] == "edited"

    resp = client.delete(f"/api/learning/examples/{example_id}")
    assert resp.status_code == 200

    resp = client.get("/api/learning/examples", params={"entity_id": "api-learn-b"})
    assert resp.json() == []


def test_reject_example():
    _make_entity("api-learn-c")
    example_id = _make_example("api-learn-c", "pending")
    client = _client()
    resp = client.post(f"/api/learning/examples/{example_id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
