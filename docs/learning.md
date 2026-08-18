# Continuous Learning & LoRA

## Correction/preference detection (spec section 13)

After every chat turn that has a prior assistant reply, a background task
(`app/memory/learning.py::detect_and_queue`) asks the LLM (constrained JSON
output) whether the user's message was correcting the previous reply or
stating a durable preference — not just continuing the conversation. If so,
a `TrainingExample` row is queued with `status="pending"`.

Nothing is ever auto-approved. The Learning page shows the review queue;
`POST /api/learning/examples/{id}/approve|reject` is a human decision.

## Dataset export

`POST /api/training/dataset/{entity_id}` writes every **approved** example
for that entity to `data/training/<entity_id>_<timestamp>.jsonl`
(`app/learning/dataset.py`) — fully functional, no ML dependencies needed.

## LoRA/QLoRA training — explicit opt-in only

`app/learning/lora_trainer.py` is real, correct code using
`peft`/`transformers`/`bitsandbytes` — but those packages are **not**
installed by default (see the commented-out block in `requirements.txt`),
and a real base-model download (e.g. `Qwen/Qwen2.5-7B-Instruct`, several GB,
separate from the GGUF Ollama uses) never happens silently.

- `GET /api/training/environment` — reports exactly which packages are
  missing, honestly (`is_environment_ready()`), rather than pretending to
  be ready.
- `POST /api/training/dry-run` — validates the dataset and environment
  without downloading or training anything. This is the path the automated
  test suite exercises (`tests/test_lora_trainer.py`).
- `scripts/train_lora.ps1` — the only way to actually run training.
  Defaults to `-DryRun $true`; pass `-DryRun $false` to install
  dependencies and run for real. Deliberately not a one-click UI button.

Resulting adapters are **not** automatically wired into Ollama serving —
Ollama doesn't load raw PEFT adapters directly. That integration (e.g.
merging the adapter and re-exporting to GGUF) is future work, not
implemented here.
