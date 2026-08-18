"""Local OCR via Tesseract (spec section 16). Always CPU, always local —
no data leaves the machine for this."""

from __future__ import annotations

import io

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("vision.ocr")


class OCRError(RuntimeError):
    pass


def is_available() -> bool:
    return get_settings().vision.resolved_tesseract_path().exists()


def _configure():
    import pytesseract

    settings = get_settings()
    pytesseract.pytesseract.tesseract_cmd = str(settings.vision.resolved_tesseract_path())
    return pytesseract


def extract_text(image_bytes: bytes) -> str:
    if not is_available():
        raise OCRError("Tesseract not installed — see docs/vision.md")

    from PIL import Image

    pytesseract = _configure()
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img)


def extract_text_with_boxes(image_bytes: bytes) -> list[dict]:
    """Returns per-word bounding boxes — useful for click-by-text automation."""
    if not is_available():
        raise OCRError("Tesseract not installed — see docs/vision.md")

    from PIL import Image

    pytesseract = _configure()
    img = Image.open(io.BytesIO(image_bytes))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    results = []
    for i, text in enumerate(data["text"]):
        if text.strip():
            results.append(
                {
                    "text": text,
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "confidence": data["conf"][i],
                }
            )
    return results
