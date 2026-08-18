"""Per-entity face image storage (spec section 9 workflow: upload face image
-> save avatar -> use for entity). Stored under entities/<id>/face/, the
same isolated directory app/entities/manager.py already creates per entity.
"""

from __future__ import annotations

from pathlib import Path

from app.entities.manager import entity_dir

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_BYTES = 10_000_000


class FaceError(ValueError):
    pass


def face_path(entity_id: str) -> Path | None:
    face_dir = entity_dir(entity_id) / "face"
    if not face_dir.exists():
        return None
    for ext in ALLOWED_EXTENSIONS:
        candidate = face_dir / f"avatar{ext}"
        if candidate.exists():
            return candidate
    return None


def save_face(entity_id: str, filename: str, data: bytes) -> Path:
    if len(data) > MAX_FILE_BYTES:
        raise FaceError(f"Image too large ({len(data)} bytes, max {MAX_FILE_BYTES})")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FaceError(f"Unsupported image type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    face_dir = entity_dir(entity_id) / "face"
    face_dir.mkdir(parents=True, exist_ok=True)

    # Remove any previous avatar (possibly a different extension) before saving the new one.
    for existing_ext in ALLOWED_EXTENSIONS:
        old = face_dir / f"avatar{existing_ext}"
        if old.exists():
            old.unlink()

    target = face_dir / f"avatar{ext}"
    target.write_bytes(data)
    return target


def delete_face(entity_id: str) -> bool:
    path = face_path(entity_id)
    if path:
        path.unlink()
        return True
    return False
