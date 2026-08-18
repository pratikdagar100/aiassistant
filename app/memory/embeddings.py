"""Local embedding model, lazy-loaded and cached — used for semantic memory
and (Phase 4b) knowledge-base retrieval. Runs on CPU by default so it never
competes with the LLM for the RTX 3060's VRAM (see app.core.config.MemoryConfig).
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("memory.embeddings")


@lru_cache
def _get_model():
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    logger.info(
        "Loading embedding model %s on %s (first call only)",
        settings.memory.embedding_model,
        settings.memory.embedding_device,
    )
    return SentenceTransformer(settings.memory.embedding_model, device=settings.memory.embedding_device)


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return vectors.tolist()


def is_available() -> bool:
    try:
        _get_model()
        return True
    except Exception:  # noqa: BLE001 — model load can fail many ways (missing weights, OOM, etc.)
        logger.warning("Embedding model unavailable", exc_info=True)
        return False
