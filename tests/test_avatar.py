import io

from fastapi.testclient import TestClient
from PIL import Image

from app.api.server import create_app
from app.db.database import session_scope
from app.entities import manager as entity_manager


def _client() -> TestClient:
    return TestClient(create_app())


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def _fake_png() -> bytes:
    img = Image.new("RGB", (64, 64), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_avatar_status_before_face_upload():
    _make_entity("avatar-test-a")
    client = _client()
    resp = client.get("/api/avatar/avatar-test-a/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_face"] is False
    assert body["lip_sync_available"] is False
    assert body["mode"] == "static_state_driven"


def test_upload_and_fetch_face():
    _make_entity("avatar-test-b")
    client = _client()

    resp = client.post(
        "/api/avatar/avatar-test-b/face", files={"file": ("avatar.png", _fake_png(), "image/png")}
    )
    assert resp.status_code == 200

    resp = client.get("/api/avatar/avatar-test-b/status")
    assert resp.json()["has_face"] is True

    resp = client.get("/api/avatar/avatar-test-b/face")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_upload_rejects_bad_extension():
    _make_entity("avatar-test-c")
    client = _client()
    resp = client.post(
        "/api/avatar/avatar-test-c/face", files={"file": ("avatar.exe", b"not an image", "application/octet-stream")}
    )
    assert resp.status_code == 400


def test_delete_face():
    _make_entity("avatar-test-d")
    client = _client()
    client.post("/api/avatar/avatar-test-d/face", files={"file": ("avatar.png", _fake_png(), "image/png")})

    resp = client.delete("/api/avatar/avatar-test-d/face")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    resp = client.get("/api/avatar/avatar-test-d/status")
    assert resp.json()["has_face"] is False
