"""Windows UI Automation via pywinauto (spec section 18) — structured
control interaction preferred over raw mouse/keyboard coordinates wherever
possible (spec section 26: prefer the fastest/most reliable method).
"""

from __future__ import annotations

from typing import Any


class UIAError(RuntimeError):
    pass


def _connect(title: str):
    try:
        from pywinauto import Application
    except Exception as exc:  # noqa: BLE001
        raise UIAError(f"pywinauto unavailable: {exc}") from exc

    try:
        app = Application(backend="uia").connect(title_re=f".*{title}.*")
        return app.top_window()
    except Exception as exc:  # noqa: BLE001
        raise UIAError(f"Could not connect to a window matching '{title}': {exc}") from exc


def inspect_tree(title: str, max_depth: int = 4) -> list[dict]:
    """Returns a flattened control tree: type, name, automation_id, depth."""
    window = _connect(title)
    results: list[dict] = []

    def walk(element, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            info = element.element_info
            results.append(
                {
                    "control_type": info.control_type,
                    "name": info.name,
                    "automation_id": info.automation_id,
                    "depth": depth,
                    "enabled": element.is_enabled() if hasattr(element, "is_enabled") else None,
                }
            )
        except Exception:  # noqa: BLE001
            return
        for child in element.children():
            walk(child, depth + 1)

    walk(window, 0)
    return results


def find_control(title: str, *, name: str | None = None, control_type: str | None = None, automation_id: str | None = None):
    window = _connect(title)
    kwargs: dict[str, Any] = {}
    if name:
        kwargs["title"] = name
    if control_type:
        kwargs["control_type"] = control_type
    if automation_id:
        kwargs["auto_id"] = automation_id
    try:
        return window.child_window(**kwargs).wrapper_object()
    except Exception as exc:  # noqa: BLE001
        raise UIAError(f"Control not found ({kwargs}): {exc}") from exc


def invoke(title: str, *, name: str | None = None, control_type: str | None = None, automation_id: str | None = None) -> dict:
    control = find_control(title, name=name, control_type=control_type, automation_id=automation_id)
    control.invoke() if hasattr(control, "invoke") else control.click_input()
    return {"invoked": name or automation_id}


def set_text(title: str, *, name: str | None = None, automation_id: str | None = None, text: str = "") -> dict:
    control = find_control(title, name=name, control_type="Edit", automation_id=automation_id)
    control.set_edit_text(text)
    return {"name": name or automation_id, "text": text}


def read_text(title: str, *, name: str | None = None, automation_id: str | None = None) -> dict:
    control = find_control(title, name=name, automation_id=automation_id)
    try:
        text = control.window_text()
    except Exception as exc:  # noqa: BLE001
        raise UIAError(f"Could not read text: {exc}") from exc
    return {"text": text}
