#!/bin/bash
# Agent Insight — Incremental update + build + git push
# Safe to run multiple times per day: dedup via timestamp file.

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

STAMP_FILE="data/.last_success"
LOG_FILE="data/update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ── Same-day dedup ──────────────────────────────────────
TODAY=$(date +%Y-%m-%d)
if [ -f "$STAMP_FILE" ]; then
    LAST=$(cat "$STAMP_FILE" 2>/dev/null || true)
    if [ "$LAST" = "$TODAY" ]; then
        log "Already refreshed today ($TODAY), skipping."
        exit 0
    fi
fi

# ── Fetch + Build ───────────────────────────────────────
log "Step 1/3: Fetching data (incremental)..."
python3 fetcher.py 2>&1 | tee -a "$LOG_FILE"

log "Step 2/3: Building HTML..."
python3 build.py 2>&1 | tee -a "$LOG_FILE"

# ── Git commit + push ───────────────────────────────────
log "Step 3/3: Pushing to GitHub..."

# Ensure git identity is set (for automated commits)
if ! git config user.name >/dev/null 2>&1; then
    git config user.name "Agent Insight Bot"
fi
if ! git config user.email >/dev/null 2>&1; then
    git config user.email "bot@agent-insight.local"
fi

# Stage and commit
git add index.html data/insights.json data/insights_raw.json 2>/dev/null || true

if git diff --cached --quiet; then
    log "No changes to commit."
else
    git commit -m "auto: daily refresh ${TODAY}" 2>&1 | tee -a "$LOG_FILE"
    git push origin main 2>&1 | tee -a "$LOG_FILE"
    log "Pushed to GitHub."
fi

# ── Mark success ────────────────────────────────────────
echo "$TODAY" > "$STAMP_FILE"
log "Done."
