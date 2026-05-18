#!/usr/bin/env python3
"""
Agent Insight Fetcher
Fetches latest posts from OpenAI Engineering, Anthropic Engineering, Karpathy (blog + X)
and writes structured JSON for the frontend.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from xml.etree import ElementTree as ET

import requests

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# ─────────────────────────────────────────────────────────────
# Sources
# ─────────────────────────────────────────────────────────────

def fetch_openai():
    """Fetch OpenAI engineering blog posts via RSS (filter category=Engineering)."""
    url = "https://openai.com/news/rss.xml"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    items = []
    for item_elem in root.findall(".//item"):
        category = (item_elem.findtext("category") or "").strip()
        if category != "Engineering":
            continue

        title = (item_elem.findtext("title") or "").strip()
        link = (item_elem.findtext("link") or "").strip()
        desc = (item_elem.findtext("description") or "").strip()
        pub_date = (item_elem.findtext("pubDate") or "").strip()

        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            ts = dt.isoformat()
        except ValueError:
            ts = pub_date

        items.append({
            "title": unescape(title),
            "link": link,
            "summary": clean_html(unescape(desc))[:300],
            "date": ts,
            "category": category,
        })

    return items


def fetch_anthropic():
    """Fetch Anthropic Engineering blog. Tries scraping SSR HTML,
    falls back to cached data."""
    url = "https://www.anthropic.com/engineering"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.text

    items = []

    # Extract engineering article data from the SSR HTML
    # The page source contains article titles, dates, and URLs in text form
    # Pattern: "/engineering/SLUG", "Article Title", "Mon DD, YYYY"

    # Find all engineering URLs
    url_matches = re.findall(r'/engineering/([^"\s]+)"', text)
    slugs_seen = set()

    for slug in url_matches:
        # Skip non-article paths
        if slug in slugs_seen or slug in ("",):
            continue
        slugs_seen.add(slug)

        link = f"https://www.anthropic.com/engineering/{slug}"

        # Try to find the article title near this URL in the page text
        # Search for title text after the URL pattern
        title = _slug_to_title(slug)

        items.append({
            "title": title,
            "link": link,
            "summary": "",
            "date": "",
            "category": "engineering",
        })

    # If scraping produced noise, load from cached
    if len(items) < 3:
        return _load_cached_anthropic()

    return items


def _slug_to_title(slug):
    """Convert a URL slug to a readable title."""
    # Remove trailing slashes and known suffixes
    slug = slug.rstrip("/")
    # Common title patterns in Anthropic slugs
    title_map = {
        "april-23-postmortem": "An update on recent Claude Code quality reports",
        "managed-agents": "Scaling Managed Agents: Decoupling the brain from the hands",
        "claude-code-auto-mode": "Claude Code auto mode: a safer way to skip permissions",
        "harness-design-long-running-apps": "Harness design for long-running application development",
        "eval-awareness-browsecomp": "Eval awareness in Claude Opus 4.6's BrowseComp performance",
        "infrastructure-noise": "Quantifying infrastructure noise in agentic coding evals",
        "building-c-compiler": "Building a C compiler with a team of parallel Claudes",
        "AI-resistant-technical-evaluations": "Designing AI-resistant technical evaluations",
        "demystifying-evals-for-ai-agents": "Demystifying evals for AI agents",
        "effective-harnesses-for-long-running-agents": "Effective harnesses for long-running agents",
        "advanced-tool-use": "Introducing advanced tool use on the Claude Developer Platform",
        "code-execution-with-mcp": "Code execution with MCP: Building more efficient agents",
        "claude-code-sandboxing": "Beyond permission prompts: making Claude Code more secure and autonomous",
        "equipping-agents-for-the-real-world-with-agent-skills": "Equipping agents for the real world with Agent Skills",
        "effective-context-engineering-for-ai-agents": "Effective context engineering for AI agents",
        "a-postmortem-of-three-recent-issues": "A postmortem of three recent issues",
        "writing-tools-for-agents": "Writing effective tools for agents — with agents",
        "desktop-extensions": "Desktop Extensions: One-click MCP server installation for Claude Desktop",
        "multi-agent-research-system": "How we built our multi-agent research system",
        "claude-code-best-practices": "Claude Code: Best practices for agentic coding",
        "claude-think-tool": 'The "think" tool: Enabling Claude to stop and think in complex tool use situations',
        "swe-bench-sonnet": "Raising the bar on SWE-bench Verified with Claude 3.5 Sonnet",
        "building-effective-agents": "Building effective agents",
        "contextual-retrieval": "Introducing Contextual Retrieval",
        "how-claude-thinks": "How Claude thinks",
    }
    if slug in title_map:
        return title_map[slug]

    # Fallback: humanize the slug
    return slug.replace("-", " ").title()


def _load_cached_anthropic():
    """Load Anthropic data from cached insights.json."""
    try:
        cache_path = os.path.join(OUTPUT_DIR, "insights.json")
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                cached = json.load(f)
            return cached.get("anthropic", [])
    except Exception:
        pass
    return []


def fetch_karpathy_blog():
    """Fetch Karpathy's blog via RSS."""
    url = "https://karpathy.github.io/feed.xml"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    items = []
    for item_elem in root.findall(".//item"):
        title = (item_elem.findtext("title") or "").strip()
        link = (item_elem.findtext("link") or "").strip()
        desc = (item_elem.findtext("description") or "").strip()
        pub_date = (item_elem.findtext("pubDate") or "").strip()

        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            ts = dt.isoformat()
        except ValueError:
            ts = pub_date

        summary = clean_html(unescape(desc))[:300]
        items.append({
            "title": unescape(title),
            "link": link,
            "summary": summary,
            "date": ts,
            "category": "blog",
        })

    return items


