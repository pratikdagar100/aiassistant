"""Local text-to-speech via the standalone Piper binary.

Uses the Piper CLI (models/piper/piper/piper.exe) via subprocess rather than
the `piper-tts` PyPI package — that package depends on `piper-phonemize`,
which has no published Windows wheel (confirmed during Phase 5 setup: pip
install fails on this platform). The binary is the officially distributed
Windows deployment method regardless. See docs/speech.md for voice install
instructions.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("speech.tts")


class TTSError(RuntimeError):
    pass


@dataclass
class Voice:
    name: str
    language: str | None
    onnx_path: Path
    config_path: Path


def piper_binary_available() -> bool:
    return get_settings().speech.resolved_piper_binary_path().exists()


def list_voices() -> list[Voice]:
    settings = get_settings()
    voices_dir = settings.speech.resolved_piper_voices_dir()
    if not voices_dir.exists():
        return []

    voices = []
    for onnx_file in voices_dir.glob("*.onnx"):
        config_file = onnx_file.with_suffix(".onnx.json")
        if not config_file.exists():
            continue
        language = None
        try:
            with config_file.open(encoding="utf-8") as f:
                meta = json.load(f)
            language = meta.get("language", {}).get("code")
        except Exception:  # noqa: BLE001
            pass
        voices.append(Voice(name=onnx_file.stem, language=language, onnx_path=onnx_file, config_path=config_file))
    return voices


def get_voice(name: str) -> Voice | None:
    return next((v for v in list_voices() if v.name == name), None)


def synthesize(text: str, voice_name: str | None = None) -> bytes:
    """Returns WAV audio bytes."""
    settings = get_settings()
    binary = settings.speech.resolved_piper_binary_path()
    if not binary.exists():
        raise TTSError(f"Piper binary not found at {binary}. See docs/speech.md to install it.")

    voice = get_voice(voice_name or settings.speech.default_voice)
    if not voice:
        available = [v.name for v in list_voices()]
        raise TTSError(
            f"Voice '{voice_name or settings.speech.default_voice}' not installed. "
            f"Available: {available or 'none — see docs/speech.md'}"
        )

    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "output.wav"
        try:
            proc = subprocess.run(
                [str(binary), "--model", str(voice.onnx_path), "--output_file", str(out_path), "--json-input"],
                input=json.dumps({"text": text}),
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(binary.parent),
            )
        except subprocess.TimeoutExpired as exc:
            raise TTSError("Piper synthesis timed out") from exc

        if proc.returncode != 0:
            raise TTSError(f"Piper failed ({proc.returncode}): {proc.stderr[-500:]}")

        if not out_path.exists():
            raise TTSError(f"Piper did not produce output: {proc.stderr[-500:]}")

        return out_path.read_bytes()
