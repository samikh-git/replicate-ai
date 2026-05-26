"""Resolve paper PDF and data CSV paths inside an example pack directory."""

from __future__ import annotations

from pathlib import Path

# Legacy name kept for card_krueger.
_LEGACY_PDF_NAMES = ("card_krueger.pdf",)


def find_example_pdf(example_dir: Path) -> Path | None:
    """Return the paper PDF for an example directory, if present."""
    directory = example_dir.resolve()
    candidates = [
        directory / "paper.pdf",
        directory / f"{directory.name}.pdf",
        *(directory / name for name in _LEGACY_PDF_NAMES),
    ]
    for path in candidates:
        if path.is_file():
            return path
    pdfs = sorted(directory.glob("*.pdf"))
    if len(pdfs) == 1:
        return pdfs[0]
    return None


def find_example_data_csv(example_dir: Path) -> Path | None:
    """Return the dataset CSV for an example directory, if present."""
    directory = example_dir.resolve()
    candidates = [
        directory / "data.csv",
        directory / f"{directory.name}.csv",
    ]
    for path in candidates:
        if path.is_file():
            return path
    csvs = [p for p in directory.glob("*.csv") if p.name != "target_spec_reference.csv"]
    if len(csvs) == 1:
        return csvs[0]
    return None
