"""Health check endpoint.

Phase 1 checks only the components that exist so far: config, database,
log directory, and (best-effort, non-fatal) whether Ollama is reachable.
Later phases extend this with STT/TTS/vision/avatar/frontend checks — see
docs/troubleshooting.md and scripts/health_check.ps1.
"""

from __future__ import annotations

import time

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import engine

router = APIRouter()
logger = get_logger("health")


def _check_database() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "READY"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Database health check failed")
        return {"status": "ERROR", "detail": str(exc)}


def _check_log_dir() -> dict:
    settings = get_settings()
    log_dir = settings.logging.resolved_dir()
    if log_dir.exists() and log_dir.is_dir():
        return {"status": "READY", "path": str(log_dir)}
    return {"status": "ERROR", "detail": f"log dir missing: {log_dir}"}


def _check_speech() -> dict:
    from app.speech import tts

    voices = [v.name for v in tts.list_voices()]
    if not tts.piper_binary_available():
        return {"status": "WARNING", "detail": "Piper binary not installed — see docs/speech.md", "voices": voices}
    if not voices:
        return {"status": "WARNING", "detail": "Piper installed but no voices — see docs/speech.md", "voices": voices}
    return {"status": "READY", "voices": voices}


def _check_vision() -> dict:
    from app.vision import ocr

    if not ocr.is_available():
        return {"status": "WARNING", "detail": "Tesseract OCR not found — see docs/vision.md"}
    return {"status": "READY"}


def _check_ollama() -> dict:
    settings = get_settings()
    try:
        resp = httpx.get(f"{settings.llm.ollama_host}/api/version", timeout=1.5)
        if resp.status_code == 200:
            return {"status": "READY", "version": resp.json().get("version")}
        return {"status": "WARNING", "detail": f"unexpected status {resp.status_code}"}
    except httpx.RequestError as exc:
        return {
            "status": "WARNING",
            "detail": f"Ollama not reachable at {settings.llm.ollama_host}: {exc}. "
            "Start it with 'ollama serve' — this is expected until Phase 2.",
        }


@router.get("")
def health() -> dict:
    settings = get_settings()
    checks = {
        "database": _check_database(),
        "logging": _check_log_dir(),
        "ollama": _check_ollama(),
        "speech": _check_speech(),
        "vision": _check_vision(),
    }

    statuses = [c["status"] for c in checks.values()]
    if "ERROR" in statuses:
        overall = "ERROR"
    elif "WARNING" in statuses:
        overall = "WARNING"
    else:
        overall = "READY"

    return {
        "status": overall,
        "app_name": settings.app_name,
        "version": settings.version,
        "phase": settings.phase,
        "timestamp": time.time(),
        "checks": checks,
    }
