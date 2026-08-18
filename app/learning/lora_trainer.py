"""LoRA/QLoRA personalization (spec section 13) — optional, explicit, never
automatic.

Real training needs a Hugging Face-format base model (separate from the
GGUF Ollama already runs — potentially 15GB+), `peft`/`transformers`/
`bitsandbytes`/`accelerate`, and meaningful GPU time on top of the LLM
already resident in VRAM. None of that is installed or downloaded by
default. This module is genuinely wired up to do the real thing — imports
are lazy so `is_environment_ready()` can report exactly what's missing
without crashing the app — but nothing here runs a multi-gigabyte download
or a training job without an explicit, non-dry-run call.

Adapters this produces would need their own serving path (Ollama doesn't
load raw PEFT adapters directly); that integration is future work and is
called out honestly in docs/learning.md rather than implied here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import PROJECT_ROOT
from app.core.logging import get_logger
from app.learning.dataset import load_dataset_jsonl

logger = get_logger("learning.lora_trainer")

ADAPTERS_DIR = PROJECT_ROOT / "models" / "adapters"


@dataclass
class TrainingConfig:
    base_model_id: str = "Qwen/Qwen2.5-7B-Instruct"  # HF hub id — NOT the Ollama GGUF tag
    dataset_path: str = ""
    output_name: str = "custom-adapter"
    epochs: int = 3
    learning_rate: float = 2e-4
    lora_r: int = 16
    lora_alpha: int = 32
    load_in_4bit: bool = True  # QLoRA


def is_environment_ready() -> dict:
    missing = []
    for pkg in ("peft", "transformers", "bitsandbytes", "accelerate", "datasets", "torch"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    import shutil

    free_gb = shutil.disk_usage(PROJECT_ROOT).free / (1024**3)

    return {
        "ready": not missing,
        "missing_packages": missing,
        "install_hint": "pip install peft transformers bitsandbytes accelerate datasets" if missing else None,
        "free_disk_gb": round(free_gb, 1),
        "disk_warning": None if free_gb > 20 else "Base model + checkpoints typically need 20GB+ free disk.",
    }


def validate_dataset(dataset_path: str, min_examples: int = 10) -> dict:
    rows = load_dataset_jsonl(dataset_path)
    issues = []
    if len(rows) < min_examples:
        issues.append(f"Only {len(rows)} examples — recommend at least {min_examples} for a meaningful LoRA run.")
    for i, row in enumerate(rows):
        if not row.get("input") or not row.get("output"):
            issues.append(f"Row {i} is missing 'input' or 'output'")
    return {"example_count": len(rows), "issues": issues, "valid": not issues}


def dry_run(config: TrainingConfig) -> dict:
    """Validates everything a real run would need, without downloading or
    training anything. This is the path exercised by tests."""
    dataset_report = validate_dataset(config.dataset_path) if config.dataset_path else {"issues": ["No dataset_path set"], "valid": False}
    env = is_environment_ready()

    return {
        "would_download": config.base_model_id,
        "dataset": dataset_report,
        "environment": env,
        "output_adapter_path": str(ADAPTERS_DIR / config.output_name),
        "can_run": env["ready"] and dataset_report.get("valid", False),
    }


def run_training(config: TrainingConfig, dry_run_only: bool = True) -> dict:
    if dry_run_only:
        return dry_run(config)

    env = is_environment_ready()
    if not env["ready"]:
        raise RuntimeError(
            f"Missing packages for LoRA training: {env['missing_packages']}. "
            f"Install with: {env['install_hint']}"
        )

    # Real training path — lazy-imported so the module loads fine without
    # these installed. Not exercised by the automated test suite (multi-GB
    # download + GPU time); see docs/learning.md for how to run it for real.
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        Trainer,
        TrainingArguments,
    )

    rows = load_dataset_jsonl(config.dataset_path)
    dataset = Dataset.from_list(rows)

    bnb_config = BitsAndBytesConfig(load_in_4bit=config.load_in_4bit) if config.load_in_4bit else None
    tokenizer = AutoTokenizer.from_pretrained(config.base_model_id)
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_id, quantization_config=bnb_config, device_map="auto"
    )

    lora_config = LoraConfig(r=config.lora_r, lora_alpha=config.lora_alpha, task_type="CAUSAL_LM")
    model = get_peft_model(model, lora_config)

    def tokenize(example):
        text = f"### Input:\n{example['input']}\n\n### Response:\n{example['output']}"
        return tokenizer(text, truncation=True, max_length=1024)

    tokenized = dataset.map(tokenize)

    output_dir = ADAPTERS_DIR / config.output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=config.epochs,
            learning_rate=config.learning_rate,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            logging_steps=10,
            save_strategy="epoch",
        ),
        train_dataset=tokenized,
    )
    trainer.train()
    model.save_pretrained(str(output_dir))

    return {"status": "completed", "output_adapter_path": str(output_dir)}
