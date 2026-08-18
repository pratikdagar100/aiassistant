from fastapi.testclient import TestClient

from app.api.server import create_app


def test_health_endpoint_reports_database_ready():
    client = TestClient(create_app())
    resp = client.get("/api/health")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] in {"READY", "WARNING", "ERROR"}
    assert body["app_name"] == "PratikAI"
    assert "database" in body["checks"]
    assert body["checks"]["database"]["status"] == "READY"
    assert "logging" in body["checks"]
    assert "ollama" in body["checks"]
