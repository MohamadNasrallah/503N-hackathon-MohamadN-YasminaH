@echo off
REM Start the Conut AI Streamlit Dashboard
REM Requires the API to be running first (start_api.bat)

cd /d "%~dp0"

echo Starting Conut AI Dashboard on http://localhost:8501 ...
echo Make sure the API is running on port 8000 first.
echo Press Ctrl+C to stop.
echo.

python -m streamlit run app/dashboard.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Dashboard failed to start. See message above.
    pause
)
