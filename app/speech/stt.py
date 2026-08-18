"""Local speech-to-text via faster-whisper, with automatic language detection
built in (spec section 6/7: never require the user to pick a language first).

Runs on CPU by default (see app.core.config.SpeechConfig) so it never
contends with the LLM for the RTX 3060's VRAM — same reasoning as the
embedding model in app/memory/embeddings.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("speech.stt")


@dataclass
class TranscriptionResult:
    text: str
    language: str
    language_confidence: float
    engine: str = "whisper"
    segments: list[dict] = field(default_factory=list)


@lru_cache
def _get_model():
    from faster_whisper import WhisperModel

    settings = get_settings()
    logger.info(
        "Loading faster-whisper model '%s' on %s (%s) — first call only",
        settings.speech.whisper_model_size,
        settings.speech.whisper_device,
        settings.speech.whisper_compute_type,
    )
    return WhisperModel(
        settings.speech.whisper_model_size,
        device=settings.speech.whisper_device,
        compute_type=settings.speech.whisper_compute_type,
    )


def is_available() -> bool:
    try:
        _get_model()
        return True
    except Exception:  # noqa: BLE001
        logger.warning("Whisper model unavailable", exc_info=True)
        return False


def transcribe(audio_path: str | Path) -> TranscriptionResult:
    model = _get_model()
    segments_iter, info = model.transcribe(str(audio_path), beam_size=5)
    segments = []
    text_parts = []
    for seg in segments_iter:
        segments.append({"start": seg.start, "end": seg.end, "text": seg.text})
        text_parts.append(seg.text)

    return TranscriptionResult(
        text="".join(text_parts).strip(),
        language=info.language,
        language_confidence=info.language_probability,
        engine="whisper",
        segments=segments,
    )
