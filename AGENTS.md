# Agent Guidance for Agent Insight

This repository is a small Python-based data fetch/build/serve app that generates a self-contained `index.html` dashboard from external RSS and web sources.

## Key workflows

- Use `./run.sh` for the complete workflow:
  1. `python3 fetcher.py`
  2. `python3 build.py`
  3. `python3 server.py 8080`
- Use `python3 fetcher.py` to refresh raw source data into `data/insights.json`.
- Use `python3 build.py` to merge translations from `data/translations.json` and embed data into `index.html`.
- Use `python3 server.py 8080` to run the local HTTP server with live refresh support.

## Important details

- `fetcher.py` depends on the Python `requests` package.
- The repo does not include a package manager manifest (`requirements.txt`, `pyproject.toml`, `package.json`, etc.).
- The build is self-contained: `index.html` is the front-end template, and `data/insights.json` / `data/translations.json` are the runtime data sources.
- `server.py` exposes `/api/refresh` and `/api/data` for live refresh and data access.

## Primary files

- `README.md` — project overview, usage instructions, and source URLs.
- `fetcher.py` — grabs OpenAI, Anthropic, and Karpathy data, then writes structured JSON.
- `build.py` — applies translations and embeds the JSON into `index.html`.
- `server.py` — serves the app and refresh endpoint.
- `run.sh` — convenience script for fetch/build/serve.
- `index.html` — the self-contained dashboard page.
- `data/insights.json` — cached fetched content.
- `data/translations.json` — Chinese translation cache.

## Agent guidance

- Prefer working from the existing Python scripts and README, not from assumptions about other frameworks.
- Do not add Node.js, npm, or frontend build tool configuration unless the repository already includes them.
- Preserve the current content generation flow: fetch, build, then serve.
- If making changes to HTML or JSON embedding, keep `index.html` self-contained with embedded data.

## References

- [README.md](README.md)
