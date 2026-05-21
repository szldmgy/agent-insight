#!/usr/bin/env python3
"""
Send email notification when Agent Insight has new content.
Reads SMTP credentials from data/smtp.json (git-ignored).
"""
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIR, "data", "smtp.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: SMTP config not found at {CONFIG_PATH}", file=sys.stderr)
        print("Create data/smtp.json with:", file=sys.stderr)
        print(json.dumps({
            "host": "smtp.example.com",
            "port": 587,
            "user": "your@email.com",
            "password": "app-password-or-token",
            "to": "recipient@example.com",
        }, indent=2), file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def send_notification(config, subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["From"] = config["user"]
    msg["To"] = config["to"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP_SSL(config["host"], config["port"], timeout=60) as server:
        server.login(config["user"], config["password"])
        server.sendmail(config["user"], [config["to"]], msg.as_string())

    print(f"Email sent to {config['to']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: notify.py <new_count> [diff_summary]", file=sys.stderr)
        sys.exit(1)

    new_count = sys.argv[1]
    diff_summary = sys.argv[2] if len(sys.argv) > 2 else ""

    config = load_config()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"[Agent Insight] {new_count} new items — {now}"

    body = f"""<html><body style="font-family: -apple-system, sans-serif; max-width: 600px;">
<h2>🔔 Agent Insight 更新</h2>
<p><strong>{now}</strong> — 发现 <strong>{new_count}</strong> 条新内容</p>
<pre style="background:#f5f2eb; padding:12px; border-radius:8px;">{diff_summary}</pre>
<p>👉 <a href="https://szldmgy.github.io/agent-insight/">打开仪表盘</a></p>
</body></html>"""

    send_notification(config, subject, body)


if __name__ == "__main__":
    main()
