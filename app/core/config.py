"""Central configuration loader for PratikAI.

Precedence (highest wins): environment variables (PRATIKAI_*) > .env file >
config/settings.json > field defaults. Secrets (API keys, credentials) must
NEVER be placed in config/settings.json — they are only ever read from the
environment, per the project's privacy/security requirements.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_JSON_PATH = PROJECT_ROOT / "config" / "settings.json"


def _load_settings_json() -> dict[str, Any]:
    if not SETTINGS_JSON_PATH.exists():
        return {}
    with SETTINGS_JSON_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


class _SubSettings(BaseSettings):
    """Base for nested config sections: tolerate unknown keys in settings.json."""

    model_config = SettingsConfigDict(extra="ignore")


class BackendConfig(_SubSettings):
    host: str = "127.0.0.1"
    port: int = 8756


class FrontendConfig(_SubSettings):
    host: str = "127.0.0.1"
    port: int = 5173


class DatabaseConfig(_SubSettings):
    path: str = "data/database/pratikai.db"

    def resolved_path(self) -> Path:
        p = Path(self.path)
        return p if p.is_absolute() else PROJECT_ROOT / p


class LoggingConfig(_SubSettings):
    level: str = "INFO"
    dir: str = "data/logs"
    max_bytes: int = 5_242_880
    backup_count: int = 5

    def resolved_dir(self) -> Path:
        p = Path(self.dir)
        return p if p.is_absolute() else PROJECT_ROOT / p


class LLMConfig(_SubSettings):
    provider: str = "ollama"
    default_model: str = "qwen3:8b"
    ollama_host: str = "http://127.0.0.1:11434"


class GoogleCloudConfig(_SubSettings):
    stt_enabled: bool = False
    translation_enabled: bool = False


class MemoryConfig(_SubSettings):
    # Multilingual so semantic search works across the languages this
    # project targets (Hindi, Hinglish, Punjabi, ...), not just English.
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"  # keep off the GPU — the LLM needs that VRAM
    chroma_path: str = "data/embeddings/chroma"
    retrieval_top_k: int = 5

    def resolved_chroma_path(self) -> Path:
        p = Path(self.chroma_path)
        return p if p.is_absolute() else PROJECT_ROOT / p


class SpeechConfig(_SubSettings):
    # local | google | hybrid — see app/speech/stt.py. "local" never touches
    # the network; "google" requires PRATIKAI_GOOGLE_APPLICATION_CREDENTIALS.
    stt_mode: str = "local"
    whisper_model_size: str = "small"  # tiny|base|small|medium|large-v3 — small fits CPU well
    whisper_device: str = "cpu"  # keep off the GPU — the LLM needs that VRAM
    whisper_compute_type: str = "int8"
    low_confidence_threshold: float = 0.5  # below this, hybrid mode would fall back to Google (Phase 5b)

    piper_binary_path: str = "models/piper/piper/piper.exe"
    piper_voices_dir: str = "models/piper/voices"
    default_voice: str = "en_US-lessac-medium"

    def resolved_piper_binary_path(self) -> Path:
        p = Path(self.piper_binary_path)
        return p if p.is_absolute() else PROJECT_ROOT / p

    def resolved_piper_voices_dir(self) -> Path:
        p = Path(self.piper_voices_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p


class VisionConfig(_SubSettings):
    tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    vision_model: str = "moondream"  # small (~1.7GB) Ollama-compatible vision model; not pulled by default

    def resolved_tesseract_path(self) -> Path:
        p = Path(self.tesseract_path)
        return p if p.is_absolute() else PROJECT_ROOT / p


class StartupConfig(_SubSettings):
    enabled: bool = False
    auto_select_entity: bool = True
    auto_mic: bool = False
    wake_word: bool = False
    auto_avatar: bool = False


class Settings(BaseSettings):
    """Application settings, merged from config/settings.json and env vars.

    Env vars use the PRATIKAI_ prefix with double-underscore nesting, e.g.
    PRATIKAI_LLM__OLLAMA_HOST=http://127.0.0.1:11434
    PRATIKAI_GOOGLE_APPLICATION_CREDENTIALS=C:\\path\\to\\creds.json
    """

    model_config = SettingsConfigDict(
        env_prefix="PRATIKAI_",
        env_nested_delimiter="__",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PratikAI"
    version: str = "0.1.0"
    phase: int = 1

    backend: BackendConfig = Field(default_factory=BackendConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    speech: SpeechConfig = Field(default_factory=SpeechConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    google_cloud: GoogleCloudConfig = Field(default_factory=GoogleCloudConfig)
    startup: StartupConfig = Field(default_factory=StartupConfig)

    default_entity: str = "friday"

    # Secrets — env-only, never read from settings.json.
    google_application_credentials: str | None = None


@lru_cache
def get_settings() -> Settings:
    raw = _load_settings_json()
    return Settings(**raw)
