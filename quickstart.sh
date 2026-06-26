#!/usr/bin/env bash
# VibrantAD — one command to run the app
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
"$PY" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo "▸ Starting VibrantAD at http://localhost:8501"
.venv/bin/streamlit run app.py
