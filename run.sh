#!/bin/bash
# Agent Insight — Fetch + Build standalone HTML
# Usage: ./run.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "===== Agent Insight ====="
echo "[1/2] Fetching latest data..."
python3 fetcher.py
echo ""
echo "[2/2] Building self-contained HTML..."
python3 build.py
echo ""
echo "Done! Open index.html in your browser:"
echo "  open index.html"
echo ""
open index.html
