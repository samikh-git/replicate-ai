# Autor, Dorn & Hanson (2013) — China shock

| File | Role |
|------|------|
| `paper.pdf` | AER paper (you provide) |
| `data.csv` | CZ-level workfile (`workfile_china.dta`) |
| `data_population_script.py` | Downloads ADH file archive zip, extracts workfile |

Paper: Autor, D. H., Dorn, D., & Hanson, G. H. (2013). The China syndrome: Local labor market effects of import competition in the United States. *American Economic Review*, 103(6), 2121–2168.

### Paper links

- Published: [https://doi.org/10.1257/aer.103.6.2121](https://doi.org/10.1257/aer.103.6.2121) · [AEA article page](https://www.aeaweb.org/articles?id=10.1257/aer.103.6.2121)
- Author PDF: [Dorn — China Syndrome](http://www.ddorn.net/papers/Autor-Dorn-Hanson-ChinaSyndrome.pdf)
- Replication package: [openICPSR E112670](https://doi.org/10.3886/E112670V1)

Headline target: Effect of Chinese import exposure on manufacturing employment share (long differences, Table 3) — coefficient often ≈ −0.6 per log-point of exposure (verify table/column).

Method: Commuting-zone regressions with import penetration; may use 2SLS.

## Setup

```bash
uv run --directory replicate_ai python ../examples/autor_dorn_hanson/data_population_script.py
```

This downloads ~15MB from [ddorn.net](http://www.ddorn.net/data.htm) (`Autor-Dorn-Hanson-ChinaSyndrome-FileArchive.zip`).

Add `paper.pdf` (links above), then:

```bash
cd replicate_ai
uv run replicate-ai ../examples/autor_dorn_hanson
```

Alternate source: [AEA openICPSR E112670](https://doi.org/10.3886/E112670V1) (manual download if the script fails).
