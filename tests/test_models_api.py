from fastapi.testclient import TestClient

from app.api.server import create_app
from app.core.config import get_settings


def test_list_models_includes_default():
    client = TestClient(create_app())
    resp = client.get("/api/models")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    names = [m["name"] for m in body]
    assert get_settings().llm.default_model in names


def test_select_default_model():
    client = TestClient(create_app())
    resp = client.post("/api/models/default", json={"name": "qwen3:8b"})
    assert resp.status_code == 200
    assert resp.json()["default_model"] == "qwen3:8b"

    resp2 = client.get("/api/models")
    default_entries = [m for m in resp2.json() if m["is_default"]]
    assert len(default_entries) == 1
    assert default_entries[0]["name"] == "qwen3:8b"
