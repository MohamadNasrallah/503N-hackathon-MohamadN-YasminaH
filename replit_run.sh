#!/bin/bash
# Conut AI Ops — Replit startup script
# Starts FastAPI backend + Streamlit dashboard

set -e

echo "================================================"
echo "  Conut AI Ops Agent — Starting on Replit"
echo "================================================"
echo ""

# Install/update dependencies
echo "[0/2] Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Optional: enable Gemini AI agent if key is set
if [ -n "$GEMINI_API_KEY" ]; then
    echo "      GEMINI_API_KEY detected - installing google-generativeai..."
    pip install -q google-generativeai
fi

echo ""

# Start FastAPI backend in background
echo "[1/2] Starting API backend on port 8000..."
python -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 &
API_PID=$!

# Give the API time to start before Streamlit calls it
sleep 5

# Start Streamlit dashboard (foreground — Replit webview shows this)
echo "[2/2] Starting Streamlit dashboard on port 8501..."
echo ""
python -m streamlit run app/dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false

# If Streamlit exits, stop the API too
kill $API_PID 2>/dev/null || true
