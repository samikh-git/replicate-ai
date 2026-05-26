# AGENTS.md — ReplicateAI

Guidance for AI coding agents working in this repository.

## What this project is

ReplicateAI autonomously replicates the headline empirical coefficient(s) of an applied economics paper from a PDF + raw CSV, without author replication code. It uses [LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview), a Modal sandbox for Python econometrics, and a statistical auditor sub-agent that writes `replication_audit.md` (verdicts: `MATCH`, `CLOSE`, `MISMATCH`, `FAILED`).

v1 scope (honest limits):

- Curated example packs under `examples/` — not arbitrary papers.
- Python only in the sandbox (`statsmodels`, `linearmodels`, etc.) — no Stata/R.
- Public data only — no PSID, Compustat, Census microdata, or credentialed sources.
- One headline estimand per run — not full tables/figures.
- Portfolio/demo orientation; see `docs/DESIGN.md` §2 non-goals.

## Repository layout

```
replciate-ai/                    # repo root (note spelling)
├── AGENTS.md                    # this file
├── docs/                        # DESIGN.md, DESIGN_TUI.md, ROADMAP.md
├── examples/                    # paper + data packs (not Python package)
│   ├── README.md
│   ├── _common.py               # download / Stata / RData helpers for data scripts
│   └── <pack>/                  # card_krueger, dehejia_wahba, …
│       ├── README.md
│       ├── data.csv
│       ├── data_population_script.py
│       ├── target_spec_reference.json   # published benchmarks (reference only)
│       └── paper.pdf            # user-provided; often gitignored
└── replicate_ai/                # installable package + CLI
    ├── pyproject.toml
    ├── .env.example             # copy to .env; never commit .env
    ├── src/replicate_ai/
    └── tests/
```

All application code lives under `replicate_ai/`. Run commands from that directory unless noted.

## Architecture (host vs Modal)

| Stage | Where | Key modules |
|-------|--------|-------------|
| PDF → `paper_text.md`, `paper_tables.json` | Host | `preflight.py`, `tools/pdf_core.py` |
| Seed `paper.pdf`, `data.csv` | Host → Modal | `workspace.py`, `example_assets.py` |
| Agent + auditor LLM | Host | `models.py`, `agent.py`, `runner/run.py` |
| Replication scripts | Modal `/workspace` | `modal_sandbox.py`, `sandbox_image.py` |

There is no persistent host `workspace/` directory. Each run copies an example pack into Modal `/workspace`.

### Modal `/workspace` contract

```
/workspace/
  paper.pdf, data.csv              # inputs (seeded)
  paper_text.md, paper_tables.json # host preflight uploads
  target_specification.json        # agent writes before coding
  scripts/attempt_NN.py, logs/     # agent loop
  results/coefficients.json        # on success
  replication_audit.md             # auditor writes
```

Schemas and rubric: `docs/DESIGN.md` §6.5–6.8. Canonical prompts: `replicate_ai/src/replicate_ai/system_prompts/` (loaded via `prompts.py`).

## Entry points

```bash
cd replicate_ai
uv sync
cp .env.example .env   # ANTHROPIC_API_KEY, MODAL, optional LLM_PROVIDER
uv run modal token new # if not using MODAL_TOKEN_* in .env
```

| Command | Purpose |
|---------|---------|
| `uv run replicate-ai ../examples/<pack>` | Full run; TUI on TTY |
| `uv run replicate-ai --no-tui ../examples/<pack>` | CLI / CI |
| `uv run replicate-ai --tui-demo` | Fake TUI stream (no Modal/LLM) |
| `uv run replicate-ai ../examples/<pack> --skip-pdf-extract` | Skip host PDF step on reruns |
| `uv run replicate-ai ../examples/<pack> --audit-out ./audit.md` | Save audit to a custom path |
| `uv run pytest -q` | Tests (from `replicate_ai/`) |

Completed runs write `replication_audit.md` to the example folder by default (`audit_export.py`). TUI key `s` re-saves the audit.

Example data refresh:

```bash
uv run --directory replicate_ai python ../examples/<pack>/data_population_script.py
```

## Module map (where to change what)

