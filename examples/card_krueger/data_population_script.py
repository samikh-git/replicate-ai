#!/usr/bin/env python3
"""Build example inputs for ReplicateAI from the Card & Krueger NJ–PA survey.

Reads ``njmin/public.dat`` (or ``public.dat`` inside ``njmin.zip``) and writes
``data.csv`` in this directory. The paper is ``card_krueger.pdf`` (Card & Krueger
1994). ``replicate-ai`` copies both into ``/workspace/`` as ``paper.pdf`` and
``data.csv``.

Usage (from repo root or this directory):

    uv run --directory replicate_ai python ../examples/card_krueger/data_population_script.py
    uv run --directory replicate_ai python ../examples/card_krueger/data_population_script.py --plant-bug nbsp
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# Variable order from njmin/check.sas (46 fields; matches public.dat columns).
COLUMN_NAMES: list[str] = [
    "sheet",
    "chain",
    "co_owned",
    "state",
    "southj",
    "centralj",
    "northj",
    "pa1",
    "pa2",
    "shore",
    "ncalls",
    "empft",
    "emppt",
    "nmgrs",
    "wage_st",
    "inctime",
    "firstinc",
    "bonus",
    "pctaff",
    "meal",
    "open",
    "hrsopen",
    "psoda",
    "pfry",
    "pentree",
    "nregs",
    "nregs11",
    "type2",
    "status2",
    "date2",
    "ncalls2",
    "empft2",
    "emppt2",
    "nmgrs2",
    "wage_st2",
    "inctime2",
    "firstin2",
    "special2",
    "meals2",
    "open2r",
    "hrsopen2",
    "psoda2",
    "pfry2",
    "pentree2",
    "nregs2",
    "nregs112",
]

EXAMPLE_DIR = Path(__file__).resolve().parent
DEFAULT_DAT = EXAMPLE_DIR / "njmin" / "public.dat"
DEFAULT_ZIP = EXAMPLE_DIR / "njmin.zip"
DEFAULT_OUTPUT = EXAMPLE_DIR / "data.csv"

PlantBug = str  # "none" | "nbsp" | "encoding" | "date"


def _read_public_dat_from_zip(zip_path: Path, member: str = "public.dat") -> pd.DataFrame:
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        # Accept public.dat at zip root or under njmin/
        candidates = [member, f"njmin/{member}"]
        chosen = next((n for n in candidates if n in names), None)
        if chosen is None:
            flat = [n for n in names if n.endswith(member)]
            if len(flat) != 1:
                raise KeyError(
                    f"{member!r} not found in {zip_path} (tried {candidates})"
                )
            chosen = flat[0]
        with z.open(chosen) as f:
            return _parse_dat_stream(f)


def _parse_dat_stream(file_obj) -> pd.DataFrame:
    df = pd.read_csv(
        file_obj,
        sep=r"\s+",
        header=None,
        names=COLUMN_NAMES,
        engine="python",
    )
    df.replace(".", np.nan, inplace=True)
    return df.apply(pd.to_numeric, errors="coerce")


def load_public_dat(*, dat_path: Path | None, zip_path: Path | None) -> pd.DataFrame:
    if dat_path is not None:
        if not dat_path.is_file():
            raise FileNotFoundError(f"Data file not found: {dat_path}")
        with open(dat_path, "rb") as f:
            return _parse_dat_stream(f)
    if zip_path is not None:
        if not zip_path.is_file():
            raise FileNotFoundError(f"Zip archive not found: {zip_path}")
        return _read_public_dat_from_zip(zip_path)
    if DEFAULT_DAT.is_file():
        with open(DEFAULT_DAT, "rb") as f:
            return _parse_dat_stream(f)
    if DEFAULT_ZIP.is_file():
        return _read_public_dat_from_zip(DEFAULT_ZIP)
    raise FileNotFoundError(
        f"No data source found. Expected {DEFAULT_DAT} or {DEFAULT_ZIP}. "
        "Download njmin.zip from the Card & Krueger replication page and extract "
        "to njmin/, or pass --zip-path."
    )


def apply_planted_bug(df: pd.DataFrame, bug: PlantBug) -> pd.DataFrame:
    """Introduce one demo bug so attempt_01.py fails (see docs/DESIGN.md §8.1)."""
    if bug == "none":
        return df
    if bug == "nbsp":
        # Literal df["wage_st"] raises KeyError; visible in pd.read_csv columns.
        df = df.rename(columns={"wage_st": "wage_st\u00a0"})
        return df
    if bug == "encoding":
        # Caller must write with encoding="latin-1"; default utf-8 read fails.
        return df
    if bug == "date":
        # DATE2 stays as MMDDYY integers; needs format= in pd.to_datetime.
        return df
    raise ValueError(f"Unknown plant-bug: {bug!r}")


def write_data_csv(
    df: pd.DataFrame,
    output_path: Path,
    *,
    plant_bug: PlantBug,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if plant_bug == "encoding":
        # Latin-1 byte in a header cell breaks utf-8 pd.read_csv().
        df = df.copy()
        # é in latin-1 (0xe9) is invalid as a lone byte in utf-8.
        df.columns = [
            c.replace("state", "st\xe9te", 1) if c == "state" else c for c in df.columns
        ]
        df.to_csv(output_path, index=False, encoding="latin-1")
    else:
        df.to_csv(output_path, index=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Card & Krueger public.dat to data.csv for ReplicateAI.",
    )
    parser.add_argument(
        "--dat-path",
        type=Path,
        default=None,
        help=f"Path to public.dat (default: {DEFAULT_DAT.relative_to(EXAMPLE_DIR)})",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        default=None,
        help="Path to njmin.zip (used if public.dat is missing)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT.name} in example dir)",
    )
    parser.add_argument(
        "--alias",
        action="store_true",
        help="Also write card_krueger.csv (same contents as data.csv)",
    )
    parser.add_argument(
        "--plant-bug",
        choices=("none", "nbsp", "encoding", "date"),
        default="nbsp",
        help=(
            "Demo trap in data.csv (default: nbsp). "
            "'date' leaves MMDDYY integers; 'encoding' writes latin-1 CSV."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        df = load_public_dat(dat_path=args.dat_path, zip_path=args.zip_path)
    except (FileNotFoundError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    df = apply_planted_bug(df, args.plant_bug)
    write_data_csv(df, args.output.resolve(), plant_bug=args.plant_bug)

    if args.alias:
        alias_path = args.output.resolve().parent / "card_krueger.csv"
        write_data_csv(df, alias_path, plant_bug=args.plant_bug)

    n_rows, n_cols = df.shape
    print(f"Wrote {args.output.resolve()} ({n_rows} rows, {n_cols} columns).")
    if args.plant_bug != "none":
        print(f"Planted bug: {args.plant_bug} (see docs/DESIGN.md §8.1).")
    if not (EXAMPLE_DIR / "card_krueger.pdf").is_file():
        print(
            "Warning: card_krueger.pdf missing — add the Card & Krueger (1994) "
            "paper PDF before running replicate-ai."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
