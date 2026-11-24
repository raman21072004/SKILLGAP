#!/usr/bin/env bash
# SkillGap-NLP setup for macOS / Linux. Run from the project root:  bash scripts/setup.sh [--skip-ml]
set -euo pipefail
cd "$(dirname "$0")/.."
SKIP_ML=${1:-}
step() { printf "\n==> %s\n" "$1"; }

step "Checking Python and Node"
PY=$(command -v python3.12 || command -v python3.11 || command -v python3)
$PY --version; node --version; npm --version

[ -f .env ] || { cp .env.example .env; echo "Created .env from .env.example"; }

step "Creating Python virtual environment (backend/.venv)"
cd backend
[ -d .venv ] || $PY -m venv .venv
VPY=.venv/bin/python
$VPY -m pip install --upgrade pip
$VPY -m pip install -r requirements.txt -r requirements-dev.txt
if [ "$SKIP_ML" != "--skip-ml" ]; then
  step "Installing CPU PyTorch + sentence-transformers (large download)"
  $VPY -m pip install torch --index-url https://download.pytorch.org/whl/cpu
  $VPY -m pip install -r requirements-ml.txt
  $VPY scripts/download_models.py || true
else
  $VPY scripts/download_models.py --skip-transformer --skip-spacy || true
fi

step "Creating database tables"
$VPY -m alembic upgrade head

step "Installing frontend packages"
cd ../frontend && npm install
echo -e "\nSetup complete. Start with:  bash scripts/run.sh"
