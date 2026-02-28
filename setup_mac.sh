#!/bin/bash
# Conut AI Ops — macOS Local Setup & Launch
# Run from the project root: bash setup_mac.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "================================================"
echo "  Conut AI Ops Agent — macOS Setup & Launch"
echo "================================================"
echo ""

# ── Check Python 3 ────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    echo "Install Python 3.11+ from: https://www.python.org/downloads/"
    echo "Or via Homebrew: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python $PYTHON_VERSION detected."

# ── Create virtual environment ────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "Virtual environment activated."
echo ""

# ── Install dependencies ──────────────────────────────────────────────────────
echo "Installing dependencies (first run takes ~1 min)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Optional: Gemini AI support if .env has key
if [ -f ".env" ] && grep -q "GEMINI_API_KEY" .env 2>/dev/null; then
    echo "GEMINI_API_KEY found - installing google-generativeai..."
    pip install -q google-generativeai
fi

echo "Dependencies ready."
echo ""

# ── Start FastAPI backend ─────────────────────────────────────────────────────
echo "[1/2] Starting API on http://localhost:8000 ..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 4

# ── Start Streamlit dashboard ─────────────────────────────────────────────────
echo "[2/2] Starting Dashboard on http://localhost:8501 ..."
python -m streamlit run app/dashboard.py \
    --server.port 8501 \
    --server.headless true &
DASH_PID=$!
sleep 3

# ── Print info ────────────────────────────────────────────────────────────────
echo ""
echo "================================================"
echo "  Conut AI Ops is LIVE!"
echo "  Dashboard : http://localhost:8501"
echo "  API docs  : http://localhost:8000/docs"
echo "  Press Ctrl+C to stop both servers."
echo "================================================"
echo ""

# Auto-open in browser
open http://localhost:8501 2>/dev/null || true

# ── Wait — Ctrl+C cleanly stops both servers ──────────────────────────────────
trap "echo ''; echo 'Stopping servers...'; kill $API_PID $DASH_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait $DASH_PID
