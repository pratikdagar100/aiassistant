# PratikAI

A local personal AI platform: multiple independent AI entities, each with
their own memory, personality, voice, and face, running on your own
hardware via a local LLM (Qwen3 8B through Ollama by default).

This is being built in phases (see **Roadmap** below). This README always
reflects what is actually implemented and working right now — not the full
end-state vision.

## Status: Phases 1-13 complete

All 13 build phases are implemented and verified live against the real
running stack (not just unit tests) — see the roadmap table below for the
phase-by-phase breakdown, and each `docs/*.md` file for what's genuinely
done vs. honestly documented as not-yet-built (avatar lip sync, LoRA
execution, Google STT). Phase 14 (final polish/optimization/packaging) is
the remaining work.

What exists and is verified working, end to end, against the real running stack:

- FastAPI backend (`app/`) with structured config, logging, and a real
  `/api/health` endpoint that checks the database, log directory, and
  Ollama connectivity.
- SQLite database (14-table schema) managed with Alembic migrations, plus
  a ChromaDB vector store (`data/embeddings/chroma/`) for semantic memory.
- Real chat against Qwen3 8B via Ollama — both request/response
  (`POST /api/chat`) and token-streaming (`WS /api/chat/ws`) — with
  multi-turn history and cross-conversation memory recall confirmed live.
