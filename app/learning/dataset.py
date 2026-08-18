"""Builds a training dataset from approved TrainingExample rows (spec
section 13). Pure data export — no ML dependencies, always available."""

from __future__ import annotations

import json
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import TrainingExample


class DatasetError(ValueError):
    pass


def build_dataset(db: Session, entity_id: str) -> list[dict]:
    examples = (
        db.query(TrainingExample)
        .filter_by(entity_id=entity_id, status="approved")
        .order_by(TrainingExample.created_at)
        .all()
    )
    return [{"input": e.input_text, "output": e.output_text, "category": e.category} for e in examples]


def export_dataset_jsonl(db: Session, entity_id: str, *, min_examples: int = 1) -> dict:
    rows = build_dataset(db, entity_id)
    if len(rows) < min_examples:
        raise DatasetError(
            f"Only {len(rows)} approved example(s) for '{entity_id}' — need at least {min_examples}. "
            "Approve more candidates on the Learning page first."
        )

    settings = get_settings()
    training_dir = settings.database.resolved_path().parent.parent / "training"
    training_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{entity_id}_{int(time.time())}.jsonl"
    path = training_dir / filename
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {"path": str(path), "example_count": len(rows)}


def load_dataset_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise DatasetError(f"Dataset not found: {path}")
    rows = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
