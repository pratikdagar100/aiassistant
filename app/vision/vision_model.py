"""Local vision-language model Q&A via Ollama's multimodal chat API (spec
section 16: "local vision model"). Not pulled by default — moondream is
~1.7GB and, per the VRAM-budget principle used throughout this project
(Phase 4 embeddings, Phase 5 Whisper), loading it alongside the 8B LLM on a
12GB card needs to be an explicit choice, made from the Models page, not
something that happens silently on first use.
"""

from __future__ import annotations

import base64

from app.core.config import get_settings
from app.llm.ollama import OllamaClient, OllamaError


class VisionModelError(RuntimeError):
    pass


async def describe_image(image_bytes: bytes, question: str = "Describe what's on the screen.", model: str | None = None) -> str:
    settings = get_settings()
    model_name = model or settings.vision.vision_model

    client = OllamaClient()
    if not await client.is_available():
        raise VisionModelError("Ollama is not reachable")

    encoded = base64.b64encode(image_bytes).decode("ascii")
    try:
        result = await client.chat(
            model=model_name,
            messages=[{"role": "user", "content": question, "images": [encoded]}],
        )
    except OllamaError as exc:
        raise VisionModelError(
            f"{exc}. If the model isn't installed, pull it from the Models page (ollama pull {model_name})."
        ) from exc

    return result.get("message", {}).get("content", "")
