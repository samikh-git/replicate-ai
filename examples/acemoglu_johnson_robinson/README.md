# Acemoglu, Johnson & Robinson (2001) — Colonial origins

| File | Role |
|------|------|
| `paper.pdf` | AER paper (you provide) |
| `data.csv` | Cross-country replication dataset |
| `data_population_script.py` | Downloads MIT replication `.dta` |

Paper: Acemoglu, D., Johnson, S., & Robinson, J. A. (2001). The colonial origins of comparative development: An empirical investigation. *American Economic Review*, 91(5), 1369–1401.

### Paper links

- Published: [https://doi.org/10.1257/aer.91.5.1369](https://doi.org/10.1257/aer.91.5.1369) · [AEA article page](https://www.aeaweb.org/articles?id=10.1257/aer.91.5.1369)
- Replication package: [openICPSR E112564](https://doi.org/10.3886/E112564V1) (2012 reply; includes AJR data/code)
- Data archive: [Acemoglu MIT](https://economics.mit.edu/people/faculty/daron-acemoglu/data-archive)

Headline target: Institutions (`avexpr`) → log income (`logpgp95`) — Table 2, column (1) OLS coefficient ≈ 0.94 (SE ≈ 0.06).

Method: Cross-country OLS; IV extension uses settler mortality (Table 4).

## Setup

```bash
uv run --directory replicate_ai python ../examples/acemoglu_johnson_robinson/data_population_script.py
```

Add `paper.pdf` (AEA/journal access; links above), then:

```bash
cd replicate_ai
uv run replicate-ai ../examples/acemoglu_johnson_robinson
```

Data source: [Acemoglu MIT data archive](https://economics.mit.edu/people/faculty/daron-acemoglu/data-archive) — `20100816_replication_dataset.dta`.

Note: Albouy (2012) and related critiques apply; expect borderline or MISMATCH unless the agent matches AJR’s exact sample rules.
