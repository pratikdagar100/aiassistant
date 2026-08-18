# Startup

## Enable / disable

```powershell
scripts\register_startup.ps1     # PratikAI starts at your next login
scripts\unregister_startup.ps1   # undo
```

Uses a Windows **Task Scheduler** entry (`Register-ScheduledTask`,
`-Trigger AtLogOn`, `-RunLevel Limited` — no admin elevation), visible in
`taskschd.msc` under Task Scheduler Library. This is intentional: the spec
requires startup be transparent and user-controllable, never a hidden
registry Run key. Verified live during Phase 13 — registered, confirmed via
`schtasks /query`, then unregistered again (this project defaults to
startup **disabled** until you explicitly opt in).

## What it runs

The scheduled task runs `scripts\start.ps1`, which starts the backend and
frontend (and Ollama, if not already running) and then runs a health check.

## Settings page

`GET/PATCH /api/settings` — `auto_select_entity`, `auto_mic`, `auto_avatar`
are stored in the `settings` table and reflected on the Settings page.
`wake_word` is present as a setting but has no implementation behind it yet
(the UI says so explicitly rather than silently no-op'ing).

`startup_task_registered` on that same endpoint reflects the live
`schtasks` state — it's not a stored flag that can drift from reality.