def fetch_karpathy_x():
    """Fetch Karpathy's X/Twitter via Nitter RSS."""
    url = "https://nitter.net/karpathy/rss"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    items = []
    for item_elem in root.findall(".//item"):
        title = (item_elem.findtext("title") or "").strip()
        link = (item_elem.findtext("link") or "").strip()
        desc = (item_elem.findtext("description") or "").strip()
        pub_date = (item_elem.findtext("pubDate") or "").strip()

        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            ts = dt.isoformat()
        except ValueError:
            ts = pub_date

        items.append({
            "title": clean_html(unescape(title))[:200],
            "link": link,
            "summary": clean_html(unescape(desc))[:280],
            "date": ts,
            "category": "twitter",
        })

    return items


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def clean_html(text):
    """Strip HTML tags (including style/script blocks) and normalize whitespace."""
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.now().isoformat()}] Fetching insights...")

    all_data = {}

    # OpenAI (Engineering only)
    try:
        all_data["openai"] = fetch_openai()
        print(f"  OpenAI Engineering: {len(all_data['openai'])} items")
    except Exception as e:
        print(f"  OpenAI ERROR: {e}")
        all_data["openai"] = []

    # Anthropic (Engineering)
    try:
        all_data["anthropic"] = fetch_anthropic()
        print(f"  Anthropic Engineering: {len(all_data['anthropic'])} items")
    except Exception as e:
        print(f"  Anthropic ERROR: {e}")
        all_data["anthropic"] = []

    # Karpathy Blog
    try:
        all_data["karpathy_blog"] = fetch_karpathy_blog()
        print(f"  Karpathy Blog: {len(all_data['karpathy_blog'])} items")
    except Exception as e:
        print(f"  Karpathy Blog ERROR: {e}")
        all_data["karpathy_blog"] = []

    # Karpathy X
    try:
        all_data["karpathy_x"] = fetch_karpathy_x()
        print(f"  Karpathy X: {len(all_data['karpathy_x'])} items")
    except Exception as e:
        print(f"  Karpathy X ERROR: {e}")
        all_data["karpathy_x"] = []

    # Add timestamp
    all_data["_fetched_at"] = datetime.now(timezone.utc).isoformat()

    # Write JSON
    out_path = os.path.join(OUTPUT_DIR, "insights.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"  Written to {out_path}")


if __name__ == "__main__":
    main()
