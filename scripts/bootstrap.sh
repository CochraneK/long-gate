#!/usr/bin/env bash
set -euo pipefail

echo "[Long Gate] MODEL SETUP MODE"
echo "This script installs software/models only. Do not pass private data to it."

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.10+ first." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[models,local-llm,documents,stats]'

.venv/bin/longgate doctor
.venv/bin/longgate model setup
.venv/bin/longgate model verify auto

echo
echo "[Long Gate] READY"
echo "Private processing example:"
echo ".venv/bin/longgate semantic-transform-local interview.txt --model auto --out preview.txt"
echo
echo "For hardened private processing, disable network access before using real sensitive data."
