#!/bin/bash

# ClawTools Daily Maintenance Script
# This script runs daily to maintain and improve the ClawTools repository

echo "Starting ClawTools daily maintenance..."

# 1. Pull latest changes from GitHub
cd /home/admin/clawd/ClawTools
git pull --ff-only

# 2. Check for new ideas from moltbook (once registered)
if [ -f "/home/admin/.config/moltbook/credentials.json" ]; then
    echo "Checking moltbook for new ideas..."
    # TODO: Add moltbook API calls once registered
fi

# 3. Update system monitor if needed
python3 system_monitor.py --check

# 4. Update diary indexer if needed  
python3 diary_indexer.py --update

# 5. Commit any changes
git add .
if ! git diff --cached --quiet; then
    git commit -m "chore: Daily maintenance update $(date +%Y-%m-%d)"
    git push origin main
    echo "Daily maintenance completed and pushed to GitHub"
else
    echo "No changes needed for daily maintenance"
fi

echo "ClawTools daily maintenance completed!"