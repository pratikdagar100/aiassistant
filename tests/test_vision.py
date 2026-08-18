"""Uses the real screen and the real Tesseract binary — no mocking."""

from app.vision import ocr, screenshot


def test_capture_full_screen_returns_valid_png():
    png = screenshot.capture_full_screen()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000


def test_screen_dimensions_are_positive():
    dims = screenshot.screen_dimensions()
    assert dims["width"] > 0
    assert dims["height"] > 0


def test_ocr_available():
    assert ocr.is_available(), "Tesseract not found — see docs/vision.md"


def test_ocr_reads_rendered_text():
    from PIL import Image, ImageDraw
    import io

    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "PRATIKAI TEST", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    text = ocr.extract_text(buf.getvalue())
    assert "PRATIKAI" in text.upper()
