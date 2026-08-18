"""Clipboard access (spec section 17)."""

from __future__ import annotations


class ClipboardError(RuntimeError):
    pass


def read() -> str:
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"Clipboard read failed: {exc}") from exc


def write(text: str) -> dict:
    try:
        import pyperclip

        pyperclip.copy(text)
        return {"written_chars": len(text)}
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"Clipboard write failed: {exc}") from exc
