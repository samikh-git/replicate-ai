"""Tests for deliverable polling edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock

from replicate_ai.runner.run import _poll_deliverables
from replicate_ai.tui.events import AuditReady, DeliverableWritten


class TestPollDeliverables:
    def test_skips_empty_files(self):
        fs = MagicMock()
        fs.read_bytes.return_value = b""
        events: list[object] = []
        seen: set[str] = set()
        _poll_deliverables(fs, seen=seen, emit=events.append, coeffs_emitted=[False])
        assert seen == set()
        assert events == []

    def test_emits_audit_ready_when_audit_file_has_content(self):
        fs = MagicMock()

        def read_bytes(path: str) -> bytes:
            if path.endswith("replication_audit.md"):
                return b"# Audit\n\nok"
            raise Exception("missing")

        fs.read_bytes.side_effect = read_bytes
        events: list[object] = []
        seen: set[str] = set()
        _poll_deliverables(fs, seen=seen, emit=events.append, coeffs_emitted=[False])
        assert "replication_audit.md" in seen
        assert any(isinstance(e, DeliverableWritten) for e in events)
        assert any(isinstance(e, AuditReady) for e in events)
