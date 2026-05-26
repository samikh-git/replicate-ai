#!/usr/bin/env python3
"""Download ADH (2013) replication archive and extract workfile_china.dta → data.csv."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXAMPLE_DIR.parent))

from _common import download_file, stata_to_csv  # noqa: E402

ARCHIVE_URL = "http://www.ddorn.net/data/Autor-Dorn-Hanson-ChinaSyndrome-FileArchive.zip"
WORKFILE_IN_ZIP = (
    "Autor-Dorn-Hanson-ChinaSyndrome-FileArchive/dta/workfile_china.dta"
)
DEFAULT_ZIP = EXAMPLE_DIR / "raw" / "adh_china_syndrome.zip"
DEFAULT_RAW = EXAMPLE_DIR / "raw" / "workfile_china.dta"
DEFAULT_OUTPUT = EXAMPLE_DIR / "data.csv"


def extract_workfile(zip_path: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if WORKFILE_IN_ZIP in names:
            chosen = WORKFILE_IN_ZIP
        else:
            matches = [n for n in names if n.endswith("workfile_china.dta")]
            if len(matches) != 1:
                raise KeyError(
                    f"workfile_china.dta not found in {zip_path} "
                    f"(candidates: {matches[:5]})"
                )
            chosen = matches[0]
        dest.write_bytes(zf.read(chosen))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=ARCHIVE_URL)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args(argv)

    if not args.skip_download or not args.zip.is_file():
        print(f"Downloading {args.url} (this may take a minute) …")
        download_file(args.url, args.zip, timeout=300.0)

    if not args.raw.is_file():
        print(f"Extracting {WORKFILE_IN_ZIP} …")
        extract_workfile(args.zip.resolve(), args.raw.resolve())

    n = stata_to_csv(args.raw.resolve(), args.output.resolve())
    print(f"Wrote {args.output.resolve()} ({n} rows).")
    if not (EXAMPLE_DIR / "paper.pdf").is_file():
        print("Next: add paper.pdf (Autor, Dorn & Hanson 2013 AER).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
