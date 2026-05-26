"""Tests for example pack asset resolution."""

from __future__ import annotations

from pathlib import Path

from replicate_ai.example_assets import find_example_data_csv, find_example_pdf


class TestExampleAssets:
    def test_find_pdf_prefers_paper_pdf(self, tmp_path: Path):
        (tmp_path / "paper.pdf").write_bytes(b"%PDF")
        (tmp_path / "other.pdf").write_bytes(b"%PDF2")
        assert find_example_pdf(tmp_path) == (tmp_path / "paper.pdf").resolve()

    def test_find_pdf_single_glob(self, tmp_path: Path):
        (tmp_path / "dehejia_wahba.pdf").write_bytes(b"%PDF")
        assert find_example_pdf(tmp_path) == (tmp_path / "dehejia_wahba.pdf").resolve()

    def test_find_data_csv(self, tmp_path: Path):
        (tmp_path / "data.csv").write_text("a\n", encoding="utf-8")
        assert find_example_data_csv(tmp_path) == (tmp_path / "data.csv").resolve()
