#!/usr/bin/env python3
"""
Build self-contained index.html with embedded insight data.
Run after fetcher.py to generate a standalone HTML file.
"""

import json
import os

DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(DIR, "index.html")
DATA_FILE = os.path.join(DIR, "data", "insights.json")

# Read template
with open(TEMPLATE, "r", encoding="utf-8") as f:
    html = f.read()

# Read data
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Embed data
data_json = json.dumps(data, ensure_ascii=False)
html = html.replace("__INSIGHT_DATA__", data_json)

# Write
with open(TEMPLATE, "w", encoding="utf-8") as f:
    f.write(html)

total = sum(len(data.get(k, [])) for k in ["openai", "anthropic", "karpathy_blog", "karpathy_x"])
print(f"Built {TEMPLATE} with {total} items embedded ({len(data_json)} bytes)")
