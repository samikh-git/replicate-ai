# ReplicateAI example packs

Each subdirectory is a self-contained paper + dataset bundle for `replicate-ai`.

## Layout

```
examples/<name>/
  README.md                    # paper, headline coefficient, setup
  data_population_script.py    # fetch raw data → data.csv
  data.csv                     # produced by the script (committed when small)
  paper.pdf                    # you add the PDF (not redistributed here)
  target_spec_reference.json   # published targets for the auditor (reference)
```

Run replication:

```bash
cd replicate_ai
uv run replicate-ai ../examples/<name>
```

## Example packs

| Directory | Paper | Difficulty |
|-----------|--------|------------|
| [card_krueger](card_krueger/) | Card & Krueger (1994) minimum wages | Demo (planted bug optional) |
| [dehejia_wahba](dehejia_wahba/) | Dehejia & Wahba (1999) / LaLonde NSW | Easy |
| [imbens_lottery](imbens_lottery/) | Imbens, Rubin & Sacerdote (2001) lottery income | Easy–medium |
| [angrist_lavy](angrist_lavy/) | Angrist & Lavy (1999) class size (Maimonides) | Medium |
| [autor_dorn_hanson](autor_dorn_hanson/) | Autor, Dorn & Hanson (2013) China shock | Medium–hard |
| [acemoglu_johnson_robinson](acemoglu_johnson_robinson/) | Acemoglu, Johnson & Robinson (2001) institutions | Hard |

## Setup checklist

1. `uv run --directory replicate_ai python ../examples/<name>/data_population_script.py`
2. Add `paper.pdf` (or `<dirname>.pdf`) — links in each README
3. `uv run replicate-ai ../examples/<name>`

Use `--skip-pdf-extract` on reruns after the first successful PDF preflight.

## Paper links (official)

| Pack | Published article | Open / author PDF |
|------|-------------------|-------------------|
| [card_krueger](card_krueger/) | [AER (DOI)](https://doi.org/10.1257/aer.84.4.772) · [AEA page](https://www.aeaweb.org/articles?id=10.1257/aer.84.4.772) | [NBER w4509](https://www.nber.org/papers/w4509) |
| [dehejia_wahba](dehejia_wahba/) | [JASA (DOI)](https://doi.org/10.1080/01621459.1999.10473858) | [Dehejia PDF](https://users.nber.org/~rdehejia/papers/dehejia_wahba_jasa.pdf) · [NBER w6586](https://www.nber.org/papers/w6586) |
| [imbens_lottery](imbens_lottery/) | [AER (DOI)](https://doi.org/10.1257/aer.91.4.778) · [AEA page](https://www.aeaweb.org/articles?id=10.1257/aer.91.4.778) | [NBER w7001](https://www.nber.org/papers/w7001) |
| [angrist_lavy](angrist_lavy/) | [QJE (DOI)](https://doi.org/10.1162/003355399556089) | [NBER w5888](https://www.nber.org/papers/w5888) |
| [autor_dorn_hanson](autor_dorn_hanson/) | [AER (DOI)](https://doi.org/10.1257/aer.103.6.2121) · [AEA page](https://www.aeaweb.org/articles?id=10.1257/aer.103.6.2121) | [Dorn PDF](http://www.ddorn.net/papers/Autor-Dorn-Hanson-ChinaSyndrome.pdf) |
| [acemoglu_johnson_robinson](acemoglu_johnson_robinson/) | [AER (DOI)](https://doi.org/10.1257/aer.91.5.1369) · [AEA page](https://www.aeaweb.org/articles?id=10.1257/aer.91.5.1369) | — (use journal / institutional access) |

Related (data only): LaLonde (1986), [AER (DOI)](https://doi.org/10.1257/aer.76.4.604) — underlying NSW experiment for `dehejia_wahba`.