| Goal | Files |
|------|--------|
| CLI flags, TUI routing | `main.py` |
| Run orchestration, deliverable polling | `runner/run.py`, `runner/log_poll.py` |
| Parse coeffs for TUI card | `runner/parse.py`, `runner/display.py` |
| TUI rendering / scroll / detail pane | `tui/app.py`, `tui/handler.py`, `tui/format.py` |
| TUI events (testable) | `tui/events.py` |
| Econometrician / auditor instructions | `system_prompts/*.md` |
| Auditor sub-agent + `get_current_date` tool | `subagents/auditor.py`, `tools/date_tool.py` |
| LLM providers | `models.py`, `.env.example` |
| PDF extraction | `tools/pdf_core.py`, `preflight.py` |
| Modal sandbox + execute | `modal_sandbox.py`, `sandbox_image.py` |
| Resolve `paper.pdf` / `data.csv` in examples | `example_assets.py`, `workspace.py` |
| New example pack | `examples/<name>/`, update `examples/README.md` |

## TUI and runner events

The runner emits structured events; the TUI applies them via pure `apply_event()` in `tui/handler.py` (unit-tested without Textual).

Important events: `PhaseChanged`, `LogChunk`, `DeliverableWritten`, `CoefficientsParsed`, `AuditReady`, `RunFinished`.

Detail pane: must show `audit_md` even when `coeffs` is `None`. Deliverable polling must not mark files “seen” on empty reads (`runner/run.py` → `_read_nonempty_file`).

## Testing conventions

- Prefer mocked Modal/agent for `runner/run.py` (`tests/test_runner_run.py`).
- Keep handler logic in `tui/handler.py` testable without UI (`tests/test_tui_handler.py`).
- Run `uv run pytest -q` from `replicate_ai/` after changes to runner, TUI, preflight, or parsing.
- Do not add tests that only assert obvious constants unless they guard real regression behavior.

## Example packs

Six packs are documented in `examples/README.md`. Each needs:

1. `data.csv` (via `data_population_script.py`)
2. `paper.pdf` (user adds; links in pack README)
3. `target_spec_reference.json` — reference published numbers; the agent still writes runtime `target_specification.json`

Only `card_krueger` ships a PDF in-repo; other packs are run candidates, not guaranteed pre-replicated.

## Coding principles for agents

1. Minimal diffs — Match existing style; do not refactor unrelated code.
2. Prompts are product — Changes to `ECONOMETRICIAN_PROMPT.md` / `AUDITOR.md` affect all runs; edit deliberately and mention in PR/commit notes.
3. Host vs sandbox — PDF/Camelot stays on host; do not move heavy extraction into Modal without updating `docs/DESIGN.md` and image size.
4. No secrets — Never commit `.env`, API keys, or tokens. Do not log secrets.
5. No git config changes — Do not amend commits unless user asked and hooks allow it.
6. Dependencies — App: `pyproject.toml` `[project]`. Sandbox econometrics: `[dependency-groups.sandbox]` (installed in Modal image via `sandbox_image.py`). Dev-only (e.g. `rdata` for example scripts): `[dependency-groups.dev]`.
7. Circular imports — Shared constants live in `constants.py` (used by `agent.py` and `runner/run.py`).

## Common pitfalls

- Auditor date — Auditor should call `get_current_date`; do not hardcode dates in prompts.
- Seeding — `seed_example_to_sandbox` requires both PDF and CSV; uses `find_example_pdf` / `find_example_data_csv`.
- Subagent tools — Pass LangChain tool objects in `auditor_subagent["tools"]`, not string names; filesystem tools are injected by Deep Agents middleware.
- Card & Krueger demo bug — `card_krueger/data.csv` may use planted bugs (`--plant-bug`); other packs use clean data.

## Design documents

Read before large features:

- `docs/DESIGN.md` — schemas, workflow, non-goals, auditor tolerance (rel. dev. ≤5% → MATCH, etc.).
- `docs/DESIGN_TUI.md` — phases (Read paper · Specify · Estimate · Audit), headline card, deliverable bullets.
- `replicate_ai/README.md` — setup, providers, example table.

## When unsure

- Match behavior to `docs/DESIGN.md` over comments if they diverge.
- For UI behavior, check `tui/handler.py` + `tests/test_tui_handler.py`.
- For replication outcomes, the ground truth is the paper’s published table, not `target_spec_reference.json` (reference only).
