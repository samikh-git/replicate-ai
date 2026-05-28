"""Docling-based PDF extraction (host preflight)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from replicate_ai.tools.pdf_core import (
    _extract_captions_from_markdown,
    _is_empty_table,
    _is_ragged,
)

if TYPE_CHECKING:
    from docling_core.types.doc import DoclingDocument

PdfDoclingOptions = dict[str, Any]


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def build_docling_converter():
    """Create a DocumentConverter tuned for economics PDFs (CPU, optional OCR)."""
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions()
    opts.do_ocr = _env_flag("REPLICATE_AI_PDF_OCR")
    opts.do_table_structure = True
    opts.accelerator_options = AcceleratorOptions(
        device=AcceleratorDevice.CPU,
        num_threads=int(os.getenv("DOCLING_NUM_THREADS", "4")),
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )


def _build_ref_text_index(doc: DoclingDocument) -> dict[str, str]:
    index: dict[str, str] = {}
    for item, _level in doc.iterate_items():
        ref = getattr(item, "self_ref", None)
        if ref is None:
            continue
        text = getattr(item, "text", None)
        if text:
            index[str(ref)] = str(text).strip()
    return index


def _caption_from_docling(
    doc: DoclingDocument,
    table: Any,
    *,
    ref_index: dict[str, str],
    captions_by_num: dict[int, str],
    table_index: int,
) -> str:
    for ref in getattr(table, "captions", None) or []:
        text = ref_index.get(str(ref.cref))
        if text:
            return text
    page = _table_page(table)
    if page is not None:
        for num, caption in captions_by_num.items():
            if f"page {page}" in caption.lower():
                return caption
    return captions_by_num.get(
        table_index,
        f"Table on page {page or '?'} (extracted index {table_index})",
    )


def _table_page(table: Any) -> int | None:
    prov = getattr(table, "prov", None)
    if not prov:
        return None
    page_no = getattr(prov[0], "page_no", None)
    if page_no is None:
        return None
    return int(page_no)


def _rows_from_dataframe(df) -> list[list[str]]:
    work = df.reset_index(drop=False)
    rows: list[list[str]] = [[str(c).strip() for c in work.columns]]
    for _idx, row in work.iterrows():
        rows.append([str(v).strip() for v in row.tolist()])
    return rows


def _rows_from_docling_table(doc: DoclingDocument, table: Any) -> list[list[str]]:
    df = table.export_to_dataframe(doc=doc)
    return _rows_from_dataframe(df)


def extract_docling_tables(
    doc: DoclingDocument,
    md: str,
) -> tuple[list[dict], int, int, int]:
    """Return (table_records, n_detected, n_kept, n_ragged)."""
    ref_index = _build_ref_text_index(doc)
    captions_by_num = _extract_captions_from_markdown(md)
    tables = list(getattr(doc, "tables", None) or [])
    records: list[dict] = []
    table_num = 0
    for table in tables:
        rows = _rows_from_docling_table(doc, table)
        if _is_empty_table(rows):
            continue
        table_num += 1
        page = _table_page(table)
        records.append(
            {
                "caption": _caption_from_docling(
                    doc,
                    table,
                    ref_index=ref_index,
                    captions_by_num=captions_by_num,
                    table_index=table_num,
                ),
                "page": page if page is not None else 0,
                "rows": rows,
            }
        )
    n_detected = len(tables)
    n_ragged = sum(1 for r in records if _is_ragged(r["rows"]))
    return records, n_detected, len(records), n_ragged


def _count_pages_docling(doc: DoclingDocument) -> int:
    pages = getattr(doc, "pages", None)
    if pages is not None:
        return len(pages)
    return 0


def run_docling_extraction(pdf_path: str) -> tuple[str, list[dict], int, int, int, int]:
    """Convert PDF with Docling; return (markdown, tables, n_pages, n_detected, n_kept, n_ragged)."""
    from pathlib import Path

    from docling.exceptions import ConversionError

    path = Path(pdf_path)
    converter = build_docling_converter()
    try:
        result = converter.convert(str(path))
    except ConversionError as exc:
        raise RuntimeError(f"Docling failed to convert {path.name}: {exc}") from exc

    doc = result.document
    md = doc.export_to_markdown()
    n_pages = _count_pages_docling(doc)
    records, n_detected, n_kept, n_ragged = extract_docling_tables(doc, md)
    return md, records, n_pages, n_detected, n_kept, n_ragged


def garbled_table_score(rows: list[list[str]]) -> float:
    """Heuristic: fraction of cells that look like OCR noise (single non-alnum char)."""
    cells = [c for row in rows for c in row if c]
    if not cells:
        return 1.0
    noisy = sum(1 for c in cells if len(c) == 1 and not c.isalnum())
    return noisy / len(cells)
