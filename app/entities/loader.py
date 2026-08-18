"""Assembles the full runtime profile for an entity: base row + extended
key/value settings merged into one object. Chat (Phase 2), memory retrieval
(Phase 4), and the agent planner (Phase 8) all read entities through this
rather than querying Entity/EntitySettings separately, so a new extended
setting doesn't require touching every caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.entities.manager import get_entity


@dataclass
class EntityProfile:
    id: str
    name: str
    description: str | None
    personality: str | None
    system_prompt: str | None
    model: str
    language_mode: str
    memory_enabled: bool
    computer_access: bool
    autonomy_level: int
    face_path: str | None
    voice_id: str | None
    avatar_config: dict | None
    settings: dict = field(default_factory=dict)

    def setting(self, key: str, default=None):
        return self.settings.get(key, default)


def load_entity_profile(db: Session, entity_id: str) -> EntityProfile:
    entity = get_entity(db, entity_id)
    return EntityProfile(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        personality=entity.personality,
        system_prompt=entity.system_prompt,
        model=entity.model,
        language_mode=entity.language_mode,
        memory_enabled=entity.memory_enabled,
        computer_access=entity.computer_access,
        autonomy_level=entity.autonomy_level,
        face_path=entity.face_path,
        voice_id=entity.voice_id,
        avatar_config=entity.avatar_config,
        settings={s.key: s.value for s in entity.settings},
    )
