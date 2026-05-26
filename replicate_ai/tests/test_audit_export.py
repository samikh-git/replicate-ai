"""Tests for host-side audit export."""

from __future__ import annotations

from pathlib import Path

import pytest

from replicate_ai.audit_export import (
    AUDIT_FILENAME,
    default_audit_path,
    maybe_save_audit,
    write_audit_file,
)


class TestAuditExport:
    def test_write_audit_file(self, tmp_path: Path):
        dest = write_audit_file(tmp_path / "out.md", "# Audit\n\nok")
        assert dest.read_text(encoding="utf-8") == "# Audit\n\nok"

    def test_default_audit_path_uses_example_dir(self, tmp_path: Path):
        assert default_audit_path(tmp_path) == tmp_path / AUDIT_FILENAME

    def test_maybe_save_audit_to_example_dir(self, tmp_path: Path):
        path = maybe_save_audit(
            markdown="# Audit",
            example_dir=tmp_path,
        )
        assert path == (tmp_path / AUDIT_FILENAME).resolve()
        assert path.is_file()

    def test_maybe_save_audit_explicit_out(self, tmp_path: Path):
        out = tmp_path / "custom.md"
        path = maybe_save_audit(
            markdown="# Audit",
            example_dir=tmp_path,
            audit_out=out,
        )
        assert path == out.resolve()

    def test_maybe_save_disabled(self, tmp_path: Path):
        assert maybe_save_audit(
            markdown="# Audit",
            example_dir=tmp_path,
            enabled=False,
        ) is None

    def test_maybe_save_empty_skips(self, tmp_path: Path):
        assert maybe_save_audit(markdown="", example_dir=tmp_path) is None

    def test_write_empty_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="empty"):
            write_audit_file(tmp_path / "x.md", "   ")
