import pytest

from app.db.database import session_scope
from app.db.models import Conversation, Memory
from app.entities import manager
from app.entities.loader import load_entity_profile


def test_create_get_list_entity():
    with session_scope() as db:
        manager.create_entity(db, id="test-alice", name="Alice", autonomy_level=3)

    with session_scope() as db:
        alice = manager.get_entity(db, "test-alice")
        assert alice.name == "Alice"
        assert alice.autonomy_level == 3
        ids = [e.id for e in manager.list_entities(db)]
        assert "test-alice" in ids


def test_create_duplicate_id_raises():
    with session_scope() as db:
        manager.create_entity(db, id="test-dupe", name="First")

    with pytest.raises(manager.EntityAlreadyExists):
        with session_scope() as db:
            manager.create_entity(db, id="test-dupe", name="Second")


def test_invalid_autonomy_level_raises():
    with pytest.raises(manager.EntityError):
        with session_scope() as db:
            manager.create_entity(db, id="test-bad-autonomy", name="X", autonomy_level=99)


def test_update_entity():
    with session_scope() as db:
        manager.create_entity(db, id="test-update", name="Before")

    with session_scope() as db:
        manager.update_entity(db, "test-update", name="After", autonomy_level=5)

    with session_scope() as db:
        e = manager.get_entity(db, "test-update")
        assert e.name == "After"
        assert e.autonomy_level == 5


def test_soft_delete_hides_from_default_listing():
    with session_scope() as db:
        manager.create_entity(db, id="test-soft-delete", name="Temp")

    with session_scope() as db:
        manager.delete_entity(db, "test-soft-delete", purge_files=False)

    with session_scope() as db:
        ids = [e.id for e in manager.list_entities(db)]
        assert "test-soft-delete" not in ids
        ids_all = [e.id for e in manager.list_entities(db, include_inactive=True)]
        assert "test-soft-delete" in ids_all


def test_purge_delete_cascades_conversations_and_memories():
    with session_scope() as db:
        manager.create_entity(db, id="test-purge", name="Temp")
        db.add(Conversation(entity_id="test-purge"))
        db.add(Memory(entity_id="test-purge", memory_type="entity", category="fact", content="x"))

    with session_scope() as db:
        manager.delete_entity(db, "test-purge", purge_files=True)

    with session_scope() as db:
        assert db.query(Conversation).filter_by(entity_id="test-purge").count() == 0
        assert db.query(Memory).filter_by(entity_id="test-purge").count() == 0
        with pytest.raises(manager.EntityNotFound):
            manager.get_entity(db, "test-purge")


def test_memory_isolation_between_entities():
    """Core requirement: entity A must never see entity B's memories."""
    with session_scope() as db:
        manager.create_entity(db, id="test-friday-iso", name="Friday")
        manager.create_entity(db, id="test-jarvis-iso", name="Jarvis")
        db.add(Memory(entity_id="test-friday-iso", memory_type="entity", category="fact", content="Friday secret"))
        db.add(Memory(entity_id="test-jarvis-iso", memory_type="entity", category="fact", content="Jarvis secret"))

    with session_scope() as db:
        friday_memories = db.query(Memory).filter_by(entity_id="test-friday-iso").all()
        jarvis_memories = db.query(Memory).filter_by(entity_id="test-jarvis-iso").all()

        assert len(friday_memories) == 1
        assert friday_memories[0].content == "Friday secret"
        assert len(jarvis_memories) == 1
        assert jarvis_memories[0].content == "Jarvis secret"
        assert friday_memories[0].content != jarvis_memories[0].content


def test_duplicate_entity_does_not_copy_memories():
    with session_scope() as db:
        manager.create_entity(db, id="test-dup-src", name="Source", personality="Witty")
        db.add(Memory(entity_id="test-dup-src", memory_type="entity", category="fact", content="secret"))

    with session_scope() as db:
        manager.duplicate_entity(db, "test-dup-src", "test-dup-copy")

    with session_scope() as db:
        clone = manager.get_entity(db, "test-dup-copy")
        assert clone.personality == "Witty"
        assert db.query(Memory).filter_by(entity_id="test-dup-copy").count() == 0


def test_export_import_roundtrip():
    with session_scope() as db:
        manager.create_entity(db, id="test-export", name="Exportable", personality="Curious")
        db.add(Memory(entity_id="test-export", memory_type="entity", category="preference", content="likes tea"))

    with session_scope() as db:
        snapshot = manager.export_entity(db, "test-export")
    assert "credentials" not in snapshot
    assert "api_key" not in snapshot

    with session_scope() as db:
        imported = manager.import_entity(db, snapshot, new_id="test-imported")

    with session_scope() as db:
        e = manager.get_entity(db, "test-imported")
        assert e.personality == "Curious"
        mems = db.query(Memory).filter_by(entity_id="test-imported").all()
        assert len(mems) == 1
        assert mems[0].content == "likes tea"


def test_load_entity_profile_merges_settings():
    from app.db.models import EntitySettings

    with session_scope() as db:
        manager.create_entity(db, id="test-profile", name="Profiled")
        db.flush()
        db.add(EntitySettings(entity_id="test-profile", key="voice_engine", value={"engine": "piper"}))

    with session_scope() as db:
        profile = load_entity_profile(db, "test-profile")
        assert profile.name == "Profiled"
        assert profile.setting("voice_engine") == {"engine": "piper"}
        assert profile.setting("nonexistent", "default") == "default"
