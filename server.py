#!/usr/bin/env python3
"""
Agent Insight Server — minimal HTTP server with live refresh.
Serves index.html and exposes /api/refresh to trigger data fetch.
"""

import json
import os
import subprocess
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/refresh":
            self._handle_refresh()
        elif path == "/api/data":
            self._handle_data()
        else:
            super().do_GET()

    def _handle_refresh(self):
        """Run fetcher + build, return result."""
        try:
            subprocess.run(
                [sys.executable, "fetcher.py"],
                cwd=DIR, capture_output=True, timeout=60, text=True
            )
            subprocess.run(
                [sys.executable, "build.py"],
                cwd=DIR, capture_output=True, timeout=10, text=True
            )
            self._send_json({"ok": True, "message": "Data refreshed"})
        except Exception as e:
            self._send_json({"ok": False, "message": str(e)}, 500)

    def _handle_data(self):
        """Serve the latest insights.json."""
        try:
            with open(os.path.join(DIR, "data", "insights.json")) as f:
                data = json.load(f)
            self._send_json(data)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress default logging noise
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Agent Insight → http://localhost:{port}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
