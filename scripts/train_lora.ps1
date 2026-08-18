<#
.SYNOPSIS
    Runs (or dry-run validates) a LoRA/QLoRA training job — spec section 13.
.DESCRIPTION
    This is a deliberately manual, explicit entry point — NOT reachable from
    the API/UI as a one-click action — because a real run downloads a
    multi-GB Hugging Face base model and uses significant GPU time.
    Defaults to -DryRun, which validates environment + dataset without
    downloading or training anything.
.PARAMETER DatasetPath
    Path to a dataset JSONL produced by the Learning/Training page
    (POST /api/training/dataset/{entity_id}).
.PARAMETER DryRun
    Default $true. Pass -DryRun:$false to actually install dependencies
    (if missing) and run training.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$DatasetPath,
    [string]$BaseModelId = "Qwen/Qwen2.5-7B-Instruct",
    [string]$OutputName = "custom-adapter",
    [bool]$DryRun = $true
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path $DatasetPath)) {
    Write-Host "[ERROR] Dataset not found: $DatasetPath" -ForegroundColor Red
    Write-Host "  Create one first: POST /api/training/dataset/{entity_id} (or the Training page)"
    exit 1
}

if (-not $DryRun) {
    Write-Host "Installing LoRA training dependencies (peft, transformers, bitsandbytes, accelerate, datasets)..." -ForegroundColor Yellow
    Write-Host "This includes large packages and will also trigger a multi-GB base model download on first run."
    & "$root\venv\Scripts\python.exe" -m pip install peft transformers bitsandbytes accelerate datasets
    if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] dependency install failed" -ForegroundColor Red; exit 1 }
}

$pyCode = @"
import json
from app.learning.lora_trainer import TrainingConfig, run_training

config = TrainingConfig(
    base_model_id=r'$BaseModelId',
    dataset_path=r'$DatasetPath',
    output_name=r'$OutputName',
)
result = run_training(config, dry_run_only=$($DryRun.ToString()))
print(json.dumps(result, indent=2))
"@

& "$root\venv\Scripts\python.exe" -c $pyCode
