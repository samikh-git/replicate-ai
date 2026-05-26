"""Tests for Modal /workspace seeding (no host workspace directory)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from replicate_ai.workspace import (
    SANDBOX_WORKSPACE,
    seed_example_to_sandbox,
    set_modal_sandbox,
)


class TestSeedExampleToSandbox:
    def test_copies_pdf_and_csv(self, tmp_path: Path):
        example = tmp_path / "example"
        example.mkdir()
        (example / "card_krueger.pdf").write_bytes(b"%PDF")
        (example / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")

        fs = MagicMock()
        sandbox = MagicMock()
        sandbox.filesystem = fs
        set_modal_sandbox(sandbox)

        seeded = seed_example_to_sandbox(example)

        assert seeded == [
            f"{SANDBOX_WORKSPACE}/paper.pdf",
            f"{SANDBOX_WORKSPACE}/data.csv",
        ]
        fs.make_directory.assert_called_once_with(SANDBOX_WORKSPACE, create_parents=True)
        assert fs.copy_from_local.call_count == 2
        set_modal_sandbox(None)

    def test_missing_pdf_raises(self, tmp_path: Path):
        example = tmp_path / "empty"
        example.mkdir()
        (example / "data.csv").write_text("a\n", encoding="utf-8")
        sandbox = MagicMock()
        set_modal_sandbox(sandbox)
        with pytest.raises(FileNotFoundError, match="paper PDF"):
            seed_example_to_sandbox(example)
        set_modal_sandbox(None)

    def test_missing_csv_raises(self, tmp_path: Path):
        example = tmp_path / "partial"
        example.mkdir()
        (example / "paper.pdf").write_bytes(b"%PDF")
        sandbox = MagicMock()
        set_modal_sandbox(sandbox)
        with pytest.raises(FileNotFoundError, match="data.csv"):
            seed_example_to_sandbox(example)
        set_modal_sandbox(None)
