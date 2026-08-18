"""Audio I/O helpers shared by the speech API routes.

Microphone/speaker device selection happens in the browser via the Web
Audio API (navigator.mediaDevices) — the backend never touches hardware
directly, it only receives already-recorded audio bytes over HTTP. This
module just handles the temp-file plumbing faster-whisper needs (it reads
from a path, not raw bytes) and cleans up after itself.
"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def temp_audio_file(data: bytes, suffix: str = ".webm") -> Iterator[Path]:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = Path(f.name)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)
