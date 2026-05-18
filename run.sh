#!/bin/bash
# Agent Insight — Fetch + Build + Serve
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "===== Agent Insight ====="
echo "[1/3] Fetching latest data..."
python3 fetcher.py
echo ""
echo "[2/3] Building self-contained HTML..."
python3 build.py
echo ""
echo "[3/3] Starting server → http://localhost:8080"
echo "      Press Ctrl+C to stop"
echo ""
python3 server.py 8080
