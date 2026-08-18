"""Screenshot + active window / screen dimensions (spec section 16)."""

from __future__ import annotations

import io


class ScreenshotError(RuntimeError):
    pass


def capture_full_screen() -> bytes:
    try:
        from PIL import ImageGrab
    except Exception as exc:  # noqa: BLE001
        raise ScreenshotError(f"PIL.ImageGrab unavailable: {exc}") from exc

    img = ImageGrab.grab(all_screens=True)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def capture_region(left: int, top: int, right: int, bottom: int) -> bytes:
    try:
        from PIL import ImageGrab
    except Exception as exc:  # noqa: BLE001
        raise ScreenshotError(f"PIL.ImageGrab unavailable: {exc}") from exc

    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def capture_active_window() -> bytes:
    from app.computer import windows as windows_module

    all_windows = windows_module.list_windows()
    active = next((w for w in all_windows if w["is_active"]), None)
    if not active:
        raise ScreenshotError("No active window found")
    return capture_region(active["left"], active["top"], active["left"] + active["width"], active["top"] + active["height"])


def screen_dimensions() -> dict:
    try:
        from PIL import ImageGrab
    except Exception as exc:  # noqa: BLE001
        raise ScreenshotError(f"PIL.ImageGrab unavailable: {exc}") from exc

    img = ImageGrab.grab(all_screens=True)
    return {"width": img.width, "height": img.height}
