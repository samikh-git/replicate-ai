"""PDF extraction for host preflight (paper_text.md + paper_tables.json)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from replicate_ai.tools.pdf_backends import PdfBackend, resolve_pdf_backend

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


def _extract_tables_legacy(pdf_path: str, md: str) -> tuple[list[dict], int, int, int]:
    """Return (table_records, n_detected, n_kept, n_ragged) via Camelot."""
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


# Backwards-compatible alias for tests
_extract_tables = _extract_tables_legacy


def _format_summary(
    *,
    path: Path,
    backend: PdfBackend,
    n_pages: int,
    n_kept: int,
    n_ragged: int,
    text_size: int,
    n_detected: int,
    empty_skipped: int,
    garbled_tables: int = 0,
) -> str:
    engine = "Docling" if backend == "docling" else "Camelot"
    summary = (
        f"Extracted ({backend}) {n_pages} pages and {n_kept} tables from {path.name}. "
        f"paper_text.md: {text_size} chars. "
        f"paper_tables.json: {n_kept - n_ragged} well-formed, {n_ragged} ragged."
    )
    if empty_skipped:
        summary += (
            f" Skipped {empty_skipped} empty {engine} region(s); use paper_text.md for tables."
        )
    if garbled_tables:
        summary += (
            f" Warning: {garbled_tables} table(s) look garbled; prefer paper_text.md for numbers."
        )
    return summary


def _run_legacy_extraction(pdf_path: str, out_dir: Path) -> str:
    import pymupdf4llm

    path = Path(pdf_path)
    n_pages = _count_pages(str(path))
    md = pymupdf4llm.to_markdown(str(path))
    (out_dir / "paper_text.md").write_text(md, encoding="utf-8")

    table_records, n_detected, n_kept, n_ragged = _extract_tables_legacy(str(path), md)
    (out_dir / "paper_tables.json").write_text(
        json.dumps(table_records, indent=2),
        encoding="utf-8",
    )
    return _format_summary(
        path=path,
        backend="legacy",
        n_pages=n_pages,
        n_kept=n_kept,
        n_ragged=n_ragged,
        text_size=len(md),
        n_detected=n_detected,
        empty_skipped=n_detected - n_kept,
    )


def _run_docling_extraction(pdf_path: str, out_dir: Path) -> str:
    from replicate_ai.tools.pdf_docling import (
        extract_docling_tables,
        garbled_table_score,
        run_docling_extraction,
    )

    path = Path(pdf_path)
    md, table_records, n_pages, n_detected, n_kept, n_ragged = run_docling_extraction(
        str(path)
    )
    (out_dir / "paper_text.md").write_text(md, encoding="utf-8")
    (out_dir / "paper_tables.json").write_text(
        json.dumps(table_records, indent=2),
        encoding="utf-8",
    )
    garbled_tables = sum(
        1 for r in table_records if garbled_table_score(r["rows"]) > 0.35
    )
    return _format_summary(
        path=path,
        backend="docling",
        n_pages=n_pages,
        n_kept=n_kept,
        n_ragged=n_ragged,
        text_size=len(md),
        n_detected=n_detected,
        empty_skipped=n_detected - n_kept,
        garbled_tables=garbled_tables,
    )


def run_pdf_extraction(
    pdf_path: str,
    *,
    backend: PdfBackend | str | None = None,
) -> str:
    """Extract PDF to paper_text.md and paper_tables.json; return summary line."""
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    resolved = resolve_pdf_backend(backend)
    out_dir = output_dir_for_pdf(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    if resolved == "docling":
        try:
            return _run_docling_extraction(pdf_path, out_dir)
        except ImportError as exc:
            raise RuntimeError(
                "PDF backend 'docling' requires the docling package. "
                "Run: uv sync --group pdf  (or install docling in your environment)"
            ) from exc
    return _run_legacy_extraction(pdf_path, out_dir)
