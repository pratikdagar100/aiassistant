from fastapi.testclient import TestClient

from app.api.server import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_create_list_get_entity_via_api():
    client = _client()

    resp = client.post("/api/entities", json={"id": "api-jarvis", "name": "Jarvis", "autonomy_level": 4})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Jarvis"

    resp = client.get("/api/entities")
    assert resp.status_code == 200
    assert any(e["id"] == "api-jarvis" for e in resp.json())

    resp = client.get("/api/entities/api-jarvis")
    assert resp.status_code == 200
    assert resp.json()["autonomy_level"] == 4


def test_create_duplicate_id_returns_409():
    client = _client()
    client.post("/api/entities", json={"id": "api-conflict", "name": "First"})
    resp = client.post("/api/entities", json={"id": "api-conflict", "name": "Second"})
    assert resp.status_code == 409


def test_invalid_id_format_returns_422():
    client = _client()
    resp = client.post("/api/entities", json={"id": "Not Valid ID!", "name": "X"})
    assert resp.status_code == 422


def test_get_unknown_entity_returns_404():
    client = _client()
    resp = client.get("/api/entities/does-not-exist")
    assert resp.status_code == 404


def test_update_entity_via_api():
    client = _client()
    client.post("/api/entities", json={"id": "api-update", "name": "Before"})
    resp = client.patch("/api/entities/api-update", json={"name": "After"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "After"


def test_delete_entity_via_api():
    client = _client()
    client.post("/api/entities", json={"id": "api-delete", "name": "Temp"})
    resp = client.delete("/api/entities/api-delete")
    assert resp.status_code == 200

    resp = client.get("/api/entities")
    assert not any(e["id"] == "api-delete" for e in resp.json())


def test_duplicate_entity_via_api():
    client = _client()
    client.post("/api/entities", json={"id": "api-dup-src", "name": "Source"})
    resp = client.post("/api/entities/api-dup-src/duplicate", json={"new_id": "api-dup-copy"})
    assert resp.status_code == 200
    assert resp.json()["id"] == "api-dup-copy"


def test_export_import_via_api():
    client = _client()
    client.post("/api/entities", json={"id": "api-export", "name": "Exportable", "personality": "Chill"})
    resp = client.get("/api/entities/api-export/export")
    assert resp.status_code == 200
    snapshot = resp.json()

    resp = client.post("/api/entities/import", json={"data": snapshot, "new_id": "api-imported"})
    assert resp.status_code == 200
    assert resp.json()["personality"] == "Chill"


def test_presets_endpoint():
    client = _client()
    resp = client.get("/api/entities/presets")
    assert resp.status_code == 200
    keys = [p["key"] for p in resp.json()]
    assert "assistant" in keys


def test_profile_endpoint():
    client = _client()
    client.post("/api/entities", json={"id": "api-profile", "name": "Profiled"})
    resp = client.get("/api/entities/api-profile/profile")
    assert resp.status_code == 200
    assert resp.json()["settings"] == {}
