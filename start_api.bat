@echo off
REM Start the Conut AI Operations Agent API
REM Run this from the project root directory

cd /d "%~dp0"

REM ── Load GEMINI_API_KEY from .env file (optional) ─────────────
REM The .env file is git-ignored and never committed.
REM Copy .env.example to .env and fill in your key to enable Gemini.
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if /i "%%a"=="GEMINI_API_KEY" set GEMINI_API_KEY=%%b
    )
)
REM ─────────────────────────────────────────────────────────────

if "%GEMINI_API_KEY%"=="" (
    echo INFO: GEMINI_API_KEY not set. AI query endpoint disabled.
    echo To enable: copy .env.example to .env and add your key.
    echo The dashboard works fully without it.
    echo.
)

echo Starting Conut AI Operations Agent API on http://localhost:8000 ...
echo API docs: http://localhost:8000/docs
echo Press Ctrl+C to stop.
echo.

python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
