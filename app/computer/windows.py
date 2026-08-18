"""Window management (spec section 17/18) via pygetwindow. Prefer this
mechanical layer over screen-coordinate clicking wherever it's sufficient —
UI Automation (Phase 7) goes further for reading/invoking specific controls.
"""

from __future__ import annotations


class WindowError(RuntimeError):
    pass


def _gw():
    try:
        import pygetwindow

        return pygetwindow
    except Exception as exc:  # noqa: BLE001
        raise WindowError(f"pygetwindow unavailable: {exc}") from exc


def list_windows() -> list[dict]:
    gw = _gw()
    windows = []
    for w in gw.getAllWindows():
        if not w.title:
            continue
        windows.append(
            {
                "title": w.title,
                "left": w.left,
                "top": w.top,
                "width": w.width,
                "height": w.height,
                "is_active": w.isActive,
                "is_minimized": w.isMinimized,
                "is_maximized": w.isMaximized,
            }
        )
    return windows


def _find(title: str):
    gw = _gw()
    matches = gw.getWindowsWithTitle(title)
    if not matches:
        raise WindowError(f"No window found with title containing '{title}'")
    return matches[0]


def focus(title: str) -> dict:
    win = _find(title)
    win.activate()
    return {"title": win.title, "focused": True}


def minimize(title: str) -> dict:
    win = _find(title)
    win.minimize()
    return {"title": win.title, "minimized": True}


def maximize(title: str) -> dict:
    win = _find(title)
    win.maximize()
    return {"title": win.title, "maximized": True}


def resize(title: str, width: int, height: int) -> dict:
    win = _find(title)
    win.resizeTo(width, height)
    return {"title": win.title, "width": width, "height": height}


def close(title: str) -> dict:
    win = _find(title)
    win.close()
    return {"title": win.title, "closed": True}
