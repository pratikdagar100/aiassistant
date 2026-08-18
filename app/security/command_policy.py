"""Maps a computer-tool call to a permission category and risk level.

This is the one place that decides "what kind of thing is this action" —
app/security/approval.py then decides "is it allowed to run right now" by
combining this with the entity's permissions (app/security/permissions.py).
Keeping the mapping centralized means a new tool can't accidentally skip
the policy check just because a route forgot to declare one.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.security.permissions import PermissionCategory


@dataclass(frozen=True)
class ToolPolicy:
    category: str
    risk: str  # low | medium | high
    reason: str


TOOL_POLICIES: dict[str, ToolPolicy] = {
    # Filesystem — reads are low risk, writes medium, deletes high.
    "filesystem.list_directory": ToolPolicy(PermissionCategory.FILESYSTEM_READ, "low", "List directory contents"),
    "filesystem.read_file": ToolPolicy(PermissionCategory.FILESYSTEM_READ, "low", "Read a file"),
    "filesystem.metadata": ToolPolicy(PermissionCategory.FILESYSTEM_READ, "low", "Inspect file metadata"),
    "filesystem.search": ToolPolicy(PermissionCategory.FILESYSTEM_READ, "low", "Search files"),
    "filesystem.compare": ToolPolicy(PermissionCategory.FILESYSTEM_READ, "low", "Compare two files"),
    "filesystem.write_file": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Write to a file"),
    "filesystem.create_file": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Create a file"),
    "filesystem.create_folder": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Create a folder"),
    "filesystem.copy": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Copy a file or folder"),
    "filesystem.move": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Move a file or folder"),
    "filesystem.rename": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Rename a file or folder"),
    "filesystem.archive": ToolPolicy(PermissionCategory.FILESYSTEM_WRITE, "medium", "Archive files into a zip"),
    "filesystem.delete": ToolPolicy(PermissionCategory.FILESYSTEM_DELETE, "high", "Delete a file or folder"),
    # Terminal
    "terminal.run_powershell": ToolPolicy(PermissionCategory.POWERSHELL, "high", "Run a PowerShell command"),
    "terminal.run_cmd": ToolPolicy(PermissionCategory.TERMINAL, "high", "Run a CMD command"),
    "terminal.run_python": ToolPolicy(PermissionCategory.PYTHON, "high", "Run a Python script"),
    # Mouse / keyboard / clipboard
    "mouse.move": ToolPolicy(PermissionCategory.MOUSE, "low", "Move the mouse"),
    "mouse.click": ToolPolicy(PermissionCategory.MOUSE, "medium", "Click the mouse"),
    "mouse.double_click": ToolPolicy(PermissionCategory.MOUSE, "medium", "Double-click the mouse"),
    "mouse.right_click": ToolPolicy(PermissionCategory.MOUSE, "medium", "Right-click the mouse"),
    "mouse.drag": ToolPolicy(PermissionCategory.MOUSE, "medium", "Drag the mouse"),
    "mouse.scroll": ToolPolicy(PermissionCategory.MOUSE, "low", "Scroll the mouse wheel"),
    "keyboard.type": ToolPolicy(PermissionCategory.KEYBOARD, "medium", "Type text"),
    "keyboard.press": ToolPolicy(PermissionCategory.KEYBOARD, "medium", "Press a key"),
    "keyboard.hotkey": ToolPolicy(PermissionCategory.KEYBOARD, "medium", "Press a key combination"),
    "clipboard.read": ToolPolicy(PermissionCategory.CLIPBOARD, "low", "Read the clipboard"),
    "clipboard.write": ToolPolicy(PermissionCategory.CLIPBOARD, "low", "Write to the clipboard"),
    # Windows
    "windows.list": ToolPolicy(PermissionCategory.SCREEN, "low", "List open windows"),
    "windows.focus": ToolPolicy(PermissionCategory.APPLICATIONS, "low", "Focus a window"),
    "windows.minimize": ToolPolicy(PermissionCategory.APPLICATIONS, "low", "Minimize a window"),
    "windows.maximize": ToolPolicy(PermissionCategory.APPLICATIONS, "low", "Maximize a window"),
    "windows.resize": ToolPolicy(PermissionCategory.APPLICATIONS, "low", "Resize a window"),
    "windows.close": ToolPolicy(PermissionCategory.APPLICATIONS, "medium", "Close a window"),
    # Applications
    "applications.launch": ToolPolicy(PermissionCategory.APPLICATIONS, "medium", "Launch an application"),
    "applications.close": ToolPolicy(PermissionCategory.APPLICATIONS, "medium", "Close an application"),
    # Screen / vision
    "vision.screenshot": ToolPolicy(PermissionCategory.SCREEN, "low", "Take a screenshot"),
    "vision.screen_dimensions": ToolPolicy(PermissionCategory.SCREEN, "low", "Get screen dimensions"),
    "vision.ocr": ToolPolicy(PermissionCategory.SCREEN, "low", "Read on-screen text via OCR"),
    # Windows UI Automation
    "uia.inspect_tree": ToolPolicy(PermissionCategory.SCREEN, "low", "Inspect a window's UI control tree"),
    "uia.invoke": ToolPolicy(PermissionCategory.APPLICATIONS, "medium", "Invoke a UI control (e.g. click a button)"),
    "uia.set_text": ToolPolicy(PermissionCategory.APPLICATIONS, "medium", "Set text in a UI control"),
    "uia.read_text": ToolPolicy(PermissionCategory.SCREEN, "low", "Read text from a UI control"),
    # Browser
    "browser.navigate": ToolPolicy(PermissionCategory.BROWSER, "medium", "Navigate the browser to a URL"),
    "browser.search": ToolPolicy(PermissionCategory.BROWSER, "medium", "Perform a web search"),
    "browser.read_page_text": ToolPolicy(PermissionCategory.BROWSER, "low", "Read the current page's text"),
    "browser.click": ToolPolicy(PermissionCategory.BROWSER, "medium", "Click an element on the page"),
    "browser.type": ToolPolicy(PermissionCategory.BROWSER, "medium", "Type into a page element"),
    "browser.scroll": ToolPolicy(PermissionCategory.BROWSER, "low", "Scroll the page"),
    "browser.page_state": ToolPolicy(PermissionCategory.BROWSER, "low", "Get the current page URL/title"),
    "browser.close": ToolPolicy(PermissionCategory.BROWSER, "low", "Close the browser session"),
}


def get_policy(tool: str) -> ToolPolicy:
    policy = TOOL_POLICIES.get(tool)
    if not policy:
        # Unknown tools default to the strictest posture — a typo in a tool
        # name must never accidentally grant looser permissions than intended.
        return ToolPolicy(PermissionCategory.ADMINISTRATOR, "high", f"Unrecognized tool '{tool}'")
    return policy
