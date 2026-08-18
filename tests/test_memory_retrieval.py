"""Uses the real local embedding model — no mocking, since the whole point
is verifying semantic search actually finds relevant content. Slower than
the rest of the suite (model load on first call) but this is the one place
that matters most to get right per spec section 11.
"""

from app.db.database import session_scope
from app.entities import manager as entity_manager
from app.memory import database as memory_db
from app.memory.retrieval import retrieve_relevant_memories


def test_semantic_search_finds_relevant_memory():
    with session_scope() as db:
        entity_manager.create_entity(db, id="test-retrieval", name="Retrieval Test")
        memory_db.create_memory(
            db, entity_id="test-retrieval", content="User's favorite programming language is Python.", category="fact"
        )
        memory_db.create_memory(
            db, entity_id="test-retrieval", content="User enjoys hiking in the mountains on weekends.", category="fact"
        )
        memory_db.create_memory(
            db, entity_id="test-retrieval", content="User's cat is named Whiskers.", category="fact"
        )

    with session_scope() as db:
        results = retrieve_relevant_memories(db, "test-retrieval", "What programming language do I like?", top_k=1)
        contents = [m.content for m in results]

    assert len(contents) >= 1
    assert "Python" in contents[0]


def test_pinned_memories_always_included():
    with session_scope() as db:
        entity_manager.create_entity(db, id="test-retrieval-pin", name="Pin Test")
        pinned = memory_db.create_memory(
            db, entity_id="test-retrieval-pin", content="Completely unrelated pinned fact about weather.", category="fact", pinned=True
        )
        pinned_id = pinned.id

    with session_scope() as db:
        results = retrieve_relevant_memories(db, "test-retrieval-pin", "Tell me about programming languages", top_k=1)
        result_ids = [m.id for m in results]

    assert pinned_id in result_ids


def test_retrieval_respects_entity_isolation():
    with session_scope() as db:
        entity_manager.create_entity(db, id="test-retrieval-iso-a", name="A")
        entity_manager.create_entity(db, id="test-retrieval-iso-b", name="B")
        memory_db.create_memory(
            db, entity_id="test-retrieval-iso-a", content="Entity A's secret favorite color is blue.", category="fact"
        )
        memory_db.create_memory(
            db, entity_id="test-retrieval-iso-b", content="Entity B's secret favorite color is red.", category="fact"
        )

    with session_scope() as db:
        results = retrieve_relevant_memories(db, "test-retrieval-iso-a", "What is the favorite color?", top_k=5)
        contents = [m.content for m in results]

    assert any("blue" in c for c in contents)
    assert not any("red" in c for c in contents)
