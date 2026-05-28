# ReplicateAI Browser GUI — Design Document

Status: v1  
Last updated: 2026-05-26

## Overview

The browser GUI is a local-only dashboard served by Starlette on `127.0.0.1`. It reuses the same event pipeline as the Textual TUI (`run_replication` → `apply_event` → view state).

```bash
cd replicate_ai
uv sync --group gui
uv run replicate-ai --gui
uv run replicate-ai --gui -p anthropic ../examples/card_krueger
uv run replicate-ai --gui-demo
```

## Entry points

| Command | Behavior |
|---------|----------|
| `--gui` | Open launcher at `/` (pick pack, upload files/folder, provider, Start) |
| `--gui <example_dir>` | Skip launcher; open run dashboard immediately |
| `--gui-demo` | Fake event stream (no Modal / LLM) |

`--gui` does not require a TTY. Mutually exclusive with the default TUI path.

## Launcher

Three input modes:

1. **Curated packs** — cards from `examples/*` (`GET /api/examples`).
2. **Upload files** — `paper.pdf` + `data.csv` (`POST /api/upload?mode=files`).
3. **Upload folder** — directory picker / drag-and-drop (`POST /api/upload?mode=directory`).

Upload size: **no server cap**. Client shows soft warnings at 100 MB+ and a confirm dialog at 1 GB+.

**Provider dropdown:** five canonical backends (`anthropic`, `cloudflare-kimi`, `cloudflare-glm`, `gemini`, `groq`) from `models.list_provider_options()`. CLI aliases (`kimi`, `glm`) still work via `-p` but are not listed twice in the UI.

## Run dashboard

Mirrors [DESIGN_TUI.md](./DESIGN_TUI.md): phases, run log, model spec, coefficient card, audit markdown (via marked.js), save audit button.

Real-time updates: Server-Sent Events on `GET /api/runs/{id}/events`.

## API

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/config` | GET | Providers, default provider, optional `initial_run_id` |
| `/api/examples` | GET | Curated pack metadata |
| `/api/upload` | POST | Multipart upload (`mode=files` or `mode=directory`) |
| `/api/runs` | POST | Start run `{ example_dir, provider, message? }` |
| `/api/runs/{id}` | GET | JSON snapshot |
| `/api/runs/{id}/events` | GET | SSE snapshots |
| `/api/runs/{id}/save-audit` | POST | Write `replication_audit.md` |

## Stack

- **Backend:** Starlette + uvicorn (Python); optional `[dependency-groups.gui]`.
- **Frontend:** Static HTML/CSS/JS in `replicate_ai/gui/static/` (Source Serif 4 + Inter).
- **Not Hono:** replication stays in Python; no second Node server.

## Module map

| File | Role |
|------|------|
| `gui/launch.py` | Port selection, browser open, uvicorn |
| `gui/server.py` | Starlette routes |
| `gui/session.py` | RunSession + SSE subscribers |
| `gui/serialize.py` | `TuiViewState` → JSON |
| `gui/uploads.py` | Temp pack dirs, streaming writes |
| `gui/examples_scan.py` | List `examples/*` |
| `gui/static/` | Launcher + dashboard SPA |
