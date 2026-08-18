"""Per-entity permission API (spec section 28)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.entities.manager import EntityNotFound, get_entity
from app.security.permissions import DEFAULT_PERMISSIONS, get_permissions, set_permissions

router = APIRouter()


class SetPermissionsRequest(BaseModel):
    permissions: dict[str, str]


@router.get("/{entity_id}")
def get_entity_permissions(entity_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        get_entity(db, entity_id)
    except EntityNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    return get_permissions(db, entity_id)


@router.put("/{entity_id}")
def update_entity_permissions(entity_id: str, req: SetPermissionsRequest, db: Session = Depends(get_db)) -> dict:
    try:
        get_entity(db, entity_id)
    except EntityNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    try:
        updated = set_permissions(db, entity_id, req.permissions)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return updated


@router.get("/{entity_id}/defaults")
def get_default_permissions(entity_id: str) -> dict:
    return dict(DEFAULT_PERMISSIONS)
