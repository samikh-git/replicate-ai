#!/usr/bin/env python3
"""Download Dehejia–Wahba NSW subset and write data.csv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXAMPLE_DIR.parent))

from _common import download_file, stata_to_csv  # noqa: E402

NSW_DW_URL = "https://users.nber.org/~rdehejia/data/nsw_dw.dta"
DEFAULT_RAW = EXAMPLE_DIR / "raw" / "nsw_dw.dta"
DEFAULT_OUTPUT = EXAMPLE_DIR / "data.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=NSW_DW_URL,
        help="URL for nsw_dw.dta",
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW,
        help="Where to save the downloaded .dta",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output CSV path",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Use existing --raw file only",
    )
    args = parser.parse_args(argv)

    if not args.skip_download or not args.raw.is_file():
        print(f"Downloading {args.url} …")
        download_file(args.url, args.raw)

    n = stata_to_csv(args.raw.resolve(), args.output.resolve())
    print(f"Wrote {args.output.resolve()} ({n} rows).")
    if not (EXAMPLE_DIR / "paper.pdf").is_file():
        print("Next: add paper.pdf (Dehejia & Wahba 1999 JASA).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
