"""Entity CRUD + lifecycle. See docs/entities.md.

Every entity gets its own asset directory (entities/<id>/{face,voice,memory,knowledge})
so later phases (avatar, voice cloning, knowledge base, memory) have an
isolated place to write without touching another entity's data — this is
the mechanism behind the spec's memory/knowledge isolation requirement.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.logging import get_logger
from app.db.models import (
    Conversation,
    Entity,
    EntitySettings,
    KnowledgeDocument,
    Memory,
    Task,
    TrainingExample,
)

logger = get_logger("entities.manager")

ENTITIES_ROOT = PROJECT_ROOT / "entities"
ASSET_SUBDIRS = ("face", "voice", "memory", "knowledge")


class EntityError(ValueError):
    pass


class EntityAlreadyExists(EntityError):
    pass


class EntityNotFound(EntityError):
    pass


def entity_dir(entity_id: str) -> Path:
    return ENTITIES_ROOT / entity_id


def _create_asset_dirs(entity_id: str) -> None:
    for sub in ASSET_SUBDIRS:
        (entity_dir(entity_id) / sub).mkdir(parents=True, exist_ok=True)


def create_entity(
    db: Session,
    *,
    id: str,
    name: str,
    description: str | None = None,
    personality: str | None = None,
    system_prompt: str | None = None,
    model: str = "qwen3:8b",
    language_mode: str = "auto",
    memory_enabled: bool = True,
    computer_access: bool = False,
    autonomy_level: int = 0,
) -> Entity:
    if db.get(Entity, id):
        raise EntityAlreadyExists(f"Entity '{id}' already exists")
    if not (0 <= autonomy_level <= 10):
        raise EntityError("autonomy_level must be between 0 and 10")

    entity = Entity(
        id=id,
        name=name,
        description=description,
        personality=personality,
        system_prompt=system_prompt,
        model=model,
        language_mode=language_mode,
        memory_enabled=memory_enabled,
        computer_access=computer_access,
        autonomy_level=autonomy_level,
    )
    db.add(entity)
    db.flush()
    _create_asset_dirs(id)
    logger.info("Created entity '%s' (%s)", id, name)
    return entity


def get_entity(db: Session, entity_id: str) -> Entity:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise EntityNotFound(f"Entity '{entity_id}' not found")
    return entity


def list_entities(db: Session, include_inactive: bool = False) -> list[Entity]:
    q = db.query(Entity)
    if not include_inactive:
        q = q.filter_by(is_active=True)
    return q.order_by(Entity.created_at).all()


def update_entity(db: Session, entity_id: str, **fields) -> Entity:
    entity = get_entity(db, entity_id)
    allowed = {
        "name",
        "description",
        "personality",
        "system_prompt",
        "model",
        "language_mode",
        "memory_enabled",
        "computer_access",
        "autonomy_level",
        "face_path",
        "voice_id",
        "avatar_config",
    }
    for key, value in fields.items():
        if key not in allowed:
            raise EntityError(f"Cannot set field '{key}'")
        if key == "autonomy_level" and value is not None and not (0 <= value <= 10):
            raise EntityError("autonomy_level must be between 0 and 10")
        setattr(entity, key, value)
    db.flush()
    return entity


def delete_entity(db: Session, entity_id: str, *, purge_files: bool = False) -> None:
    """Soft-deletes by default (is_active=False); purge_files also removes
    entities/<id>/ from disk and hard-deletes the DB row (cascades to
    conversations/memories/knowledge/tasks/training examples via FKs)."""
    entity = get_entity(db, entity_id)
    if purge_files:
        db.delete(entity)
        db.flush()
        d = entity_dir(entity_id)
        if d.exists():
            shutil.rmtree(d)
        logger.info("Purged entity '%s' (DB row + files)", entity_id)
    else:
        entity.is_active = False
        db.flush()
        logger.info("Soft-deleted entity '%s'", entity_id)


def duplicate_entity(db: Session, source_id: str, new_id: str, new_name: str | None = None) -> Entity:
    source = get_entity(db, source_id)
    if db.get(Entity, new_id):
        raise EntityAlreadyExists(f"Entity '{new_id}' already exists")

    clone = create_entity(
        db,
        id=new_id,
        name=new_name or f"{source.name} (copy)",
        description=source.description,
        personality=source.personality,
        system_prompt=source.system_prompt,
        model=source.model,
        language_mode=source.language_mode,
        memory_enabled=source.memory_enabled,
        computer_access=source.computer_access,
        autonomy_level=source.autonomy_level,
    )
    for setting in source.settings:
        db.add(EntitySettings(entity_id=new_id, key=setting.key, value=setting.value))
    # Conversations, memories, knowledge, and training examples are
    # intentionally NOT copied — a duplicate starts with a clean history,
    # matching the spec's entity memory isolation requirement.
    return clone


def export_entity(db: Session, entity_id: str) -> dict:
    """Returns a JSON-serializable snapshot for backup/import.

    Never includes credentials/secrets (there are none on Entity) and never
    includes raw conversation transcripts — memories and profile only, per
    the spec's "do not export secret/API credentials" requirement.
    """
    entity = get_entity(db, entity_id)
    memories = db.query(Memory).filter_by(entity_id=entity_id).all()
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
        "voice_id": entity.voice_id,
        "avatar_config": entity.avatar_config,
        "settings": {s.key: s.value for s in entity.settings},
        "memories": [
            {
                "memory_type": m.memory_type,
                "category": m.category,
                "content": m.content,
                "importance": m.importance,
                "confidence": m.confidence,
                "pinned": m.pinned,
            }
            for m in memories
        ],
    }


def import_entity(db: Session, data: dict, *, new_id: str | None = None) -> Entity:
    entity_id = new_id or data["id"]
    entity = create_entity(
        db,
        id=entity_id,
        name=data["name"],
        description=data.get("description"),
        personality=data.get("personality"),
        system_prompt=data.get("system_prompt"),
        model=data.get("model", "qwen3:8b"),
        language_mode=data.get("language_mode", "auto"),
        memory_enabled=data.get("memory_enabled", True),
        computer_access=data.get("computer_access", False),
        autonomy_level=data.get("autonomy_level", 0),
    )
    for key, value in (data.get("settings") or {}).items():
        db.add(EntitySettings(entity_id=entity_id, key=key, value=value))
    for mem in data.get("memories", []):
        db.add(
            Memory(
                entity_id=entity_id,
                memory_type=mem.get("memory_type", "entity"),
                category=mem.get("category", "other"),
                content=mem["content"],
                importance=mem.get("importance", 0.5),
                confidence=mem.get("confidence", 1.0),
                pinned=mem.get("pinned", False),
                source="import",
            )
        )
    return entity


def entity_stats(db: Session, entity_id: str) -> dict:
    get_entity(db, entity_id)  # raises if missing
    return {
        "conversation_count": db.query(Conversation).filter_by(entity_id=entity_id).count(),
        "memory_count": db.query(Memory).filter_by(entity_id=entity_id).count(),
        "knowledge_document_count": db.query(KnowledgeDocument).filter_by(entity_id=entity_id).count(),
        "task_count": db.query(Task).filter_by(entity_id=entity_id).count(),
        "training_example_count": db.query(TrainingExample).filter_by(entity_id=entity_id).count(),
    }
