#!/usr/bin/env bash
# Install the Conut AI Ops Agent skill into OpenClaw workspace
# Run from the project root: bash openclaw/install_skill.sh

SKILL_DIR="${HOME}/.openclaw/workspace/skills/conut-ops-agent"

echo "Installing Conut AI Ops Agent skill to: $SKILL_DIR"
mkdir -p "$SKILL_DIR"
cp openclaw/SKILL.md "$SKILL_DIR/SKILL.md"
echo "Done. Restart OpenClaw to load the new skill."
echo ""
echo "Then start the API server:"
echo "  export GEMINI_API_KEY=<your_key>"
echo "  uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
