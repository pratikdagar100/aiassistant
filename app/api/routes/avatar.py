"""Avatar API: upload/fetch entity face image, avatar status."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.avatar import face_manager, manager as avatar_manager
from app.db.database import get_db
from app.db.models import Entity

router = APIRouter()


@router.post("/{entity_id}/face")
async def upload_face(entity_id: str, file: UploadFile, db: Session = Depends(get_db)) -> dict:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(404, f"Entity '{entity_id}' not found")

    data = await file.read()
    try:
        path = face_manager.save_face(entity_id, file.filename or "avatar.png", data)
    except face_manager.FaceError as exc:
        raise HTTPException(400, str(exc)) from exc

    entity.face_path = str(path)
    db.commit()
    return {"entity_id": entity_id, "face_path": str(path)}


@router.get("/{entity_id}/face")
def get_face(entity_id: str) -> FileResponse:
    path = face_manager.face_path(entity_id)
    if not path:
        raise HTTPException(404, f"No face image set for entity '{entity_id}'")
    return FileResponse(path)


@router.delete("/{entity_id}/face")
def delete_face(entity_id: str, db: Session = Depends(get_db)) -> dict:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(404, f"Entity '{entity_id}' not found")
    deleted = face_manager.delete_face(entity_id)
    entity.face_path = None
    db.commit()
    return {"deleted": deleted}


@router.get("/{entity_id}/status")
def avatar_status(entity_id: str, db: Session = Depends(get_db)) -> dict:
    return avatar_manager.get_avatar_status(db, entity_id)
