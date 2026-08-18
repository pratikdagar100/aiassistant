"""Entity Manager API (spec section 3): create/edit/delete/duplicate/export/import."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import get_db
from app.entities import manager
from app.entities.loader import load_entity_profile
from app.entities.profiles import PRESETS

router = APIRouter()
logger = get_logger("api.entities")


class CreateEntityRequest(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    name: str
    description: str | None = None
    personality: str | None = None
    system_prompt: str | None = None
    model: str = "qwen3:8b"
    language_mode: str = "auto"
    memory_enabled: bool = True
    computer_access: bool = False
    autonomy_level: int = 0


class UpdateEntityRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    personality: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    language_mode: str | None = None
    memory_enabled: bool | None = None
    computer_access: bool | None = None
    autonomy_level: int | None = None
    voice_id: str | None = None


class DuplicateEntityRequest(BaseModel):
    new_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    new_name: str | None = None


class ImportEntityRequest(BaseModel):
    data: dict
    new_id: str | None = None


def _entity_to_dict(entity) -> dict:
    return {
        "id": entity.id,
        "name": entity.name,
        "description": entity.description,
        "personality": entity.personality,
        "system_prompt": entity.system_prompt,
        "model": entity.model,
        "language_mode": entity.language_mode,
        "memory_enabled": entity.memory_enabled,
        "computer_access": entity.computer_access,
        "autonomy_level": entity.autonomy_level,
        "face_path": entity.face_path,
        "voice_id": entity.voice_id,
        "is_active": entity.is_active,
        "created_at": entity.created_at.isoformat(),
        "last_active_at": entity.last_active_at.isoformat() if entity.last_active_at else None,
    }


@router.get("/presets")
def get_presets() -> list[dict]:
    return [{"key": p.key, "label": p.label, "personality": p.personality, "system_prompt": p.system_prompt} for p in PRESETS]


@router.get("")
def list_entities(include_inactive: bool = False, db: Session = Depends(get_db)) -> list[dict]:
    return [_entity_to_dict(e) for e in manager.list_entities(db, include_inactive=include_inactive)]


@router.post("")
def create_entity(req: CreateEntityRequest, db: Session = Depends(get_db)) -> dict:
    try:
        entity = manager.create_entity(db, **req.model_dump())
        db.commit()
    except manager.EntityAlreadyExists as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except manager.EntityError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return _entity_to_dict(entity)


@router.get("/{entity_id}")
def get_entity(entity_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        entity = manager.get_entity(db, entity_id)
    except manager.EntityNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    return _entity_to_dict(entity)


@router.get("/{entity_id}/profile")
def get_entity_profile(entity_id: str, db: Session = Depends(get_db)) -> dict:
    """Full runtime profile: base fields merged with extended entity_settings."""
    try:
        profile = load_entity_profile(db, entity_id)
    except manager.EntityNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "personality": profile.personality,
        "system_prompt": profile.system_prompt,
        "model": profile.model,
        "language_mode": profile.language_mode,
        "memory_enabled": profile.memory_enabled,
        "computer_access": profile.computer_access,
        "autonomy_level": profile.autonomy_level,
        "face_path": profile.face_path,
        "voice_id": profile.voice_id,
        "avatar_config": profile.avatar_config,
        "settings": profile.settings,
    }


@router.get("/{entity_id}/stats")
def get_entity_stats(entity_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        return manager.entity_stats(db, entity_id)
    except manager.EntityNotFound as exc:
        raise HTTPException(404, str(exc)) from exc


@router.patch("/{entity_id}")
def update_entity(entity_id: str, req: UpdateEntityRequest, db: Session = Depends(get_db)) -> dict:
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    try:
        entity = manager.update_entity(db, entity_id, **fields)
        db.commit()
    except manager.EntityNotFound as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except manager.EntityError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return _entity_to_dict(entity)


@router.delete("/{entity_id}")
def delete_entity(entity_id: str, purge: bool = False, db: Session = Depends(get_db)) -> dict:
    try:
        manager.delete_entity(db, entity_id, purge_files=purge)
        db.commit()
    except manager.EntityNotFound as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return {"deleted": entity_id, "purged": purge}


@router.post("/{entity_id}/duplicate")
def duplicate_entity(entity_id: str, req: DuplicateEntityRequest, db: Session = Depends(get_db)) -> dict:
    try:
        clone = manager.duplicate_entity(db, entity_id, req.new_id, req.new_name)
        db.commit()
    except manager.EntityAlreadyExists as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except manager.EntityNotFound as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    return _entity_to_dict(clone)


@router.get("/{entity_id}/export")
def export_entity(entity_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        return manager.export_entity(db, entity_id)
    except manager.EntityNotFound as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/import")
def import_entity(req: ImportEntityRequest, db: Session = Depends(get_db)) -> dict:
    try:
        entity = manager.import_entity(db, req.data, new_id=req.new_id)
        db.commit()
    except manager.EntityAlreadyExists as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except (KeyError, manager.EntityError) as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return _entity_to_dict(entity)
