# ReplicateAI example packs

Each subdirectory is a self-contained paper + dataset bundle for `replicate-ai`.

## Layout

```
examples/<name>/
  README.md                    # paper, headline coefficient, setup
  data_population_script.py    # fetch raw data → data.csv
  data.csv                     # produced by the script (committed when small)
  paper.pdf                    # you add the PDF (not redistributed here)
  target_spec_reference.json   # published targets; optional "user_message" for the agent
  user_message.txt             # optional; overrides default run message for this pack
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
| [imbens_lottery](imbens_lottery/) | Imbens, Rubin & Sacerdote (2001) lottery income (pinned IRS microdata via [lalonde](https://github.com/xuyiqing/lalonde)) | Easy–medium |
| [angrist_lavy](angrist_lavy/) | Angrist & Lavy (1999) class size (Maimonides) | Medium |
| [autor_dorn_hanson](autor_dorn_hanson/) | Autor, Dorn & Hanson (2013) China shock | Medium–hard |
| [acemoglu_johnson_robinson](acemoglu_johnson_robinson/) | Acemoglu, Johnson & Robinson (2001) institutions | Hard |

## Setup checklist

1. `uv run --directory replicate_ai python ../examples/<name>/data_population_script.py`
2. Add `paper.pdf` (or `<dirname>.pdf`) — links in each README
3. `uv run replicate-ai ../examples/<name>`

PDF preflight runs on the host with **Docling** by default (`paper_text.md`, `paper_tables.json` uploaded to Modal). First run downloads layout weights from Hugging Face. Use `--pdf-backend legacy` for pymupdf4llm + Camelot; `--skip-pdf-extract` on reruns after a successful extract.

**Note on scanned PDFs:** Older papers (pre-2000 AER, some QJE issues) are bitmap scans rather than text-layer PDFs. `paper_tables.json` cells may be garbled or reduced to `["index"]`; `paper_text.md` is typically usable. The agent falls back to `paper_text.md` + `target_spec_reference.json` when tables are unreadable — include a `user_message` field in `target_spec_reference.json` to keep it on-target (see `imbens_lottery` for an example). Set `REPLICATE_AI_PDF_OCR=true` to enable OCR on image-only PDFs (slower; downloads additional model weights).

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
