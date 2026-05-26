# Imbens, Rubin & Sacerdote (2001) — Lottery income

| File | Role |
|------|------|
| `paper.pdf` | AER 91(4) paper (you provide) |
| `data.csv` | Massachusetts lottery survey |
| `data_population_script.py` | Downloads `lottery.RData` and writes `data.csv` |

**Paper:** Imbens, G. W., Rubin, D. B., & Sacerdote, B. I. (2001). Estimating the effect of unearned income on labor earnings, savings, and consumption. *American Economic Review*, 91(4), 778–794.

### Paper links

- **Published:** [https://doi.org/10.1257/aer.91.4.778](https://doi.org/10.1257/aer.91.4.778) · [AEA article page](https://www.aeaweb.org/articles?id=10.1257/aer.91.4.778)
- **Working paper:** [NBER w7001](https://www.nber.org/papers/w7001) · [DOI 10.3386/w7001](https://doi.org/10.3386/w7001)
- **JSTOR:** [stable URL](https://www.jstor.org/stable/2677812)

**Headline target:** Effect of **yearly prize amount** on **labor earnings** (reduced-form; modest prizes). Published elasticity ≈ **−0.11** (Table 2 / discussion); levels depend on specification.

**Method:** OLS / reduced-form of earnings on prize size among lottery players.

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

**Data source:** [Imbens & Xu tutorial repo](https://github.com/xuyiqing/lalonde) (`data/irs/lottery.RData`), derived from the IRS 2001 survey.
