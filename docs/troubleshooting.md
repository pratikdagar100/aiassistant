# Troubleshooting

Run `scripts\health_check.ps1` first — it checks Python venv, Node, Ollama
CLI, and (via `/api/health`) database/logging/Ollama-connectivity/speech/
vision, printing READY/WARNING/ERROR for each.

## Backend won't start

- `venv not found` — run `scripts\setup.ps1`.
- Check `data\logs\backend.err.log` for the actual traceback (this file is
  populated by uvicorn's own error logger — see `app/main.py`; don't
  disable `log_config` there or tracebacks go silent, a real bug this
  project hit and fixed during Phase 2).

## Ollama not reachable

`/api/health` reports it under `checks.ollama`. Start it with
`ollama serve`, or check it's running as a service (`ollama --version`
should succeed; `http://127.0.0.1:11434/api/version` should respond).

## Chat returns 503

Ollama isn't reachable, or the entity's `model` isn't pulled yet —
check the Models page, or `ollama pull qwen3:8b` /
`scripts\install_models.ps1`.

## GPU / VRAM contention

Qwen3 8B needs ~6-8GB VRAM. Whisper, the embedding model, and (if you
enable it) OCR/vision-model calls all default to CPU specifically to avoid
competing for it — see `app/core/config.py`'s `SpeechConfig`/`MemoryConfig`
device settings. If VRAM runs low, check `nvidia-smi` for what else is
using the GPU (this project's own dev history: a crypto miner was found
occupying 8GB of the 12GB card before Phase 1 even started — close anything
unexpected first).

## Frontend can't reach the backend

`vite.config.ts` proxies `/api` to `http://127.0.0.1:8756` — if you changed
`backend.port` in `config/settings.json`, update the proxy target too.

## Windows startup task isn't running

`schtasks /query /tn PratikAI` — if missing, run
`scripts\register_startup.ps1`. Check Task Scheduler Library
(`taskschd.msc`) for its last run result if it's registered but nothing
started.

## Tests failing intermittently around the SQLite test database

Fixed in Phase 1 (`tests/conftest.py` now drops+recreates schema at session
start, not just deletes the file at teardown) — if you see
`UNIQUE constraint failed` on a fresh test run, check that fix wasn't
reverted.
