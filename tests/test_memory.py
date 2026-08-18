import pytest

from app.db.database import session_scope
from app.entities import manager as entity_manager
from app.memory import database as memory_db


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def test_create_and_list_memory():
    _make_entity("test-mem-a")
    with session_scope() as db:
        memory_db.create_memory(
            db,
            entity_id="test-mem-a",
            content="User prefers VS Code over PyCharm.",
            memory_type="semantic",
            category="preference",
        )

    with session_scope() as db:
        memories = memory_db.list_memories(db, "test-mem-a")
        assert len(memories) == 1
        assert memories[0].content == "User prefers VS Code over PyCharm."
        assert memories[0].category == "preference"


def test_invalid_category_raises():
    _make_entity("test-mem-b")
    with pytest.raises(memory_db.MemoryError):
        with session_scope() as db:
            memory_db.create_memory(db, entity_id="test-mem-b", content="x", category="not-a-real-category")


def test_search_filters_by_content():
    _make_entity("test-mem-c")
    with session_scope() as db:
        memory_db.create_memory(db, entity_id="test-mem-c", content="Likes hiking on weekends", category="fact")
        memory_db.create_memory(db, entity_id="test-mem-c", content="Main project is called PratikAI", category="project")

    with session_scope() as db:
        results = memory_db.list_memories(db, "test-mem-c", search="PratikAI")
        assert len(results) == 1
        assert "PratikAI" in results[0].content


def test_pin_and_unpin():
    _make_entity("test-mem-d")
    with session_scope() as db:
        m = memory_db.create_memory(db, entity_id="test-mem-d", content="pin me", category="fact")
        mem_id = m.id

    with session_scope() as db:
        memory_db.pin_memory(db, mem_id, True)
    with session_scope() as db:
        assert memory_db.list_memories(db, "test-mem-d", pinned_only=True)[0].id == mem_id

    with session_scope() as db:
        memory_db.pin_memory(db, mem_id, False)
    with session_scope() as db:
        assert memory_db.list_memories(db, "test-mem-d", pinned_only=True) == []


def test_update_memory_content():
    _make_entity("test-mem-e")
    with session_scope() as db:
        m = memory_db.create_memory(db, entity_id="test-mem-e", content="old content", category="fact")
        mem_id = m.id

    with session_scope() as db:
        memory_db.update_memory(db, mem_id, content="new content")

    with session_scope() as db:
        updated = memory_db.list_memories(db, "test-mem-e")[0]
        assert updated.content == "new content"


def test_delete_memory():
    _make_entity("test-mem-f")
    with session_scope() as db:
        m = memory_db.create_memory(db, entity_id="test-mem-f", content="temp", category="fact")
        mem_id = m.id

    with session_scope() as db:
        memory_db.delete_memory(db, mem_id)

    with session_scope() as db:
        assert memory_db.list_memories(db, "test-mem-f") == []


def test_clear_entity_memory_does_not_affect_other_entities():
    _make_entity("test-mem-g1")
    _make_entity("test-mem-g2")
    with session_scope() as db:
        memory_db.create_memory(db, entity_id="test-mem-g1", content="g1 memory", category="fact")
        memory_db.create_memory(db, entity_id="test-mem-g2", content="g2 memory", category="fact")

    with session_scope() as db:
        deleted = memory_db.clear_entity_memory(db, "test-mem-g1")
        assert deleted == 1

    with session_scope() as db:
        assert memory_db.list_memories(db, "test-mem-g1") == []
        assert len(memory_db.list_memories(db, "test-mem-g2")) == 1
