#!/usr/bin/env bash
# ParkPulse one-click launcher for macOS / Linux.
# Creates a virtual env, installs deps, runs the pipeline, opens the demo.
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
if [ ! -d ".venv" ]; then
  echo "[setup] creating virtual environment..."
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[setup] installing dependencies..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

echo "[run] building results (python run_all.py)..."
python run_all.py

echo "[run] launching demo (Ctrl+C to stop)..."
streamlit run app.py
