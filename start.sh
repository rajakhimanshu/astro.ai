#!/usr/bin/env bash
# One-command launcher (macOS / Linux): installs dependencies on first run, then starts backend + frontend.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env - add your GROQ_API_KEY (or set LLM_MODE=ollama) for AI replies."
fi

PY="$PWD/venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
fi

STAMP=venv/.deps-installed
if [ ! -f "$STAMP" ] || [ backend/requirements.txt -nt "$STAMP" ]; then
  echo "Installing backend dependencies (first run takes a few minutes)..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r backend/requirements.txt
  touch "$STAMP"
fi

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

(cd backend && exec "$PY" main.py) &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

echo ""
echo "Backend: http://127.0.0.1:8001   App: http://localhost:3000"
echo "Press Ctrl+C to stop both."
cd frontend && npm run dev
