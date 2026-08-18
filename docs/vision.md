# Vision

## Installed and working

- **Screenshot**: `app/vision/screenshot.py` via `PIL.ImageGrab` — full
  screen, a region, or the active window (cross-referenced with
  `app/computer/windows.py`).
- **OCR**: Tesseract 5.5.3, installed via
  `winget install --id tesseract-ocr.tesseract -e` at
  `C:\Program Files\Tesseract-OCR\tesseract.exe`. `app/vision/ocr.py` wraps
  it with `pytesseract`. Verified live: renders text into an image and
  confirms OCR reads it back correctly (`tests/test_vision.py`).
- **UI element detection**: covered by Windows UI Automation
  (`app/computer/uia.py`, Phase 7), not a separate vision-based detector —
  structured control trees are more reliable than pixel detection wherever
  the target is a native Windows app.

## Optional: local vision-language model

`app/vision/vision_model.py` calls Ollama's multimodal chat API (works with
any vision-capable model Ollama supports, e.g. `moondream`, ~1.7GB). **Not
pulled by default** — install explicitly if you want screen Q&A:

```powershell
ollama pull moondream
```

Then `POST /api/vision/describe {"question": "What's open right now?"}`.
This follows the same VRAM-budget principle as Whisper/embeddings: nothing
that adds meaningful VRAM pressure loads without an explicit decision.

## API

`GET /api/vision/screenshot` (PNG), `/dimensions`, `/ocr`,
`POST /describe`, `/status`.
