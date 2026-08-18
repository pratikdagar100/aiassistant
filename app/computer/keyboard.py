"""Keyboard control (spec section 17)."""

from __future__ import annotations


class KeyboardError(RuntimeError):
    pass


def _pg():
    try:
        import pyautogui

        return pyautogui
    except Exception as exc:  # noqa: BLE001
        raise KeyboardError(f"pyautogui unavailable: {exc}") from exc


def type_text(text: str, interval: float = 0.02) -> dict:
    _pg().write(text, interval=interval)
    return {"typed_chars": len(text)}


def press(key: str) -> dict:
    _pg().press(key)
    return {"key": key}


def hotkey(*keys: str) -> dict:
    _pg().hotkey(*keys)
    return {"keys": list(keys)}
