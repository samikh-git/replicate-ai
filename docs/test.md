# Agent replication test suite

Specification for evaluating ReplicateAI on curated example packs. Each row is one **headline estimand** per pack (see `examples/<pack>/target_spec_reference.json` for published targets; the agent still writes runtime `target_specification.json`).

**Ground truth for the auditor:** published table values in the paper (and pack README), not `target_spec_reference.json` alone — the JSON is a maintainer reference.

**Verdict rubric** ([DESIGN.md §6.8](./DESIGN.md#68-auditor_prompt-sub-agent)): `MATCH` (same sign, rel. dev. ≤ 5%, same significance bucket), `CLOSE` (same sign + significance, 5–20% rel. dev.), `MISMATCH`, `FAILED` (no usable estimate / run error).

---

## How to run

```bash
cd replicate_ai
uv sync
# optional: uv sync --group gui

# One pack (record results in tables below)
uv run replicate-ai --no-tui -p anthropic ../examples/<pack>
# or: uv run replicate-ai --gui -p anthropic ../examples/<pack>

# After run, copy from:
#   examples/<pack>/replication_audit.md
#   results/coefficients.json (in Modal workspace; also surfaced in TUI/GUI)
```

**Update protocol:** After each benchmark run, fill the **Actual** columns, set **Last run**, and note provider model ID from `LLM: …` / audit header. Re-run the same pack 3× before marking a row stable (see [ROADMAP.md](./ROADMAP.md) Now #1).

**CI:** Mocked pack tests (`tests/test_pack_*`, `tests/test_runner_run.py`) assert wiring only — they do not replace live Modal + LLM runs in this document.

---

## Suite summary (primary: Anthropic)

Default provider: `anthropic` (`claude-sonnet-4-6` unless `ANTHROPIC_MODEL` overrides).


| Pack                                                                | Pack target (reference)                           | Published β (SE)   | Expected verdict | Actual verdict | Actual β (SE)    | Rel. dev. | Last run   | Notes                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------- | ------------------ | ---------------- | -------------- | ---------------- | --------- | ---------- | ----------------------------------------------------------------- |
| [card_krueger](../examples/card_krueger/)                           | NJ × Post (1994 Table 3)                          | 2.76 (1.36)        | MATCH            | MATCH          | 2.41 (1.32) †    | — †       | 2026-05-26 | † Run hit 2000 reply `nj_coef_*`, not 1994 Table 3 — re-benchmark |
| [dehejia_wahba](../examples/dehejia_wahba/)                         | `treat` → RE78 (Table 2 Panel C)                  | 1794 (632)         | MATCH            | MATCH          | —                | —         | —          | Fill Actual β from latest audit                                   |
| [imbens_lottery](../examples/imbens_lottery/)                       | Table 2: `prize_on_earnings` (elasticity ≈ −0.11) | −0.11 (elasticity) | MATCH or CLOSE   | **MATCH**      | −0.1145 (elast.) | 4.1%      | 2026-05-27 | Run 3: on-pack MATCH; Docling; see run log                        |
| [angrist_lavy](../examples/angrist_lavy/)                           | Class size IV (5th grade)                         | −0.25 (0.08)       | MATCH or CLOSE   | **CLOSE**      | −0.233 (0.078)   | 6.9%      | 2026-05-27 | Run 1: on-spec; garbled tables; 2SLS correct spec; see run log    |
| [autor_dorn_hanson](../examples/autor_dorn_hanson/)                 | Import exposure → mfg share                       | −0.60 (0.15)       | MATCH or CLOSE   | —              | —                | —         | —          | Not yet run                                                       |
| [acemoglu_johnson_robinson](../examples/acemoglu_johnson_robinson/) | `avexpr` → log GDP                                | 0.94 (0.06)        | MATCH or CLOSE   | —              | —                | —         | —          | Not yet run                                                       |


**Exit criteria (roadmap):** ≥ 4 / 6 packs at **MATCH** on Anthropic **on the pack target estimand**, without per-pack prompt edits.

---

## Run log — imbens_lottery

Recorded run for comparison on re-run. Audit: `[examples/imbens_lottery/replication_audit.md](../examples/imbens_lottery/replication_audit.md)`.

### Run 1 (2026-05-27) — off-pack estimand, auditor MATCH


| Field                  | Pack target (`target_spec_reference.json`)                            | Run 1 actual                                                       |
| ---------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Paper (cited in audit) | Imbens et al. (2001) *AER* 91(4)                                      | NBER WP 7001 (1999)                                                |
| Estimand               | Reduced form: **yearly prize → labor earnings** (Table 2; elasticity) | `**bigwinner` dummy** → earnings year+6 (Table 5, Winners *N*=237) |
| Published benchmark    | Elasticity **≈ −0.11** (modest prizes)                                | Level **−5.0** (approx.; SE n/a in spec)                           |
| Estimated              | —                                                                     | **−4.987 (1.543)**                                                 |
| Implied elasticity     | —                                                                     | **−0.406** (≈ paper **−0.41** for big winners)                     |
| Rel. dev. (level)      | —                                                                     | **0.26%**                                                          |
| Sig.                   | —                                                                     | p<0.01 both                                                        |
| Overall verdict        | MATCH or CLOSE (on pack target)                                       | **MATCH** (on Table 5 bigwinner only)                              |
| Tags                   | —                                                                     | `spec`, `audit-parse` (garbled `paper_tables.json`)                |


**Interpretation:** Numerically tight on the coefficient the agent chose. Does **not** certify the pack’s documented Table 2 / −0.11 headline. Published −5.0 came from `coef_approx` in agent-written `target_specification.json`, not from extracted tables — auditor could not cross-check Table 5 in `paper_tables.json`.

**Re-run goal:** MATCH on **Table 2 modest-prize elasticity ≈ −0.11** (or explicitly document if the data pack only supports Table 5).

### Run 2 (2026-05-27) — on-pack estimand, auditor MISMATCH


| Field                  | Pack target                                                    | Run 2 actual                                                                       |
| ---------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Paper (cited in audit) | Imbens et al. (2001) *AER* 91(4)                               | AER 91(4) (audit citation aligned)                                                 |
| Estimand               | `**prize_on_earnings`** (elasticity, Table 2 / reference JSON) | Same — prize → labor earnings (elasticity)                                         |
| Published benchmark    | **−0.11** (elasticity)                                         | **−0.11** (from `target_spec_reference.json`)                                      |
| Estimated              | —                                                              | **−0.192** (elasticity; avg across years per agent notes)                          |
| Rel. dev.              | —                                                              | **74.7%**                                                                          |
| Sig.                   | not reported (pub)                                             | significant (est, t ≈ −3.2)                                                        |
| Overall verdict        | MATCH or CLOSE                                                 | **MISMATCH**                                                                       |
| Tags                   | —                                                              | `spec` (partial — right estimand, wrong magnitude), `audit-parse` (garbled tables) |


**Interpretation:** Agent tweaks worked for **estimand alignment** — it targeted `prize_on_earnings` and used the reference JSON, not Table 5 bigwinner. Numerically it did **not** hit −0.11: −0.192 is same sign but ~75% off the reference anchor. Audit notes paper may report −0.11 to −0.20 by year; −0.192 is near the top of that range but auditor correctly applied the single −0.11 benchmark → MISMATCH.

If the GUI still shows Run 1 (MATCH / bigwinner), that is a stale session; on-disk audit for runs 1–2 is above. **Latest certified run: Run 3** (on-disk `[replication_audit.md](../examples/imbens_lottery/replication_audit.md)`).

### Run 3 (2026-05-27) — on-pack estimand, auditor MATCH (Docling)


| Field                  | Pack target                                                    | Run 3 actual                                                                                             |
| ---------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Paper (cited in audit) | Imbens et al. (2001) *AER* 91(4)                               | AER 91(4) (aligned)                                                                                      |
| PDF backend            | —                                                              | **Docling** (default host preflight)                                                                     |
| Estimand               | `**prize_on_earnings`** (elasticity; Table 2 / reference JSON) | Same — average reduced-form elasticity, post-win years 1–6, modest-prize sample (*N*=453 per agent spec) |
| Published benchmark    | **−0.11** (elasticity; `target_spec_reference.json`)           | **−0.11** (curator reference; tables still garbled)                                                      |
| Estimated              | —                                                              | **−0.1145** (elasticity; component years p < 0.01)                                                       |
| Rel. dev.              | —                                                              | **4.1%**                                                                                                 |
| Sig.                   | significant (benchmark)                                        | significant (est, all component years p < 0.01)                                                          |
| Overall verdict        | MATCH or CLOSE                                                 | **MATCH**                                                                                                |
| Tags                   | —                                                              | `spec` (on-pack), `audit-parse` (`paper_tables.json` slash/OCR noise; auditor used reference JSON)       |


**Interpretation:** First **on-spec MATCH** for the pack headline. Agent followed `user_message` + reference JSON; estimate −0.1145 is within 5% of −0.11. `paper_tables.json` remains unreadable for Table 4 elasticities (Docling: 15 tables, 0 ragged, but cell OCR artifacts); auditor correctly anchored published values to `target_spec_reference.json`.

**Cost (informal):** GUI/Anthropic runs for this pack are often **~1.5–2×** Card & Krueger — expected, not a bug (see [Cost notes](#cost-notes-imbens-vs-card--krueger) below).

---

## Run log — angrist_lavy

Audit: [`examples/angrist_lavy/replication_audit.md`](../examples/angrist_lavy/replication_audit.md).

### Run 1 (2026-05-27) — on-pack estimand, auditor CLOSE

| Field | Pack target | Run 1 actual |
|-------|-------------|--------------|
| Paper (cited in audit) | Angrist & Lavy (1999) *QJE* 114(2) | QJE 114(2) (aligned) |
| PDF backend | — | Docling (default) |
| Estimand | **`class_size_iv`** (5th grade, 2SLS, Maimonides instrument) | Same — 5th-grade math, 2SLS, Maimonides, controls for tipuach + cohsize, weighted |
| Published benchmark | **−0.25 (0.08)** | −0.25 (0.08) (from `target_spec_reference.json`) |
| Estimated | — | **−0.2327 (0.0777)** |
| Rel. dev. | — | **6.9%** |
| Overall verdict | MATCH or CLOSE | **CLOSE** |
| Tags | — | `audit-parse` (`paper_tables.json` all `["index"]`; tables garbled; benchmark from reference JSON) |

**Interpretation:** First run; correct estimand, correct method, correct instrument. 6.9% relative deviation is just above the 5% MATCH threshold. A second run may tip into MATCH — or adding a `user_message` in `target_spec_reference.json` pinning the exact table column (as done for Imbens) could help.

---

## Per-pack detail

### card_krueger — Card & Krueger (1994) minimum wages


| Field           | Expected                                     | Actual (last run)                              |
| --------------- | -------------------------------------------- | ---------------------------------------------- |
| Paper           | Card & Krueger (1994), *AER* 84(4), Table 3  | Card & Krueger (2000) reply                    |
| Estimand        | β (NJ × Post) on FTE employment              | `nj_coef_no_controls`, `nj_coef_with_controls` |
| Published β     | 2.76                                         | 2.488 / 2.411                                  |
| Published SE    | 1.36                                         | 1.323                                          |
| Overall verdict | MATCH                                        | MATCH                                          |
| Audit path      | `examples/card_krueger/replication_audit.md` | same                                           |


`data.csv` may include a planted bug (`--plant-bug` in data script); clean data required for 1994 Table 3 target.

---

### dehejia_wahba — Dehejia & Wahba (1999) experimental NSW


| Field            | Expected     | Actual           |
| ---------------- | ------------ | ---------------- |
| Coefficient name | `treat_re78` | —                |
| Published β      | 1794.0       | —                |
| Published SE     | 632.0        | —                |
| Overall verdict  | MATCH        | MATCH (reported) |


---

### imbens_lottery — Imbens, Rubin & Sacerdote (2001)


| Field            | Pack target         | Run 1                 | Run 2               | Run 3 (latest on disk)                                                    |
| ---------------- | ------------------- | --------------------- | ------------------- | ------------------------------------------------------------------------- |
| Coefficient name | `prize_on_earnings` | `bigwinner` (Table 5) | `prize_on_earnings` | `prize_on_earnings`                                                       |
| Published β      | −0.11 (elasticity)  | −5.000 (level)        | −0.11 (elasticity)  | −0.11 (elasticity)                                                        |
| Estimated        | —                   | −4.987 (1.543)        | −0.192 (elasticity) | **−0.1145** (elasticity)                                                  |
| Rel. dev.        | —                   | — (wrong scale)       | 74.7%               | **4.1%**                                                                  |
| Overall verdict  | MATCH or CLOSE      | MATCH (off-spec)      | MISMATCH (on-spec)  | **MATCH** (on-spec)                                                       |
| Audit path       | —                   | —                     | —                   | `[replication_audit.md](../examples/imbens_lottery/replication_audit.md)` |


---

### angrist_lavy — Angrist & Lavy (1999) Maimonides rule

| Field            | Expected        | Run 1 (latest on disk)                                                      |
| ---------------- | --------------- | --------------------------------------------------------------------------- |
| Coefficient name | `class_size_iv` | `class_size_iv`                                                             |
| Published β      | −0.25           | −0.2327                                                                     |
| Published SE     | 0.08            | 0.0777                                                                      |
| Rel. dev.        | —               | 6.9%                                                                        |
| Overall verdict  | MATCH or CLOSE  | **CLOSE**                                                                   |
| Audit path       | —               | [`replication_audit.md`](../examples/angrist_lavy/replication_audit.md)     |


---

### autor_dorn_hanson — Autor, Dorn & Hanson (2013) China shock


| Field            | Expected              | Actual |
| ---------------- | --------------------- | ------ |
| Coefficient name | `import_exposure_mfg` | —      |
| Published β      | −0.60                 | —      |
| Published SE     | 0.15                  | —      |
| Overall verdict  | MATCH or CLOSE        | —      |


---

### acemoglu_johnson_robinson — Acemoglu, Johnson & Robinson (2001)


| Field            | Expected             | Actual |
| ---------------- | -------------------- | ------ |
| Coefficient name | `avexpr_on_logpgp95` | —      |
| Published β      | 0.94                 | —      |
| Published SE     | 0.06                 | —      |
| Overall verdict  | MATCH or CLOSE       | —      |


---

## Multi-provider matrix (optional)


| Pack                      | Anthropic           | Cloudflare Kimi | Cloudflare GLM | Gemini | Groq |
| ------------------------- | ------------------- | --------------- | -------------- | ------ | ---- |
| card_krueger              | MATCH †             | —               | —              | —      | —    |
| dehejia_wahba             | MATCH               | —               | —              | —      | —    |
| imbens_lottery            | **MATCH** (run 3) ‡ | —               | —              | —      | —    |
| angrist_lavy              | **CLOSE** (run 1) § | —               | —              | —      | —    |
| autor_dorn_hanson         | —                   | —               | —              | —      | —    |
| acemoglu_johnson_robinson | —                   | —               | —              | —      | —    |


‡ Run 1: MATCH on Table 5 bigwinner (off-spec). Run 2: MISMATCH on `prize_on_earnings` (−0.192 vs −0.11). Run 3: **MATCH** on `prize_on_earnings` (−0.1145 vs −0.11, 4.1%).

§ Run 1: CLOSE on `class_size_iv` (−0.233 vs −0.25, 6.9%); correct 2SLS spec, garbled tables, benchmark from reference JSON.

---

## Cost notes (Imbens vs Card & Krueger)

ReplicateAI does not yet log per-run USD in the audit. If your provider dashboard shows Imbens at **~1.5–2×** Card & Krueger, that is **normal** for this harness:


| Factor                   | Card & Krueger             | Imbens lottery                                              |
| ------------------------ | -------------------------- | ----------------------------------------------------------- |
| PDF / `paper_text.md`    | ~26 pages, ~127k chars     | ~~60 pages, ~205k chars (~~1.6× text)                       |
| Estimand complexity      | Single DiD / WLS table row | Multi-year elasticity, sample rules (modest vs all winners) |
| Typical agent work       | One main regression script | More specification search, year loops, subsample logic      |
| Host preflight (Docling) | Shorter PDF                | Longer PDF (~2× pages); **not** billed as LLM tokens        |


Docling adds **host CPU time** on first run (model download), not duplicate LLM turns. Most of the cost gap is **larger paper context + harder estimand**, not the PDF backend choice alone.

---

## Agent / pack lessons (from imbens runs)


| Issue                                          | Suggested tweak                                                                                                                                                                                                                       |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agent picks a different table than pack README | Seed `target_spec_reference.json`; use `resolve_user_message()` (default is method-agnostic; optional `user_message` in reference JSON or `user_message.txt` per pack)                                                                |
| Default message assumed DiD for all papers     | Replaced `DEFAULT_USER_MESSAGE` — no longer prescribes DiD; points at reference JSON and paper method                                                                                                                                 |
| `paper_tables.json` useless for this PDF       | Docling improves structure (15 tables, 0 ragged) but AER scan cells can still be OCR-garbled; pack README + `target_spec_reference.json` + `user_message` remain essential; auditor should cite reference JSON when tables unreadable |
| Run 3: on-spec MATCH after pack message        | `user_message` in reference JSON + method-agnostic default message — agent hit −0.1145 vs −0.11 (4.1%)                                                                                                                                |
| Auditor MATCH on agent-supplied `coef_approx`  | Auditor prompt: require published column to cite `paper_tables.json` or `target_spec_reference.json` path; downgrade to CLOSE if only `coef_approx` in runtime spec                                                                   |
| Pack reference out of date                     | Update `target_spec_reference.json` after a deliberate choice of headline estimand                                                                                                                                                    |


---

## Failure taxonomy (tag in Notes)


| Tag           | Meaning                                                            |
| ------------- | ------------------------------------------------------------------ |
| `spec`        | Wrong equation / sample / table row in `target_specification.json` |
| `data`        | CSV build, merge, or variable coding error                         |
| `code`        | Estimation script bug or library misuse                            |
| `audit-parse` | Auditor misread coeffs or published table                          |
| `timeout`     | Modal or agent time limit                                          |
| `cost`        | Run aborted for cost                                               |


---

## Related documents


| Document                                    | Role                                                 |
| ------------------------------------------- | ---------------------------------------------------- |
| [examples/README.md](../examples/README.md) | Pack layout and setup                                |
| [ROADMAP.md](./ROADMAP.md)                  | Benchmark goals and future `BENCHMARK.md` automation |
| [DESIGN.md](./DESIGN.md)                    | Auditor rubric and `/workspace` contract             |


