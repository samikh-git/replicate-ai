# Angrist & Lavy (1999) — Class size (Maimonides’ rule)

| File | Role |
|------|------|
| `paper.pdf` | QJE paper (you provide) |
| `data.csv` | 5th-grade class-level data (`final5.dta`) |
| `data_population_script.py` | Downloads MIT replication file |

Paper: Angrist, J. D., & Lavy, V. (1999). Using Maimonides’ rule to estimate the effect of class size on scholastic achievement. *Quarterly Journal of Economics*, 114(2), 533–575.

### Paper links

- Published: [https://doi.org/10.1162/003355399556089](https://doi.org/10.1162/003355399556089) · [OUP / QJE](https://academic.oup.com/qje/article-abstract/114/2/533/1583777)
- Working paper: [NBER w5888](https://www.nber.org/papers/w5888) · [DOI 10.3386/w5888](https://doi.org/10.3386/w5888)
- SSRN: [abstract 225670](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=225670)

Headline target: Effect of class size on average test score (5th grade, IV using Maimonides rule) — see Table II, column (1) or similar; published coefficient often negative and significant for 5th graders.

Method: 2SLS / fuzzy RD: enrollment caps induce instrument for class size.

## Setup

```bash
uv run --directory replicate_ai python ../examples/angrist_lavy/data_population_script.py
```

Add `paper.pdf` (links above), then:

```bash
cd replicate_ai
uv run replicate-ai ../examples/angrist_lavy
```

Data source: [Angrist Data Archive](https://economics.mit.edu/people/faculty/josh-angrist/angrist-data-archive) — `final5.dta`.
