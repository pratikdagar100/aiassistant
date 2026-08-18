"""Uses the real embedding model — no mocking."""

from app.db.database import session_scope
from app.entities import manager as entity_manager
from app.knowledge import ingest as ingest_module
from app.knowledge.chunker import chunk_text
from app.knowledge.retrieval import retrieve_relevant_chunks


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def test_chunk_text_splits_long_text():
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) == 3
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_text_short_text_single_chunk():
    assert chunk_text("short text") == ["short text"]


def test_ingest_txt_document_and_retrieve():
    _make_entity("test-kb-a")
    content = b"PratikAI's default LLM is Qwen3 8B, served locally through Ollama."

    with session_scope() as db:
        doc = ingest_module.ingest_document(db, entity_id="test-kb-a", filename="notes.txt", data=content)
        assert doc.status == "indexed"
        assert len(doc.chunks) == 1

    with session_scope() as db:
        results = retrieve_relevant_chunks(db, "test-kb-a", "What LLM does this project use?", top_k=1)
        assert len(results) >= 1
        assert "Qwen3" in results[0].content


def test_ingest_unsupported_extension_marks_error():
    _make_entity("test-kb-b")
    with session_scope() as db:
        doc = ingest_module.ingest_document(db, entity_id="test-kb-b", filename="virus.exe", data=b"not real")
        assert doc.status == "error"
        assert doc.error_message


def test_delete_document_removes_chunks():
    _make_entity("test-kb-c")
    with session_scope() as db:
        doc = ingest_module.ingest_document(db, entity_id="test-kb-c", filename="notes.txt", data=b"hello world")
        doc_id = doc.id

    with session_scope() as db:
        ingest_module.delete_document(db, doc_id)

    with session_scope() as db:
        from app.db.models import KnowledgeDocument

        assert db.get(KnowledgeDocument, doc_id) is None


def test_knowledge_isolated_between_entities():
    _make_entity("test-kb-iso-a")
    _make_entity("test-kb-iso-b")
    with session_scope() as db:
        ingest_module.ingest_document(db, entity_id="test-kb-iso-a", filename="a.txt", data=b"Entity A secret project codename: BLUEFALCON.")
        ingest_module.ingest_document(db, entity_id="test-kb-iso-b", filename="b.txt", data=b"Entity B secret project codename: REDHAWK.")

    with session_scope() as db:
        results = retrieve_relevant_chunks(db, "test-kb-iso-a", "What is the project codename?", top_k=5)
        contents = [c.content for c in results]

    assert any("BLUEFALCON" in c for c in contents)
    assert not any("REDHAWK" in c for c in contents)
