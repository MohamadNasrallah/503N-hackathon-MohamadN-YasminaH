@echo off
REM Install the Conut AI Ops Agent skill into OpenClaw workspace (Windows)
REM Run from the project root: openclaw\install_skill_windows.bat

set "SKILL_DIR=%APPDATA%\SPB_Data\.openclaw\workspace\skills\conut-ops-agent"
if not exist "%APPDATA%\SPB_Data\.openclaw\workspace" (
    set "SKILL_DIR=%USERPROFILE%\.openclaw\workspace\skills\conut-ops-agent"
)

echo Installing Conut AI Ops Agent skill to: %SKILL_DIR%
if not exist "%SKILL_DIR%" mkdir "%SKILL_DIR%"
copy /Y "openclaw\SKILL.md" "%SKILL_DIR%\SKILL.md"
echo Done. Restart OpenClaw to load the skill.
echo.
echo Now start the API server in another terminal:
echo   set GEMINI_API_KEY=your_key_here
echo   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
pause