- Entity Manager: create/edit/delete/duplicate/export/import, personality
  presets, a 6-step creation wizard in the UI, and verified memory isolation
  between entities (one entity's memories are never visible to another).
- Memory system: every user message is screened by the LLM itself for
  anything worth remembering long-term (preferences, facts, explicit
  "remember this" instructions); relevant memories are retrieved by semantic
  search (multilingual embedding model) and injected into context — not the
  full conversation history. Full CRUD + pin/search/clear from the Memory page.
- Knowledge base: upload PDF/DOCX/TXT/MD/code, chunked + embedded +
  retrieved during chat the same way memories are — confirmed live (asked
  about a fact only present in an uploaded doc, got the right answer).
- Speech: local faster-whisper STT with automatic language detection, local
  Piper TTS, mic recording + voice-reply playback in the Chat page —
  verified with a real synthesize -> transcribe round trip.
- Computer control: filesystem/terminal/mouse/keyboard/clipboard/windows/
  application-launch/Windows UI Automation/browser (Playwright) tools, all
  gated by a per-entity permission system (disabled/enabled/confirmation)
  and an audit log. Confirmed live: a confirmation-gated file write does
  not create the file until approved, never runs at all if denied.
- Agent planner: natural-language task -> LLM-generated step plan ->
  execute through the same permission gateway -> observe/verify -> pause
  for approval or fail explicitly (no silent retries) -> optional replan.
  Verified live with a real multi-step task through Friday.
- Vision: screenshot, screen dimensions, OCR (Tesseract) — all real,
  no mocked capture.
- Avatar: face upload/storage + a state-driven UI (idle/listening/thinking/
  speaking) reflecting real mic/streaming state. Full MuseTalk lip sync is
  honestly documented as not installed (see docs/avatar.md).
- Continuous learning: LLM-detected corrections/preferences staged in a
  review queue; approved examples export to a training-dataset JSONL.
  LoRA/QLoRA training has a real, correct interface with a working
  dry-run — actually running it needs an explicit, separate opt-in
  (`scripts\train_lora.ps1`) since it involves a multi-GB download (see
  docs/learning.md).
- Model Manager: list/pull/select-default/test, VRAM-estimate aware.
- React + TypeScript + Tailwind frontend (`frontend/`) — every page in the
  spec (Dashboard, Live Chat, Entities, Memory, Knowledge, Computer
  Control, Tasks, Learning, Training, Models, Permissions, Audit,
  Settings) is live and backed by real data, production build verified
  (`npm run build`).
- Operational scripts (`scripts/`) to set up, start, stop, restart, health
  check, pull models, and register/unregister Windows startup — the
  startup registration was verified live (registered, confirmed via
  `schtasks`, then unregistered to leave it opt-in as designed).
- 125 automated tests (`tests/`), the large majority against real local
  models (Ollama/Whisper/Piper/Tesseract/embeddings) and a real browser/
  UI-automation session — no mocked LLM, STT, TTS, OCR, or vector-search
  calls anywhere in the suite.

Honestly not done: Google STT/Translation (interface shaped for it, no
working code path — see docs/multilingual.md), MuseTalk real-time lip sync
(see docs/avatar.md), actually executing a LoRA training run (see
docs/learning.md), a compiled/packaged installer beyond the PowerShell
scripts.

## Prerequisites

- Windows 10/11
- NVIDIA GPU with ~12GB VRAM (RTX 3060 or similar) — CPU fallback works but
  is much slower once the LLM phase lands
- Git

`scripts/setup.ps1` installs everything else (Python 3.11, Node.js LTS,
Ollama) it doesn't find, or tells you exactly what to install by hand.

## Install

```powershell
git clone <this-repo> PratikAI
cd PratikAI
scripts\setup.ps1
```

This creates the Python 3.11 virtual environment, installs backend and
frontend dependencies, and applies database migrations. It does **not**
download any LLM weights — that's a separate, explicit step because it's a
multi-gigabyte download:

```powershell
scripts\install_models.ps1        # pulls qwen3:8b via Ollama
```

## Run

```powershell
scripts\start.ps1                 # starts backend (127.0.0.1:8756) + frontend (127.0.0.1:5173)
scripts\health_check.ps1          # prints READY/WARNING/ERROR for every component
scripts\stop.ps1
scripts\restart.ps1
```

Open http://127.0.0.1:5173 for the dashboard.

## Windows startup

PratikAI does not start automatically until you opt in. This uses a
visible Task Scheduler entry (Task Scheduler Library), never a hidden
registry run key — you can inspect or remove it at any time.

```powershell
scripts\register_startup.ps1      # PratikAI starts at your next login
scripts\unregister_startup.ps1    # undo
```

## Tests

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

## Configuration

Non-secret settings live in `config/settings.json`. Secrets (API keys,
service account credentials) are never stored there — set them as
environment variables (`PRATIKAI_*`) or in a local `.env` file, which is
git-ignored. See `app/core/config.py` for the full list of settings and
their env var equivalents.

## Project layout

```
app/            FastAPI backend — core (planner/executor/orchestrator), entities, llm,
                speech, vision, computer, memory, knowledge, learning, avatar, security,
                api, db (models + Alembic migrations)
entities/       Per-entity assets (face images, voice models, private knowledge)
data/           SQLite database, logs, conversations, training data, embeddings — all git-ignored
models/         Downloaded local model weights — git-ignored
frontend/       React + TypeScript + Tailwind UI
scripts/        setup / start / stop / restart / startup registration / health check
tests/          Automated tests (pytest)
config/         Non-secret settings (config/settings.json)
docs/           Architecture and subsystem documentation, added as each phase lands
```

## Roadmap

| Phase | Scope |
|---|---|
| 1 ✅ | Foundation: backend, frontend, database, config, logging |
| 2 ✅ | Ollama + Qwen3 8B integration, real-time streaming chat |
| 3 ✅ | Entity system (create/edit/delete/duplicate/export/import, isolated memory) |
| 4 ✅ | Conversation engine + memory (SQLite + ChromaDB semantic retrieval, LLM-based extraction) |
| 5 ✅ | Whisper STT + language detection, Piper TTS, mic/voice-reply in chat UI |
| 6 ✅ | Computer tools (filesystem/terminal/mouse/keyboard/clipboard/windows/apps), permission system, confirmation gate, audit log |
| 7 ✅ | Windows UI Automation (pywinauto), browser control (Playwright) |
| 8 ✅ | Agent planner: plan → execute → observe → verify → replan, live-verified with real tasks |
| 9 ✅ | Computer vision: screenshot, OCR (Tesseract), screen dimensions |
| 10 ✅ | Avatar: face upload + state-driven UI (MuseTalk lip-sync documented as not installed — see docs/avatar.md) |
| 11 ✅ | Continuous learning: correction/preference detection, review queue, dashboard |
| 12 ✅ | LoRA/QLoRA: dataset export (functional), training interface (dry-run verified; real run is opt-in via scripts/train_lora.ps1) |
| 13 ✅ | Settings page, startup registration verified live |
| 14 🔶 | Final testing pass (125 tests, all passing), production frontend build verified; no compiled installer beyond the PowerShell scripts |

## Privacy & security

All data — conversations, memories, entity assets, training data — stays
local under `data/` and `entities/` unless you explicitly enable an online
service (Google STT/Translation) and even then only the specific audio/text
you send is transmitted, never uploaded silently. See `docs/security.md`
(added in Phase 6 alongside the permission system it documents).
