# Imbens, Rubin & Sacerdote (2001) — Lottery income

| File | Role |
|------|------|
| `paper.pdf` | AER 91(4) paper (you provide) |
| `data.csv` | Massachusetts lottery survey (496 respondents) |
| `data_population_script.py` | Downloads pinned `lottery.RData` and writes `data.csv` |
| `target_spec_reference.json` | Published benchmark + **column map** for `data.csv` |

Paper: Imbens, G. W., Rubin, D. B., & Sacerdote, B. I. (2001). Estimating the effect of unearned income on labor earnings, savings, and consumption. *American Economic Review*, 91(4), 778–794.

### Paper links

- Published: [https://doi.org/10.1257/aer.91.4.778](https://doi.org/10.1257/aer.91.4.778) · [AEA article page](https://www.aeaweb.org/articles?id=10.1257/aer.91.4.778)
- Working paper: [NBER w7001](https://www.nber.org/papers/w7001) · [DOI 10.3386/w7001](https://doi.org/10.3386/w7001)
- JSTOR: [stable URL](https://www.jstor.org/stable/2677812)

Headline target: Effect of yearly prize amount on labor earnings (reduced-form; modest prizes). Published elasticity ≈ −0.11 (Table 2 / discussion); levels depend on specification.

Method: OLS / reduced-form of earnings on prize size among lottery players (see paper for subsamples and log/elasticity definitions).

## Data provenance

The microdata are the **original 2001 IRS survey** (Massachusetts Megabucks, mid-1980s), not a new sample collected for Imbens & Xu (2024). That paper’s [GitHub repo](https://github.com/xuyiqing/lalonde) hosts the file for teaching and lists:

> Data provided by Guido Imbens — [source.txt](https://github.com/xuyiqing/lalonde/blob/main/data/irs/source.txt)

| Check | Value |
|-------|--------|
| N | 496 |
| Controls (`winner==0`) | 259 (small one-time prizes) |
| Major-prize winners (`winner==1`) | 237 (43 `bigwinner`, 194 small winners) |

We download `data/irs/lottery.RData` and pin its SHA-256 in `data_population_script.py` so upstream changes do not silently alter the example pack.

Variable definitions: [lottery_keybook.csv](https://github.com/xuyiqing/lalonde/blob/main/data/irs/lottery_keybook.csv) (also summarized in `target_spec_reference.json` → `data_columns`).

### Key columns in `data.csv`

| Column | Meaning |
|--------|---------|
| `yearlpr` | Annual lottery prize (treatment intensity) |
| `yearn.1` … `yearn.7` | Labor earnings win year (t=0) through six years post-win |
| `xearn.1` … `xearn.6` | Pre-win labor earnings (six years before win) |
| `winner` | 1 = major-prize winner; 0 = control |
| `bigwinner` | 1 = large prize winner (43 obs) |
| `male`, `workthen`, `tixbot`, `agew`, `educ` | Covariates |

Replication agents should use these names (not abstract `yearly_prize` / `labor_earnings` aliases).

## Setup

```bash
uv run pip install rdata   # once, for .RData conversion
uv run --directory replicate_ai python ../examples/imbens_lottery/data_population_script.py
```

Add `paper.pdf` (links above), then:

```bash
cd replicate_ai
uv run replicate-ai ../examples/imbens_lottery
```

To refresh data after an intentional upstream change, re-download and update `LOTTERY_RDATA_SHA256` in `data_population_script.py` (or pass `--no-verify-sha256` temporarily).
