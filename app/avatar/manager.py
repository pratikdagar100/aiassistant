"""Avatar configuration per entity — what face to show and whether
real-time lip sync is available (it isn't, by default — see musetalk.py).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.avatar import face_manager, musetalk
from app.db.models import Entity


def get_avatar_status(db: Session, entity_id: str) -> dict:
    entity = db.get(Entity, entity_id)
    path = face_manager.face_path(entity_id)
    return {
        "entity_id": entity_id,
        "has_face": path is not None,
        "voice_id": entity.voice_id if entity else None,
        "lip_sync_available": musetalk.is_available(),
        "mode": "lip_sync" if musetalk.is_available() else "static_state_driven",
    }
