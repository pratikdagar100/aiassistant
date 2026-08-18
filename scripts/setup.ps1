<#
.SYNOPSIS
    One-time setup for PratikAI: verifies prerequisites, creates the Python
    venv, installs dependencies, initializes the database, and installs
    frontend dependencies.
.DESCRIPTION
    Safe to re-run — every step checks current state before acting.
    Does NOT download LLM/STT/TTS models (see scripts\install_models.ps1,
    added in Phase 2+) and does NOT register Windows startup (see
    scripts\register_startup.ps1) — those are separate, explicit steps.
#>

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

function Fail($message) {
    Write-Host "`n[ERROR] $message" -ForegroundColor Red
    exit 1
}

Write-Host "PratikAI Setup`n==============" -ForegroundColor Cyan

# 1. Windows version
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "[OK] Windows: $($os.Caption) ($($os.Version))"

# 2. Python 3.11 (the ML stack in later phases requires 3.11 specifically —
#    newer interpreters frequently lack prebuilt wheels for torch/faster-whisper/chromadb)
$py311 = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
if (-not (Test-Path $py311)) {
    Fail "Python 3.11 not found at $py311.`n  Install it with: winget install --id Python.Python.3.11 -e"
}
Write-Host "[OK] Python 3.11 found: $py311"

# 3. Node.js
try {
    $nodeVer = node --version
    Write-Host "[OK] Node.js: $nodeVer"
} catch {
    Fail "Node.js not found on PATH.`n  Install it with: winget install --id OpenJS.NodeJS.LTS -e"
}

# 4. Git
try {
    $gitVer = git --version
    Write-Host "[OK] Git: $gitVer"
} catch {
    Fail "Git not found on PATH.`n  Install it with: winget install --id Git.Git -e"
}

# 5. Ollama
try {
    $ollamaVer = ollama --version
    Write-Host "[OK] Ollama: $ollamaVer"
} catch {
    Fail "Ollama not found on PATH.`n  Install it with: winget install --id Ollama.Ollama -e"
}

# 6. NVIDIA GPU / VRAM
try {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] GPU: $gpuInfo"
    } else {
        Write-Host "[WARN] nvidia-smi returned a non-zero exit code — GPU acceleration may be unavailable." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] nvidia-smi not found — GPU acceleration will be unavailable, CPU fallback will be used." -ForegroundColor Yellow
}

# 7. Python virtual environment
if (-not (Test-Path "$root\venv\Scripts\python.exe")) {
    Write-Host "`nCreating virtual environment..."
    & $py311 -m venv "$root\venv"
} else {
    Write-Host "[OK] venv already exists"
}

# 8. Python dependencies
Write-Host "`nInstalling Python dependencies..."
& "$root\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
# CPU-only torch first: sentence-transformers (Phase 4 memory embeddings)
# depends on torch, and the default PyPI wheel is CUDA — that would silently
# compete with the LLM for VRAM. Installing CPU torch first makes pip treat
# the dependency as already satisfied.
& "$root\venv\Scripts\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet
if ($LASTEXITCODE -ne 0) { Fail "torch (CPU) install failed — see output above." }
& "$root\venv\Scripts\python.exe" -m pip install -r "$root\requirements.txt"
if ($LASTEXITCODE -ne 0) { Fail "pip install failed — see output above." }

# 9. Frontend dependencies
Write-Host "`nInstalling frontend dependencies..."
Push-Location "$root\frontend"
npm install
if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "npm install failed — see output above." }
Pop-Location

# 10. Directories (idempotent)
$dirs = @(
    "data\conversations", "data\training", "data\embeddings", "data\database", "data\logs",
    "models", "entities\friday\face", "entities\friday\voice", "entities\friday\memory", "entities\friday\knowledge"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path "$root\$d" | Out-Null
}
Write-Host "[OK] Data directories ready"

# 11. Database migrations
Write-Host "`nApplying database migrations..."
& "$root\venv\Scripts\python.exe" -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Fail "alembic upgrade failed — see output above." }

Write-Host "`nSetup complete." -ForegroundColor Green
Write-Host "Next: scripts\install_models.ps1 (pull the default LLM), then scripts\start.ps1"
