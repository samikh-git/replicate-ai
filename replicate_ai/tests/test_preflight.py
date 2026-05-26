"""Tests for host-side preflight PDF extraction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replicate_ai.preflight import (
    cleanup_extract_dir,
    extract_paper_locally,
    find_example_pdf,
    run_local_pdf_extract,
    upload_extract_artifacts,
)


class TestFindExamplePdf:
    def test_prefers_paper_pdf(self, tmp_path: Path):
        (tmp_path / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "card_krueger.pdf").write_bytes(b"%PDF2")
        assert find_example_pdf(tmp_path) == (tmp_path / "paper.pdf").resolve()

    def test_falls_back_to_legacy_card_krueger_name(self, tmp_path: Path):
        (tmp_path / "card_krueger.pdf").write_bytes(b"%PDF")
        assert find_example_pdf(tmp_path) == (tmp_path / "card_krueger.pdf").resolve()

    def test_returns_none_when_missing(self, tmp_path: Path):
        assert find_example_pdf(tmp_path) is None


class TestExtractPaperLocally:
    @patch("replicate_ai.preflight.run_pdf_extraction")
    def test_writes_to_temp_and_returns_summary(self, mock_run, tmp_path: Path):
        pdf = tmp_path / "card_krueger.pdf"
        pdf.write_bytes(b"%PDF")
        mock_run.return_value = "Extracted 2 pages and 0 tables from paper.pdf."

        extract_dir, summary = extract_paper_locally(pdf)

        try:
            assert "Extracted 2 pages" in summary
            assert (extract_dir / "paper.pdf").is_file()
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0].endswith("paper.pdf")
        finally:
            cleanup_extract_dir(extract_dir)


class TestUploadExtractArtifacts:
    def test_uploads_md_and_json(self, tmp_path: Path, monkeypatch):
        extract_dir = tmp_path / "extract"
        extract_dir.mkdir()
        (extract_dir / "paper_text.md").write_text("# hi", encoding="utf-8")
        (extract_dir / "paper_tables.json").write_text("[]", encoding="utf-8")

        fs = MagicMock()
        sandbox = MagicMock()
        sandbox.filesystem = fs

        import replicate_ai.workspace as ws

        monkeypatch.setattr(ws, "_modal_sandbox", sandbox)

        uploaded = upload_extract_artifacts(extract_dir)
        assert len(uploaded) == 2
        assert fs.copy_from_local.call_count == 2


class TestRunLocalPdfExtract:
    @patch("replicate_ai.preflight.extract_paper_locally")
    def test_returns_temp_dir(self, mock_extract, tmp_path: Path):
        (tmp_path / "paper.pdf").write_bytes(b"%PDF")
        mock_extract.return_value = (tmp_path / "out", "summary")

        result = run_local_pdf_extract(tmp_path)
        assert result == tmp_path / "out"
