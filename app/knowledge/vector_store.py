"""ChromaDB collection for knowledge-base chunks — separate from the
memories collection (app/memory/vector_store.py) even though both share the
same Chroma client/on-disk store, so a knowledge query never accidentally
surfaces a personal memory or vice versa.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings

GLOBAL_SCOPE = "__global__"


@lru_cache
def _get_collection():
    import chromadb

    settings = get_settings()
    path = settings.memory.resolved_chroma_path()
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection(name="knowledge_chunks")


def upsert_chunk(chunk_id: int, entity_id: str | None, document_id: int, content: str, embedding: list[float]) -> None:
    collection = _get_collection()
    collection.upsert(
        ids=[str(chunk_id)],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"entity_id": entity_id or GLOBAL_SCOPE, "document_id": document_id}],
    )


def delete_document_chunks(chunk_ids: list[int]) -> None:
    if not chunk_ids:
        return
    collection = _get_collection()
    collection.delete(ids=[str(i) for i in chunk_ids])


def query(query_embedding: list[float], entity_id: str, top_k: int = 5, include_global: bool = True) -> list[dict[str, Any]]:
    collection = _get_collection()
    if collection.count() == 0:
        return []

    scopes = [entity_id] + ([GLOBAL_SCOPE] if include_global else [])
    where = {"entity_id": {"$in": scopes}} if len(scopes) > 1 else {"entity_id": scopes[0]}

    result = collection.query(query_embeddings=[query_embedding], n_results=min(top_k, collection.count()), where=where)

    hits = []
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    documents = result.get("documents", [[]])[0]
    for chunk_id, distance, doc in zip(ids, distances, documents):
        hits.append({"chunk_id": int(chunk_id), "distance": distance, "content": doc})
    return hits
