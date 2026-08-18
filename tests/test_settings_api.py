from fastapi.testclient import TestClient

from app.api.server import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_get_settings_defaults():
    client = _client()
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_entity"] == "friday"
    assert "startup_task_registered" in body


def test_update_settings_persists():
    client = _client()
    resp = client.patch("/api/settings", json={"values": {"auto_mic": True}})
    assert resp.status_code == 200
    assert resp.json()["auto_mic"] is True

    resp = client.get("/api/settings")
    assert resp.json()["auto_mic"] is True


def test_update_settings_ignores_unknown_keys():
    client = _client()
    resp = client.patch("/api/settings", json={"values": {"not_a_real_setting": 123}})
    assert resp.status_code == 200
    assert "not_a_real_setting" not in resp.json()
