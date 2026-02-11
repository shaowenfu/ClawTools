#!/usr/bin/env python3
import json
import os
import subprocess
import time
from datetime import datetime

# Configuration (override via environment variables)
# Example:
#   export CLAWDBOT_SESSIONS_JSON="$HOME/.clawdbot/agents/main/sessions/sessions.json"
#   export CLAWDBOT_TARGET_SESSION_KEY="agent:main:main"
SESSIONS_JSON = os.path.expanduser(os.environ.get('CLAWDBOT_SESSIONS_JSON', '~/.clawdbot/agents/main/sessions/sessions.json'))
TARGET_SESSION_KEY = os.environ.get('CLAWDBOT_TARGET_SESSION_KEY', 'agent:main:main')  # main session by default

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

def refresh_session():
    if not os.path.exists(SESSIONS_JSON):
        log(f"Error: {SESSIONS_JSON} not found.")
        return

    try:
        with open(SESSIONS_JSON, 'r') as f:
            data = json.load(f)

        session = data.get(TARGET_SESSION_KEY)
        if not session:
            log(f"Session {TARGET_SESSION_KEY} not found in sessions.json.")
            return

        transcript_path = session.get('sessionFile')
        if not transcript_path or not os.path.exists(transcript_path):
            log(f"Transcript file not found or path missing: {transcript_path}")
            return

        # Backup and clear
        backup_path = f"{transcript_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        os.rename(transcript_path, backup_path)
        with open(transcript_path, 'w') as f:
            pass # Create empty file

        log(f"Successfully refreshed transcript for {TARGET_SESSION_KEY}.")
        log(f"Backup saved to {backup_path}")

        # Restart gateway to apply changes
        log("Restarting gateway...")
        subprocess.run(['moltbot', 'gateway', 'restart'], check=True)
        log("Gateway restart signal sent.")

    except Exception as e:
        log(f"Critical error during session refresh: {e}")

if __name__ == "__main__":
    refresh_session()
