from fastapi.testclient import TestClient

from app.api.server import create_app
from app.db.seed import seed_default_entity


def _client() -> TestClient:
    seed_default_entity()
    return TestClient(create_app())


def test_chat_unknown_entity_returns_404():
    client = _client()
    resp = client.post("/api/chat", json={"message": "hi", "entity_id": "does-not-exist"})
    assert resp.status_code == 404


def test_chat_conversation_id_for_wrong_entity_returns_404():
    client = _client()
    resp = client.post(
        "/api/chat",
        json={"message": "hi", "entity_id": "friday", "conversation_id": 999999},
    )
    assert resp.status_code == 404


def test_list_conversations_empty_for_fresh_entity():
    client = _client()
    resp = client.get("/api/chat/conversations", params={"entity_id": "friday"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_messages_for_unknown_conversation_404():
    client = _client()
    resp = client.get("/api/chat/conversations/999999/messages")
    assert resp.status_code == 404
