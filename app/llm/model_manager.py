"""Model lifecycle management: what's installed, VRAM footprint, default model.

RTX 3060 has 12GB VRAM (see README) — this module exists so the rest of the
app can make VRAM-aware decisions instead of assuming unlimited headroom
(section 41 of the spec: don't assume multiple large models stay loaded
simultaneously). Phase 2 only needs list/status/select; Phase 9-10 (vision,
avatar) are the modules that will actually contend for VRAM and consult this.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import session_scope
from app.db.models import ModelRecord
from app.llm.ollama import OllamaClient, OllamaError

logger = get_logger("llm.model_manager")


@dataclass
class ModelStatus:
    name: str
    installed: bool
    size_bytes: int | None
    parameter_size: str | None
    quantization: str | None
    is_default: bool


async def list_models() -> list[ModelStatus]:
    """Cross-references Ollama's installed models with our default-model setting."""
    settings = get_settings()
    client = OllamaClient()

    installed: dict[str, dict] = {}
    if await client.is_available():
        try:
            for m in await client.list_models():
                installed[m["name"]] = m
        except OllamaError:
            logger.warning("Ollama reachable but /api/tags failed", exc_info=True)

    default_model = _get_default_model_name() or settings.llm.default_model

    results = []
    seen = set()
    for name, info in installed.items():
        details = info.get("details", {})
        results.append(
            ModelStatus(
                name=name,
                installed=True,
                size_bytes=info.get("size"),
                parameter_size=details.get("parameter_size"),
                quantization=details.get("quantization_level"),
                is_default=(name == default_model),
            )
        )
        seen.add(name)

    if default_model not in seen:
        results.append(
            ModelStatus(
                name=default_model,
                installed=False,
                size_bytes=None,
                parameter_size=None,
                quantization=None,
                is_default=True,
            )
        )

    return results


def _get_default_model_name() -> str | None:
    from app.db.models import SettingRecord

    with session_scope() as db:
        row = db.query(SettingRecord).filter_by(key="default_llm_model").first()
        return row.value.get("name") if row and row.value else None


def set_default_model(name: str) -> None:
    from app.db.models import SettingRecord

    with session_scope() as db:
        row = db.query(SettingRecord).filter_by(key="default_llm_model").first()
        if row:
            row.value = {"name": name}
        else:
            db.add(SettingRecord(key="default_llm_model", value={"name": name}))


def get_default_model() -> str:
    return _get_default_model_name() or get_settings().llm.default_model


async def sync_model_record(name: str) -> None:
    """Upserts a ModelRecord row from live Ollama data — called after pulls."""
    client = OllamaClient()
    try:
        info = await client.show(name)
    except OllamaError:
        logger.warning("Could not fetch model info for %s", name, exc_info=True)
        return

    details = info.get("details", {})
    size_bytes = None
    for m in await client.list_models():
        if m["name"] == name:
            size_bytes = m.get("size")
            break

    with session_scope() as db:
        record = db.query(ModelRecord).filter_by(name=name).first()
        if not record:
            record = ModelRecord(name=name, type="llm")
            db.add(record)
        record.status = "installed"
        record.size_bytes = size_bytes
        # Rough VRAM heuristic: quantized weights dominate VRAM use, so file
        # size on disk is a reasonable first-order estimate (see docs).
        record.vram_estimate_mb = int(size_bytes / (1024 * 1024)) if size_bytes else None
        record.purpose = f"{details.get('family', 'LLM')} {details.get('parameter_size', '')}".strip()
