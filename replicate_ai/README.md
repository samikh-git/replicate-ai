# ReplicateAI

Autonomous replication of empirical economics papers using [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) and a [Modal](https://modal.com) sandbox.

See [ROADMAP.md](../docs/ROADMAP.md) for planned work and [DESIGN.md](../docs/DESIGN.md) for architecture.

## Setup

```bash
cd replicate_ai
uv sync
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
| `LANGSMITH_*` | No | Optional tracing in [LangSmith](https://smith.langchain.com/) |

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

PDF parsing runs on the host. Install Ghostscript for Camelot table extraction:
`brew install ghostscript` on macOS.

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

`target_spec_reference.json` in each pack lists published headline coefficients for comparison (the agent still writes `target_specification.json` at runtime).

## Run

The Card & Krueger example pack (`../examples/card_krueger/`) includes
`card_krueger.pdf`, `data.csv` (with a planted demo bug), and `njmin/` survey
files. The CLI extracts the PDF **on your machine** (CPU-heavy OCR/Camelot), then
uploads `paper.pdf`, `data.csv`, `paper_text.md`, and `paper_tables.json` into
Modal `/workspace`. The sandbox only runs econometrics code. Regenerate the CSV with:

```bash
uv run python ../examples/card_krueger/data_population_script.py
```

```bash
cd replicate_ai
uv run replicate-ai ../examples/card_krueger
```

On a TTY, that launches the **dashboard TUI** (see [DESIGN_TUI.md](../docs/DESIGN_TUI.md)): live run log, headline coefficient card, and final audit. Use `--no-tui` for the plain Rich/stdout CLI (CI-friendly).

When you pass an `example_dir`, the audit is **saved on the host** after a successful run:

- Default: `<example_dir>/replication_audit.md`
- Override: `--audit-out /path/to/audit.md`
- TUI: auto-save on completion; press **`s`** to save again
- Opt out: `--no-save-audit`

```bash
# UI shell with fake demo data (no Modal / LLM)
uv run replicate-ai --tui-demo

# Force TUI or disable it
uv run replicate-ai --tui ../examples/card_krueger
uv run replicate-ai --no-tui ../examples/card_krueger
```

`replicate-ai` is a console script declared in `[project.scripts]`; equivalent
to `uv run python -m replicate_ai.main`.

## Module layout

```
src/replicate_ai/
├── main.py            # CLI entry: argparse, .env loading, TUI vs CLI routing
├── agent.py           # thin wrapper around runner.run_replication
├── runner/            # orchestration + TUI event emission
├── tui/               # Textual dashboard (docs/DESIGN_TUI.md)
├── constants.py       # APP_NAME, default user message, sandbox timeout
├── models.py          # LLM provider selection
├── prompts.py         # loads system prompts from disk
├── sandbox_image.py   # Modal image built from [dependency-groups.sandbox]
├── system_prompts/    # ECONOMETRICIAN_PROMPT.md, AUDITOR.md
├── subagents/         # auditor sub-agent config
├── preflight.py       # host PDF extract + upload to Modal
└── tools/pdf_core.py  # PDF parsing logic (host)
```

Sandbox Python deps come from `[dependency-groups.sandbox]` in `pyproject.toml`, installed into the Modal image via `uv_pip_install` (see `sandbox_image.py`).

## Tests

```bash
uv run pytest -q
```
