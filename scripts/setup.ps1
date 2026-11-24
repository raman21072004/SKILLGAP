# SkillGap-NLP setup for Windows (PowerShell). Run from the project root:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Add -SkipML to skip the ~800 MB deep-learning install (app then uses TF-IDF fallback).
param([switch]$SkipML)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

Step "Checking Python and Node"
python --version
node --version
npm --version

if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Created .env from .env.example" }

Step "Creating Python virtual environment (backend\.venv)"
Set-Location backend
if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt -r requirements-dev.txt

if (-not $SkipML) {
  Step "Installing CPU PyTorch + sentence-transformers (large download)"
  & $py -m pip install torch --index-url https://download.pytorch.org/whl/cpu
  & $py -m pip install -r requirements-ml.txt
}

Step "Downloading NLTK data and models (optional items may fail offline)"
if ($SkipML) { & $py scripts\download_models.py --skip-transformer --skip-spacy } else { & $py scripts\download_models.py }

Step "Creating database tables"
& $py -m alembic upgrade head

Step "Installing frontend packages"
Set-Location ..\frontend
npm install

Set-Location $root
Write-Host "`nSetup complete. Start the app with:  powershell -ExecutionPolicy Bypass -File scripts\run.ps1" -ForegroundColor Green
