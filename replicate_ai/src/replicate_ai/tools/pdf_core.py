"""PDF extraction logic (runs inside the Modal sandbox)."""

from __future__ import annotations

import json
import re
from pathlib import Path

TABLE_CAPTION_RE = re.compile(
    r"^(?:TABLE|Table)\s+(\d+)\s*(?:[—\-\.:]\s*(.+))?$",
    re.MULTILINE,
)

SANDBOX_WORKSPACE = Path("/workspace")


def output_dir_for_pdf(pdf_path: str) -> Path:
    """Directory for paper_text.md and paper_tables.json."""
    p = Path(pdf_path)
    if str(p).startswith("/workspace"):
        return SANDBOX_WORKSPACE
    return p.parent if p.is_file() else p


def _count_pages(pdf_path: str) -> int:
    import pymupdf

    with pymupdf.open(pdf_path) as doc:
        return len(doc)


def _extract_captions_from_markdown(md: str) -> dict[int, str]:
    captions: dict[int, str] = {}
    for match in TABLE_CAPTION_RE.finditer(md):
        num = int(match.group(1))
        captions[num] = match.group(0).strip()
    return captions


def _rows_from_camelot_table(table) -> list[list[str]]:
    df = table.df
    return [[str(cell).strip() for cell in row] for row in df.values.tolist()]


def _is_ragged(rows: list[list[str]]) -> bool:
    if not rows:
        return True
    widths = {len(row) for row in rows}
    return len(widths) > 1


def _is_empty_table(rows: list[list[str]]) -> bool:
    return not rows or all(not cell for row in rows for cell in row)


def _extract_tables(pdf_path: str, md: str) -> tuple[list[dict], int, int, int]:
    """Return (table_records, n_detected, n_kept, n_ragged)."""
    import camelot

    captions_by_num = _extract_captions_from_markdown(md)
    records: list[dict] = []

    try:
        table_list = camelot.read_pdf(pdf_path, flavor="lattice", pages="all")
    except Exception:
        table_list = camelot.read_pdf(pdf_path, flavor="stream", pages="all")

    n_detected = len(table_list)
    table_num = 0
    for table in table_list:
        rows = _rows_from_camelot_table(table)
        if _is_empty_table(rows):
            continue
        table_num += 1
        caption = captions_by_num.get(
            table_num,
            f"Table on page {table.page} (extracted index {table_num})",
        )
        records.append(
            {
                "caption": caption,
                "page": int(table.page),
                "rows": rows,
            }
        )

    n_ragged = sum(1 for r in records if _is_ragged(r["rows"]))
    return records, n_detected, len(records), n_ragged


def run_pdf_extraction(pdf_path: str) -> str:
    """Extract PDF to paper_text.md and paper_tables.json; return summary line."""
    import pymupdf4llm

    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    out_dir = output_dir_for_pdf(pdf_path)
    text_path = out_dir / "paper_text.md"
    tables_path = out_dir / "paper_tables.json"
    out_dir.mkdir(parents=True, exist_ok=True)

    n_pages = _count_pages(str(path))
    md = pymupdf4llm.to_markdown(str(path))
    text_path.write_text(md, encoding="utf-8")

    table_records, n_detected, n_kept, n_ragged = _extract_tables(str(path), md)
    tables_path.write_text(
        json.dumps(table_records, indent=2),
        encoding="utf-8",
    )

    text_size = len(md)
    empty_skipped = n_detected - n_kept
    summary = (
        f"Extracted {n_pages} pages and {n_kept} tables from {path.name}. "
        f"paper_text.md: {text_size} chars. "
        f"paper_tables.json: {n_kept - n_ragged} well-formed, {n_ragged} ragged."
    )
    if empty_skipped:
        summary += f" Skipped {empty_skipped} empty Camelot region(s); use paper_text.md for tables."
    return summary
