# Memory

## Levels (spec section 11)

`Memory.memory_type`: `short_term` (handled by the plain conversation
history sliding window in `app/llm/prompts.py`, not a DB row) / `episodic` /
`semantic` / `profile` / `project` / `global` / `entity`. `Memory.category`
(spec section 12's classification): `temporary` / `preference` / `fact` /
`project` / `personal_context` / `explicit_memory` / `task` / `other`.

## Pipeline

```
user message
  -> app/memory/retrieval.py: semantic search (ChromaDB) + pinned memories, entity-isolated
  -> injected into system prompt (app/llm/prompts.py) — NOT the full conversation history
  -> LLM reply sent back to user immediately
  -> (background task, after response) app/memory/extractor.py: LLM classifies whether
     the message was worth remembering; if so, embeds + stores it
```

Extraction runs as a FastAPI `BackgroundTask` specifically so classification
latency never delays the reply the user is waiting for.

## Isolation

`Memory.entity_id` is a foreign key; `NULL` means GLOBAL scope (explicitly
shared). Every retrieval call filters by `entity_id` — see
`tests/test_memory_retrieval.py::test_retrieval_respects_entity_isolation`
for the live proof.

## Embedding model

`paraphrase-multilingual-MiniLM-L12-v2` (CPU, see `app/memory/embeddings.py`)
— chosen specifically because it's multilingual, matching the project's
language requirements, not just English.
