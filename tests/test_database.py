from app.db.database import session_scope
from app.db.models import Entity, EntitySettings


def test_create_and_query_entity():
    with session_scope() as db:
        entity = Entity(
            id="test-friday",
            name="Friday",
            personality="Intelligent, calm, helpful and witty",
            system_prompt="You are Friday, a personal AI assistant.",
            model="qwen3:8b",
            autonomy_level=7,
        )
        db.add(entity)

    with session_scope() as db:
        fetched = db.get(Entity, "test-friday")
        assert fetched is not None
        assert fetched.name == "Friday"
        assert fetched.autonomy_level == 7
        assert fetched.memory_enabled is True  # column default
        assert fetched.is_active is True


def test_entity_settings_cascade_delete():
    with session_scope() as db:
        entity = Entity(id="test-cascade", name="Cascade Test")
        db.add(entity)
        db.flush()
        db.add(EntitySettings(entity_id=entity.id, key="voice", value={"engine": "piper"}))

    with session_scope() as db:
        assert db.get(Entity, "test-cascade") is not None
        db.delete(db.get(Entity, "test-cascade"))

    with session_scope() as db:
        remaining = db.query(EntitySettings).filter_by(entity_id="test-cascade").all()
        assert remaining == []


def test_entity_settings_unique_constraint():
    from sqlalchemy.exc import IntegrityError

    with session_scope() as db:
        db.add(Entity(id="test-unique", name="Unique Test"))

    with session_scope() as db:
        db.add(EntitySettings(entity_id="test-unique", key="voice", value={"engine": "piper"}))

    try:
        with session_scope() as db:
            db.add(EntitySettings(entity_id="test-unique", key="voice", value={"engine": "other"}))
        raised = False
    except IntegrityError:
        raised = True

    assert raised
