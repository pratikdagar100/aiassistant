"""ChromaDB wrapper for memory embeddings.

One persistent collection ("memories"), entity isolation enforced by a
`where={"entity_id": ...}` filter on every query — not separate collections
per entity, so cross-entity leakage would require an actual code bug in the
filter, not just forgetting to pick the right collection. Global memories
are stored with entity_id="__global__" and are explicitly included/excluded
by callers (see app/memory/retrieval.py).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("memory.vector_store")

GLOBAL_SCOPE = "__global__"


@lru_cache
def _get_collection():
    import chromadb

    settings = get_settings()
    path = settings.memory.resolved_chroma_path()
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection(name="memories")


def upsert_memory(memory_id: int, entity_id: str | None, content: str, embedding: list[float], metadata: dict[str, Any]) -> None:
    collection = _get_collection()
    collection.upsert(
        ids=[str(memory_id)],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{**metadata, "entity_id": entity_id or GLOBAL_SCOPE}],
    )


def delete_memory(memory_id: int) -> None:
    collection = _get_collection()
    collection.delete(ids=[str(memory_id)])


def query(
    query_embedding: list[float],
    entity_id: str,
    top_k: int = 5,
    include_global: bool = True,
) -> list[dict[str, Any]]:
    collection = _get_collection()
    scopes = [entity_id] + ([GLOBAL_SCOPE] if include_global else [])
    where = {"entity_id": {"$in": scopes}} if len(scopes) > 1 else {"entity_id": scopes[0]}

    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where=where,
    )

    hits = []
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    for mem_id, distance, metadata in zip(ids, distances, metadatas):
        hits.append({"memory_id": int(mem_id), "distance": distance, "metadata": metadata})
    return hits
