"""Speech API: transcribe (STT + language detection) and synthesize (TTS)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.logging import get_logger
from app.speech import stt, tts
from app.speech.audio import temp_audio_file
from app.speech.language import display_name

router = APIRouter()
logger = get_logger("api.speech")


class SynthesizeRequest(BaseModel):
    text: str
    voice: str | None = None


@router.post("/transcribe")
async def transcribe(file: UploadFile) -> dict:
    if not stt.is_available():
        raise HTTPException(503, "Whisper model unavailable — check the server logs.")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty audio upload")

    suffix = "." + (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "webm")
    with temp_audio_file(data, suffix=suffix) as path:
        try:
            result = stt.transcribe(path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Transcription failed", exc_info=True)
            raise HTTPException(500, f"Transcription failed: {exc}") from exc

    return {
        "text": result.text,
        "language": result.language,
        "language_name": display_name(result.language),
        "language_confidence": result.language_confidence,
        "engine": result.engine,
    }


@router.post("/synthesize")
def synthesize(req: SynthesizeRequest) -> Response:
    try:
        audio = tts.synthesize(req.text, voice_name=req.voice)
    except tts.TTSError as exc:
        raise HTTPException(503, str(exc)) from exc
    return Response(content=audio, media_type="audio/wav")


@router.get("/voices")
def list_voices() -> list[dict]:
    return [{"name": v.name, "language": v.language} for v in tts.list_voices()]


@router.get("/status")
def speech_status() -> dict:
    return {
        "stt_available": stt.is_available(),
        "tts_available": tts.piper_binary_available(),
        "voices_installed": [v.name for v in tts.list_voices()],
    }
