"""Real-time talking-avatar generation via MuseTalk — NOT bundled.

This is the honest boundary of Phase 10: MuseTalk is a full diffusion-based
lip-sync pipeline (its own multi-GB checkpoint set, a pinned PyTorch/CUDA
version often in tension with the rest of this project's stack, and a face
-detection preprocessing step) — installing and validating it reliably
inside this session isn't something this project can respectably claim to
have done. Per the spec's own instruction for a subsystem an external model
blocks: implement the real interface, document setup, provide a fallback,
and say plainly what's missing. The fallback actually shipped is the
state-driven static avatar in the frontend (AvatarFace component) — the
face image plus idle/listening/thinking/speaking animation — which uses
the face_path and audio the rest of the system already produces.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import PROJECT_ROOT

MUSETALK_DIR = PROJECT_ROOT / "models" / "musetalk"


class MuseTalkError(RuntimeError):
    pass


def is_available() -> bool:
    """True only once a real MuseTalk checkoint set has been installed at
    models/musetalk/ — see docs/avatar.md. Always False out of the box."""
    return MUSETALK_DIR.exists() and any(MUSETALK_DIR.iterdir())


def generate_talking_frame(face_image_path: str, audio_chunk: bytes) -> bytes:
    """Would return one lip-synced video frame for the given audio chunk.
    Raises until a real MuseTalk installation is present — never returns a
    fake or placeholder frame."""
    if not is_available():
        raise MuseTalkError(
            "MuseTalk is not installed. PratikAI's avatar falls back to the "
            "state-driven static face (see frontend AvatarFace component). "
            "To enable real-time lip sync, follow docs/avatar.md."
        )
    raise MuseTalkError("MuseTalk integration point reached but no runtime is wired up yet — see docs/avatar.md.")
