# Dehejia & Wahba (1999) — LaLonde NSW experimental sample

| File | Role |
|------|------|
| `paper.pdf` | JASA paper (you provide; see below) |
| `data.csv` | Dehejia–Wahba NSW subset (`nsw_dw`) |
| `data_population_script.py` | Downloads `nsw_dw.dta` and writes `data.csv` |

Paper: Dehejia, R. H., & Wahba, S. (1999). Causal effects in non-experimental studies: Reevaluating the evaluation of training programs. *Journal of the American Statistical Association*, 94(448), 1053–1062.

### Paper links

- Published: [https://doi.org/10.1080/01621459.1999.10473858](https://doi.org/10.1080/01621459.1999.10473858) · [Taylor & Francis](https://www.tandfonline.com/doi/abs/10.1080/01621459.1999.10473858)
- Author PDF: [Dehejia (NBER host)](https://users.nber.org/~rdehejia/papers/dehejia_wahba_jasa.pdf)
- Working paper: [NBER w6586](https://www.nber.org/papers/w6586) · [DOI 10.3386/w6586](https://doi.org/10.3386/w6586)
- Underlying experiment: LaLonde (1986) [AER](https://doi.org/10.1257/aer.76.4.604)

Headline target: Experimental treatment effect on RE78 (1978 earnings) — Table 2, Panel C, difference in means ≈ 1794 (SE ≈ 632).

Method: Simple experimental comparison (treated NSW vs control NSW). No CPS/PSID pseudo-experiment in v1.

## Setup

```bash
uv run --directory replicate_ai python ../examples/dehejia_wahba/data_population_script.py
```

Add a PDF as `paper.pdf` (links above).

```bash
cd replicate_ai
uv run replicate-ai ../examples/dehejia_wahba
```

Data source: [Rajeev Dehejia — NSW data](https://users.nber.org/~rdehejia/nswdata2.html) (`nsw_dw.dta`).
