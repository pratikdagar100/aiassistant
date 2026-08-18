# Entities

Every AI entity (Friday, Jarvis, ...) is a row in the `entities` table
(`app/db/models.py`) plus an asset directory at `entities/<id>/{face,voice,memory,knowledge}/`
created by `app/entities/manager.py` on creation.

## Isolation

Conversations, memories, knowledge documents, tasks, and training examples
all carry a foreign key to `entity_id`. Nothing in the codebase queries
these tables without filtering by entity — see the isolation tests in
`tests/test_entities.py::test_memory_isolation_between_entities`. A
`Memory` row with `entity_id = NULL` is the one exception: that's the
explicit GLOBAL scope, shared across every entity on purpose, and is only
created when something calls `create_memory(entity_id=None, ...)` — never
by default.

## Lifecycle

`app/entities/manager.py` — create / get / list / update / delete
(soft by default; `purge_files=True` hard-deletes the DB row, cascades to
conversations/memories/etc., and removes `entities/<id>/` from disk) /
duplicate (never copies conversations or memories — a clone starts clean)
/ export / import (JSON snapshot; never includes credentials).

## Creation wizard

`frontend/src/components/EntityWizard.tsx` — 6 steps: preset, identity,
personality, model/language, memory & autonomy, review. Presets
(`app/entities/profiles.py`) are starting points only, every field stays
editable per entity afterward.

## What's not built yet

Per-entity voice selection (every entity currently uses the global default
Piper voice — see docs/speech.md) and per-entity knowledge bases (Phase 4's
scope stopped at conversational memory; a document-upload knowledge base
was not built in this pass).
