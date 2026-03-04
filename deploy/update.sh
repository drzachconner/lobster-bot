#!/usr/bin/env bash
set -euo pipefail

# lobster-bot — Pull latest and restart
# Usage: ./deploy/update.sh

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "Pulling latest changes..."
git pull --ff-only

echo "Updating dependencies..."
python3 -m pip install -r requirements.txt --quiet

if command -v systemctl >/dev/null 2>&1; then
    echo "Restarting service..."
    sudo systemctl restart lobster-bot 2>/dev/null && echo "  lobster-bot restarted" || echo "  lobster-bot not running"
fi

echo "Done."
