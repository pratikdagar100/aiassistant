# Security & Permissions

## Model

`app/security/permissions.py` — 15 categories (SCREEN, MOUSE, KEYBOARD,
CLIPBOARD, APPLICATIONS, FILESYSTEM_READ/WRITE/DELETE, TERMINAL, POWERSHELL,
PYTHON, BROWSER, NETWORK, SYSTEM, ADMINISTRATOR), each set per entity to
`disabled` / `enabled` / `confirmation`. Defaults
(`DEFAULT_PERMISSIONS`) are safe: reads are enabled, writes/deletes/terminal
require confirmation, **ADMINISTRATOR is always disabled and cannot be
changed from the UI** (`frontend/src/pages/Permissions.tsx` disables that
row's dropdown; the backend has no code path that sets it to anything else
either).

An entity's `computer_access` flag is a hard override: if it's `False`,
every category resolves to `disabled` regardless of the stored permission
map (`app/security/permissions.py::get_mode`).

## Enforcement point

`app/security/approval.py::request_execution` is the single gateway.
`app/api/routes/computer.py` and `app/core/executor.py` (autonomous tasks)
both call it — there's no separate path that bypasses it.

## Confirmation UX

Pending approvals show the action, parameters, and risk level
(Computer Control and Tasks pages) with Approve/Deny buttons. Verified live
and in tests that a `confirmation`-gated file write does not create the
file until approved, and never runs at all if denied.

## What's explicitly not done

- No UAC bypass, no hidden persistence (Windows startup uses a visible
  Task Scheduler entry — see docs/startup.md), no credential capture, no
  keylogging.
- Google STT/Translation credentials, if configured, are read only from
  environment variables (`PRATIKAI_GOOGLE_APPLICATION_CREDENTIALS`) —
  never from `config/settings.json`, never committed (see `.gitignore`).
