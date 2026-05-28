# ReplicateAI

Autonomous replication of empirical economics papers using [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) and a [Modal](https://modal.com) sandbox.

See [ROADMAP.md](../docs/ROADMAP.md) for planned work and [DESIGN.md](../docs/DESIGN.md) for architecture.

## Setup

```bash
cd replicate_ai
uv sync
uv sync --group gui      # optional: browser GUI (--gui)
cp .env.example .env     # add ANTHROPIC_API_KEY (see below)
uv run modal token new   # one-time Modal auth (or set MODAL_TOKEN_* in .env)
```

### Environment variables

| Variable | When required | Purpose |
|----------|---------------|---------|
| `LLM_PROVIDER` | No (default `anthropic`) | `anthropic`, `cloudflare-kimi`, `cloudflare-glm`, `gemini`, or `groq` |
| `ANTHROPIC_API_KEY` | `LLM_PROVIDER=anthropic` | Claude API for the agent and auditor |
| `CF_ACCOUNT_ID`, `CF_AI_API_TOKEN` | Cloudflare providers | Workers AI (Kimi K2.6 / GLM-4.7-Flash) |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | `LLM_PROVIDER=gemini` | Google Gemini API key (Developer API mode) |
| `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT` | Vertex AI mode (`GOOGLE_GENAI_USE_VERTEXAI=true`) | Use Gemini via Vertex AI |
| `GEMINI_THINKING_LEVEL` | `LLM_PROVIDER=gemini` | Thinking level: `minimal` \| `low` \| `medium` \| `high` (default `medium`) |
| `GROQ_API_KEY` | `LLM_PROVIDER=groq` | Groq API key |
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | No* | Modal sandbox; *not needed if you ran `modal token new` |
| `REPLICATE_AI_SANDBOX_TIMEOUT_SECONDS` | No | Modal sandbox timeout (seconds; default 1800 / 30 min) |
| `LANGSMITH_*` | No | Optional tracing in [LangSmith](https://smith.langchain.com/) |
| `TQDM_DISABLE` | No | Disable tqdm progress bars (stability on some macOS setups) |
| `HF_HUB_DISABLE_PROGRESS_BARS` | No | Disable Hugging Face progress bars (often fixes GUI startup crashes) |

See [`.env.example`](.env.example) for a full template.

### LLM providers (testing vs demo)

```bash
# Cheap harness / wiring tests (Cloudflare GLM-4.7-Flash)
LLM_PROVIDER=cloudflare-glm uv run replicate-ai ../examples/card_krueger

# Fuller dry runs (Cloudflare Kimi K2.6)
LLM_PROVIDER=cloudflare-kimi uv run replicate-ai ../examples/card_krueger

# Canonical demo (Anthropic Sonnet)
LLM_PROVIDER=anthropic uv run replicate-ai ../examples/card_krueger

# Google Gemini (Google AI / Gemini)
LLM_PROVIDER=gemini uv run replicate-ai ../examples/card_krueger

# Groq (low-latency inference)
LLM_PROVIDER=groq uv run replicate-ai ../examples/card_krueger

# Or pass --provider on the CLI (overrides LLM_PROVIDER for that run)
uv run replicate-ai ../examples/card_krueger --provider glm
```

PDF parsing runs on the host with **Docling** by default (layout-aware tables).
The first run downloads Docling layout weights from Hugging Face. For legacy
Camelot extraction: `uv run replicate-ai … --pdf-backend legacy` and install
Ghostscript (`brew install ghostscript` on macOS).

**Scanned PDFs:** Older journal issues (e.g. AER pre-2000) are often bitmap scans rather than text-layer PDFs. Docling can detect table regions but cell content may be garbled or missing in `paper_tables.json`. In that case the agent falls back to searching `paper_text.md` and the `target_spec_reference.json` benchmark — replication can still succeed (demonstrated on Imbens et al. 2001). Enabling OCR (`REPLICATE_AI_PDF_OCR=true`) may help on true image scans but is slower and not guaranteed to clean up encoding artifacts in already-digitised PDFs.

## Example packs

See [`../examples/README.md`](../examples/README.md) for all curated paper + data bundles.

| Pack | Paper | Difficulty |
|------|--------|------------|
| `card_krueger` | Card & Krueger (1994) | Demo |
| `dehejia_wahba` | Dehejia & Wahba (1999) / LaLonde NSW | Easy |
| `imbens_lottery` | Imbens, Rubin & Sacerdote (2001) | Easy–medium |
| `angrist_lavy` | Angrist & Lavy (1999) class size | Medium |
| `autor_dorn_hanson` | Autor, Dorn & Hanson (2013) China shock | Medium–hard |
| `acemoglu_johnson_robinson` | Acemoglu, Johnson & Robinson (2001) | Hard |

For each pack (except `card_krueger`, which ships `data.csv` already):

```bash
uv run --directory replicate_ai python ../examples/<pack>/data_population_script.py
# add paper.pdf (links in each pack README)
uv run replicate-ai ../examples/<pack>
```

`target_spec_reference.json` in each pack lists published headline coefficients; it is seeded to `/workspace/target_spec_reference.json` as a read-only hint. The agent still writes `target_specification.json` at runtime.

## Run

The Card & Krueger example pack (`../examples/card_krueger/`) includes
`card_krueger.pdf`, `data.csv` (with a planted demo bug), and `njmin/` survey
files. The CLI extracts the PDF on your machine (CPU-heavy Docling on first run), then
uploads `paper.pdf`, `data.csv`, `paper_text.md`, and `paper_tables.json` into
Modal `/workspace`. The sandbox only runs econometrics code. Regenerate the CSV with:

```bash
uv run python ../examples/card_krueger/data_population_script.py
```

```bash
cd replicate_ai
uv run replicate-ai ../examples/card_krueger
```

On a TTY, that launches the dashboard TUI (see [DESIGN_TUI.md](../docs/DESIGN_TUI.md)): live run log, headline coefficient card, and final audit. Use `--no-tui` for the plain Rich/stdout CLI (CI-friendly).

When you pass an `example_dir`, the audit is saved on the host after a successful run:

- Default: `<example_dir>/replication_audit.md`
- Override: `--audit-out /path/to/audit.md`
- TUI: auto-save on completion; press `s` to save again
- Opt out: `--no-save-audit`

```bash
# UI shell with fake demo data (no Modal / LLM)
uv run replicate-ai --tui-demo

# Force TUI or disable it
uv run replicate-ai --tui ../examples/card_krueger
uv run replicate-ai --no-tui ../examples/card_krueger

# Browser GUI (requires: uv sync --group gui)
uv run replicate-ai --gui
uv run replicate-ai --gui -p anthropic ../examples/card_krueger
uv run replicate-ai --gui-demo
```

See [DESIGN_GUI.md](../docs/DESIGN_GUI.md) for launcher, uploads, and API details.

### GUI run logs

The GUI persists a per-run host log file you can view in-browser via **View full log**:

- `<example_dir>/.replicate_ai/runs/<run_id>.log`

`replicate-ai` is a console script declared in `[project.scripts]`; equivalent
to `uv run python -m replicate_ai.main`.

## Module layout

```
src/replicate_ai/
├── main.py            # CLI entry: argparse, .env loading, TUI vs CLI routing
├── agent.py           # thin wrapper around runner.run_replication
├── runner/            # orchestration + TUI event emission
├── tui/               # Textual dashboard (docs/DESIGN_TUI.md)
├── gui/               # Browser GUI (docs/DESIGN_GUI.md)
├── constants.py       # APP_NAME, default user message, sandbox timeout
├── models.py          # LLM provider selection
├── prompts.py         # loads system prompts from disk
├── sandbox_image.py   # Modal image built from [dependency-groups.sandbox]
├── system_prompts/    # ECONOMETRICIAN_PROMPT.md, AUDITOR.md
├── subagents/         # auditor sub-agent config
├── preflight.py       # host PDF extract + upload to Modal
└── tools/
    ├── pdf_core.py    # PDF dispatch (host)
    └── pdf_docling.py # Docling backend (host)
```

Sandbox Python deps come from `[dependency-groups.sandbox]` in `pyproject.toml`, installed into the Modal image via `uv_pip_install` (see `sandbox_image.py`).

## Tests

```bash
uv run pytest -q
```
