# Computer Use

## Architecture

```
app/computer/registry.py        tool name -> callable (single source of truth)
app/security/command_policy.py  tool name -> permission category + risk level
app/security/permissions.py     per-entity category -> disabled|enabled|confirmation
app/security/approval.py        the gateway every call goes through
app/security/audit.py           every call logged, whatever the outcome
```

Every computer-tool call — whether from a direct API request
(`/api/computer/execute`) or from an autonomous task
(`app/core/executor.py`) — goes through the exact same gateway. There is no
separate code path that skips the permission check.

## Tool modules

- `filesystem.py` — list/search/read/write/copy/move/rename/archive/delete/compare/metadata
- `terminal.py` — PowerShell/CMD/Python, always returns `{stdout, stderr, returncode, success}`
- `mouse.py` / `keyboard.py` / `clipboard.py` — pyautogui/pyperclip
- `windows.py` — pygetwindow (list/focus/minimize/maximize/resize/close)
- `applications.py` — generic launch (path -> PATH -> `os.startfile`) + process management, not hardcoded to specific apps
- `uia.py` — Windows UI Automation via pywinauto (inspect tree, invoke, set/read text)
- `browser.py` — Playwright/Chromium (navigate, search, click, type, scroll, read page text)

## Priority order (spec section 26)

The planner (`app/core/planner.py`) picks whichever tool the LLM judges
best for the task from the full registry — there's no hardcoded preference
ordering enforced in code beyond what's implied by each tool's description
in the catalog the planner sees.

## Confirmation flow

`POST /api/computer/execute` returns either `{status: "success", result}`
immediately, or `{status: "pending_approval", audit_id}` — the action has
**not** run yet. `POST /api/computer/approve/{audit_id}` runs it;
`POST /api/computer/deny/{audit_id}` marks it denied and it never runs.
Verified live and in `tests/test_computer_api.py` (the target file is
checked to genuinely not exist before approval).
