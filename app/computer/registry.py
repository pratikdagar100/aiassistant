"""Tool name -> callable dispatch table. The single source of truth for
"what can be invoked by name" — used by the /api/computer/execute endpoint
now, and by the Phase 8 agent planner later, so both go through the exact
same set of tools with no separate hardcoded path.
"""

from __future__ import annotations

from typing import Callable

from app.computer import applications, browser, clipboard, filesystem, keyboard, mouse, terminal, uia, windows
from app.vision import ocr, screenshot

TOOL_REGISTRY: dict[str, Callable[..., object]] = {
    "filesystem.list_directory": filesystem.list_directory,
    "filesystem.search": filesystem.search,
    "filesystem.read_file": filesystem.read_file,
    "filesystem.write_file": filesystem.write_file,
    "filesystem.create_folder": filesystem.create_folder,
    "filesystem.create_file": filesystem.create_file,
    "filesystem.copy": filesystem.copy,
    "filesystem.move": filesystem.move,
    "filesystem.rename": filesystem.rename,
    "filesystem.archive": filesystem.archive,
    "filesystem.delete": filesystem.delete,
    "filesystem.compare": filesystem.compare,
    "filesystem.metadata": filesystem.metadata,
    "terminal.run_powershell": lambda **kw: terminal.run_powershell(**kw).to_dict(),
    "terminal.run_cmd": lambda **kw: terminal.run_cmd(**kw).to_dict(),
    "terminal.run_python": lambda **kw: terminal.run_python(**kw).to_dict(),
    "mouse.move": mouse.move,
    "mouse.click": mouse.click,
    "mouse.double_click": mouse.double_click,
    "mouse.right_click": mouse.right_click,
    "mouse.drag": mouse.drag,
    "mouse.scroll": mouse.scroll,
    "keyboard.type": keyboard.type_text,
    "keyboard.press": keyboard.press,
    "keyboard.hotkey": lambda keys: keyboard.hotkey(*keys),
    "clipboard.read": lambda: clipboard.read(),
    "clipboard.write": clipboard.write,
    "windows.list": lambda: windows.list_windows(),
    "windows.focus": windows.focus,
    "windows.minimize": windows.minimize,
    "windows.maximize": windows.maximize,
    "windows.resize": windows.resize,
    "windows.close": windows.close,
    "applications.launch": applications.launch,
    "applications.close": lambda process_name: applications.close_by_process_name(process_name),
    "uia.inspect_tree": uia.inspect_tree,
    "uia.invoke": uia.invoke,
    "uia.set_text": uia.set_text,
    "uia.read_text": uia.read_text,
    "browser.navigate": browser.navigate,
    "browser.search": browser.search,
    "browser.read_page_text": lambda: browser.read_page_text(),
    "browser.click": browser.click,
    "browser.type": browser.type_text,
    "browser.scroll": browser.scroll,
    "browser.page_state": lambda: browser.page_state(),
    "browser.close": lambda: browser.close_browser(),
    "vision.screenshot": lambda: screenshot.capture_full_screen().hex(),
    "vision.screen_dimensions": lambda: screenshot.screen_dimensions(),
    "vision.ocr": lambda: ocr.extract_text(screenshot.capture_full_screen()),
}


def get_tool(name: str) -> Callable[..., object]:
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        raise KeyError(f"Unknown tool '{name}'")
    return tool
