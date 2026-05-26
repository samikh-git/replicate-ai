"""Shared helpers for example-pack data_population_script.py files."""

from __future__ import annotations

import shutil
import sys
import urllib.request
from pathlib import Path


def download_file(url: str, dest: Path, *, timeout: float = 120.0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "replicate-ai-examples/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def require_pandas():
    try:
        import pandas as pd  # noqa: F401

        return pd
    except ImportError as e:
        print(
            "pandas is required. Run from replicate_ai:\n"
            "  uv run --directory replicate_ai python <script>",
            file=sys.stderr,
        )
        raise SystemExit(1) from e


def stata_to_csv(stata_path: Path, csv_path: Path) -> int:
    pd = require_pandas()
    df = pd.read_stata(stata_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return len(df)


def rdata_to_csv(rdata_path: Path, csv_path: Path, object_name: str | None = None) -> int:
    pd = require_pandas()
    try:
        import rdata
    except ImportError as e:
        print(
            "Install rdata to convert .RData:\n"
            "  uv pip install rdata",
            file=sys.stderr,
        )
        raise SystemExit(1) from e

    parsed = rdata.parser.parse_file(rdata_path)
    converted = rdata.conversion.convert(parsed)
    if object_name is not None:
        df = converted[object_name]
    elif len(converted) == 1:
        df = next(iter(converted.values()))
    else:
        names = ", ".join(sorted(converted))
        raise ValueError(f"Multiple objects in {rdata_path}: {names}. Pass object_name=.")

    if not hasattr(df, "to_csv"):
        raise TypeError(f"Expected a DataFrame-like object, got {type(df)}")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return len(df)


def copy_if_exists(src: Path, dest: Path) -> bool:
    if not src.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True
