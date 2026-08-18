"""Training dataset + LoRA API (spec section 13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.learning import dataset as dataset_module
from app.learning.lora_trainer import TrainingConfig, dry_run, is_environment_ready

router = APIRouter()


class DryRunRequest(BaseModel):
    dataset_path: str
    base_model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    output_name: str = "custom-adapter"


@router.post("/dataset/{entity_id}")
def create_dataset(entity_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        return dataset_module.export_dataset_jsonl(db, entity_id)
    except dataset_module.DatasetError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/environment")
def environment_status() -> dict:
    return is_environment_ready()


@router.post("/dry-run")
def training_dry_run(req: DryRunRequest) -> dict:
    config = TrainingConfig(base_model_id=req.base_model_id, dataset_path=req.dataset_path, output_name=req.output_name)
    return dry_run(config)
