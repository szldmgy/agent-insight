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
# Incremental merge helpers
# ─────────────────────────────────────────────────────────────

# Max items to keep per source
MAX_ITEMS = {
    "openai": 20,
    "anthropic": 20,
    "karpathy_blog": 15,
    "karpathy_x": 10,
}


def load_cache():
    """Load existing insights.json as cache, return {source: [items]}."""
    cache_path = os.path.join(OUTPUT_DIR, "insights.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def merge_incremental(source_key, new_items, cache):
    """
    Merge new items into cached items for a source.
    - Items are identified uniquely by 'link'.
    - New items are prepended; existing cached items preserved.
    - Caps total count at MAX_ITEMS[source_key].
    Returns merged list.
    """
    cached_items = cache.get(source_key, [])
    cached_links = {item.get("link") for item in cached_items}

    # Filter out items already in cache
    truly_new = [item for item in new_items if item.get("link") not in cached_links]

    if truly_new:
        print(f"    → {len(truly_new)} new, {len(cached_items)} cached")

    # Merge: new first, then cached
    merged = truly_new + cached_items

    # Cap
    cap = MAX_ITEMS.get(source_key, 20)
    if len(merged) > cap:
        merged = merged[:cap]

    return merged


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.now().isoformat()}] Fetching insights (incremental)...")

    # Load existing cache
    cache = load_cache()
    cache.pop("_fetched_at", None)  # remove meta key for merging

    new_data = {}

    # OpenAI (Engineering only)
    try:
        fresh_openai = fetch_openai()
        print(f"  OpenAI Engineering: {len(fresh_openai)} fetched")
        new_data["openai"] = merge_incremental("openai", fresh_openai, cache)
    except Exception as e:
        print(f"  OpenAI ERROR: {e}, keeping cached")
        new_data["openai"] = cache.get("openai", [])

    # Anthropic (Engineering)
    try:
        fresh_anthropic = fetch_anthropic()
        print(f"  Anthropic Engineering: {len(fresh_anthropic)} fetched")
        new_data["anthropic"] = merge_incremental("anthropic", fresh_anthropic, cache)
    except Exception as e:
        print(f"  Anthropic ERROR: {e}, keeping cached")
        new_data["anthropic"] = cache.get("anthropic", [])

    # Karpathy Blog
    try:
        fresh_blog = fetch_karpathy_blog()
        print(f"  Karpathy Blog: {len(fresh_blog)} fetched")
        new_data["karpathy_blog"] = merge_incremental("karpathy_blog", fresh_blog, cache)
    except Exception as e:
        print(f"  Karpathy Blog ERROR: {e}, keeping cached")
        new_data["karpathy_blog"] = cache.get("karpathy_blog", [])

    # Karpathy X
    try:
        fresh_x = fetch_karpathy_x()
        print(f"  Karpathy X: {len(fresh_x)} fetched")
        new_data["karpathy_x"] = merge_incremental("karpathy_x", fresh_x, cache)
    except Exception as e:
        print(f"  Karpathy X ERROR: {e}, keeping cached")
        new_data["karpathy_x"] = cache.get("karpathy_x", [])

    # Add timestamp
    new_data["_fetched_at"] = datetime.now(timezone.utc).isoformat()

    # Write JSON
    out_path = os.path.join(OUTPUT_DIR, "insights.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    total = sum(len(new_data.get(k, [])) for k in ["openai", "anthropic", "karpathy_blog", "karpathy_x"])
    print(f"  Written {total} items to {out_path}")


if __name__ == "__main__":
    main()
