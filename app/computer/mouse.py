"""Mouse control (spec section 17). Lazy pyautogui import so a missing
display/driver doesn't break app startup — see section 42 (one subsystem
failing must not crash the whole app)."""

from __future__ import annotations


class MouseError(RuntimeError):
    pass


def _pg():
    try:
        import pyautogui

        return pyautogui
    except Exception as exc:  # noqa: BLE001
        raise MouseError(f"pyautogui unavailable: {exc}") from exc


def move(x: int, y: int, duration: float = 0.2) -> dict:
    _pg().moveTo(x, y, duration=duration)
    return {"x": x, "y": y}


def click(x: int | None = None, y: int | None = None, button: str = "left") -> dict:
    _pg().click(x=x, y=y, button=button)
    return {"x": x, "y": y, "button": button}


def double_click(x: int | None = None, y: int | None = None) -> dict:
    _pg().doubleClick(x=x, y=y)
    return {"x": x, "y": y}


def right_click(x: int | None = None, y: int | None = None) -> dict:
    _pg().rightClick(x=x, y=y)
    return {"x": x, "y": y}


def drag(from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5) -> dict:
    pg = _pg()
    pg.moveTo(from_x, from_y)
    pg.dragTo(to_x, to_y, duration=duration)
    return {"from": [from_x, from_y], "to": [to_x, to_y]}


def scroll(clicks: int, x: int | None = None, y: int | None = None) -> dict:
    _pg().scroll(clicks, x=x, y=y)
    return {"clicks": clicks}


def position() -> dict:
    pos = _pg().position()
    return {"x": pos.x, "y": pos.y}
