# Card & Krueger (1994) example

See [../README.md](../README.md) for the full list of example packs.

| File | Role |
|------|------|
| `card_krueger.pdf` | Paper (seeded as `/workspace/paper.pdf`) |
| `data.csv` | NJ–PA survey data with planted demo bug (seeded as `/workspace/data.csv`) |
| `njmin/` | Original `public.dat`, codebook, and SAS check program |
| `data_population_script.py` | Rebuild `data.csv` from `njmin/public.dat` |

**Paper:** Card, D., & Krueger, A. B. (1994). Minimum wages and employment. *AER* 84(4), 772–793.

### Paper links

- **Published:** [https://doi.org/10.1257/aer.84.4.772](https://doi.org/10.1257/aer.84.4.772) · [AEA article page](https://www.aeaweb.org/articles?id=10.1257/aer.84.4.772)
- **Working paper:** [NBER w4509](https://www.nber.org/papers/w4509)

```bash
cd replicate_ai
uv run replicate-ai ../examples/card_krueger
```

Regenerate data:

```bash
uv run python ../examples/card_krueger/data_population_script.py
```
