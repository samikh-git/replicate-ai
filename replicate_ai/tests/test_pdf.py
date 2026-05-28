"""Unit tests for PDF extraction (core logic + Modal tool wrapper)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replicate_ai.tools.pdf_core import (
    _extract_captions_from_markdown,
    _extract_tables,
    _is_empty_table,
    _is_ragged,
    _rows_from_camelot_table,
    output_dir_for_pdf,
    run_pdf_extraction,
)
from replicate_ai.tools.pdf_docling import garbled_table_score

class TestOutputDir:
    def test_under_workspace(self):
        assert output_dir_for_pdf("/workspace/paper.pdf") == Path("/workspace")

    def test_local_pdf_returns_parent(self, tmp_path: Path):
        pdf = tmp_path / "paper.pdf"
        pdf.touch()
        assert output_dir_for_pdf(str(pdf)) == tmp_path.resolve()


class TestExtractCaptionsFromMarkdown:
    def test_parses_table_captions(self):
        md = (
            "Some intro.\n\n"
            "Table 3: Employment effects\n"
            "More text.\n\n"
            "TABLE 4—Wage changes\n"
        )
        captions = _extract_captions_from_markdown(md)
        assert captions[3] == "Table 3: Employment effects"
        assert captions[4].startswith("TABLE 4")

    def test_empty_markdown(self):
        assert _extract_captions_from_markdown("") == {}


class TestIsRagged:
    @pytest.mark.parametrize(
        "rows,expected",
        [
            ([], True),
            ([["a", "b"], ["c", "d"]], False),
            ([["a"], ["b", "c"]], True),
        ],
    )
    def test_ragged_detection(self, rows: list[list[str]], expected: bool):
        assert _is_ragged(rows) is expected


class TestIsEmptyTable:
    def test_all_blank_cells(self):
        assert _is_empty_table([["", ""], ["", ""]]) is True

    def test_has_content(self):
        assert _is_empty_table([["", "x"]]) is False


class TestRowsFromCamelotTable:
    def test_converts_dataframe_to_string_rows(self):
        table = MagicMock()
        table.df.values.tolist.return_value = [[1, 2.5], [3, 4]]
        assert _rows_from_camelot_table(table) == [["1", "2.5"], ["3", "4"]]


class TestExtractTables:
    def _mock_camelot_table(self, page: str, rows: list[list]):
        table = MagicMock()
        table.page = page
        table.df.values.tolist.return_value = rows
        return table

    @patch("camelot.read_pdf")
    def test_skips_empty_tables(self, mock_read_pdf):
        empty = self._mock_camelot_table("6", [["", ""], ["", ""]])
        good = self._mock_camelot_table("7", [["NJ", "2.76"]])
        mock_read_pdf.return_value = [empty, good]

        records, n_detected, n_kept, n_ragged = _extract_tables("/fake/paper.pdf", "")

        assert n_detected == 2
        assert n_kept == 1
        assert len(records) == 1
        assert records[0]["rows"] == [["NJ", "2.76"]]


class TestGarbledTableScore:
    def test_clean_table_low_score(self):
        rows = [["", "NJ", "PA"], ["Wage", "5.05", "4.25"]]
        assert garbled_table_score(rows) < 0.1

    def test_noisy_table_high_score(self):
        rows = [["|", "@", "#"], ["$", "%", "^"]]
        assert garbled_table_score(rows) > 0.5


class TestRunPdfExtraction:
    @patch("replicate_ai.tools.pdf_core._extract_tables_legacy")
    @patch("pymupdf4llm.to_markdown")
    @patch("replicate_ai.tools.pdf_core._count_pages")
    def test_legacy_writes_outputs_and_returns_summary(
        self,
        mock_count_pages: MagicMock,
        mock_to_markdown: MagicMock,
        mock_extract_tables: MagicMock,
        tmp_path: Path,
    ):
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 minimal")
        md = "# Title\n\nTable 1: Results\n\nBody text."
        mock_count_pages.return_value = 28
        mock_to_markdown.return_value = md
        mock_extract_tables.return_value = (
            [{"caption": "Table 1: Results", "page": 3, "rows": [["x", "y"]]}],
            2,
            1,
            0,
        )

        result = run_pdf_extraction(str(pdf), backend="legacy")

        assert (tmp_path / "paper_text.md").read_text(encoding="utf-8") == md
        tables = json.loads((tmp_path / "paper_tables.json").read_text(encoding="utf-8"))
        assert len(tables) == 1
        assert "(legacy)" in result
        assert "28 pages" in result
        assert "Skipped 1 empty" in result

    @patch("replicate_ai.tools.pdf_core._run_docling_extraction")
    def test_docling_backend_dispatches(
        self,
        mock_docling: MagicMock,
        tmp_path: Path,
    ):
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 minimal")
        mock_docling.return_value = "Extracted (docling) 10 pages and 2 tables."

        result = run_pdf_extraction(str(pdf), backend="docling")

        assert "(docling)" in result
        mock_docling.assert_called_once()

