#!/usr/bin/env python3
"""Download IRS lottery data and write data.csv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXAMPLE_DIR.parent))

from _common import download_file, rdata_to_csv, verify_file_sha256  # noqa: E402

# 2001 survey (Imbens–Rubin–Sacerdote); redistributed via Imbens & Xu (2024) lalonde repo.
LOTTERY_RDATA_URL = (
    "https://raw.githubusercontent.com/xuyiqing/lalonde/main/data/irs/lottery.RData"
)
# Pin file bytes (git blob e12d3b2c on xuyiqing/lalonde main as of pack setup).
LOTTERY_RDATA_SHA256 = "1014702bfdf33740bdca7caeef0dba913f229082595cd3742769b302cad0b7f4"
DEFAULT_RAW = EXAMPLE_DIR / "raw" / "lottery.RData"
DEFAULT_OUTPUT = EXAMPLE_DIR / "data.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=LOTTERY_RDATA_URL)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument(
        "--no-verify-sha256",
        action="store_true",
        help="Skip SHA-256 check (not recommended for reproducible packs).",
    )
    args = parser.parse_args(argv)

    if not args.skip_download or not args.raw.is_file():
        print(f"Downloading {args.url} …")
        download_file(args.url, args.raw)

    if not args.no_verify_sha256:
        verify_file_sha256(args.raw.resolve(), LOTTERY_RDATA_SHA256)

    n = rdata_to_csv(args.raw.resolve(), args.output.resolve())
    print(f"Wrote {args.output.resolve()} ({n} rows).")
    if not (EXAMPLE_DIR / "paper.pdf").is_file():
        print("Next: add paper.pdf (Imbens, Rubin & Sacerdote 2001 AER).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
