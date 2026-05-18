#!/usr/bin/env python3
"""
Build self-contained index.html with embedded insight data.
Merges Chinese translations from data/translations.json (keyed by title).
"""

import json
import os

DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(DIR, "index.html")
DATA_FILE = os.path.join(DIR, "data", "insights.json")
TRANS_FILE = os.path.join(DIR, "data", "translations.json")


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Read template
with open(TEMPLATE, "r", encoding="utf-8") as f:
    html = f.read()

data = load_json(DATA_FILE)
translations = load_json(TRANS_FILE)

# Apply translations by title
applied = 0
for key in ["openai", "anthropic", "karpathy_blog", "karpathy_x"]:
    for item in data.get(key, []):
        title = item.get("title", "")
        if title in translations:
            item["summary"] = translations[title]
            applied += 1

# Write back translated data for /api/data endpoint
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Embed data into HTML
data_json = json.dumps(data, ensure_ascii=False)
html = html.replace("__INSIGHT_DATA__", data_json)

with open(TEMPLATE, "w", encoding="utf-8") as f:
    f.write(html)

total = sum(len(data.get(k, [])) for k in ["openai", "anthropic", "karpathy_blog", "karpathy_x"])
print(f"Built index.html — {total} items, {applied} translated ({len(data_json)} bytes)")
