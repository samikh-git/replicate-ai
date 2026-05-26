"""Tests for run_replication event emission (mocked Modal/agent)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from modal.exception import SandboxFilesystemNotFoundError

from replicate_ai.runner.run import RunConfig, run_replication
from replicate_ai.tui.events import (
    AuditReady,
    DeliverableWritten,
    Phase,
    PhaseChanged,
    RunFinished,
)


@pytest.fixture
def collected_events():
    events: list[object] = []

    def emit(ev: object) -> None:
        events.append(ev)

    return events, emit


class TestRunReplicationEvents:
    @patch("replicate_ai.runner.run.create_deep_agent")
    @patch("replicate_ai.runner.run.modal.Sandbox.create")
    @patch("replicate_ai.runner.run.modal.App.lookup")
    @patch("replicate_ai.runner.run.build_sandbox_image")
    @patch("replicate_ai.runner.run.seed_example_to_sandbox")
    def test_emits_phases_and_audit(
        self,
        mock_seed,
        mock_image,
        mock_lookup,
        mock_sandbox_create,
        mock_create_agent,
        tmp_path: Path,
        collected_events,
    ):
        events, emit = collected_events
        (tmp_path / "card_krueger.pdf").write_bytes(b"%PDF")
        (tmp_path / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")

        mock_seed.return_value = ["/workspace/paper.pdf", "/workspace/data.csv"]

        sandbox = MagicMock()
        fs = MagicMock()
        sandbox.filesystem = fs
        mock_sandbox_create.return_value = sandbox

        def read_bytes(path: str) -> bytes:
            if path.endswith("replication_audit.md"):
                return b"# Audit\n\nok"
            if path.endswith("target_specification.json"):
                return b'{"expected_coefficients":[{"name":"nj_post","published_estimate":2.76,"published_se":1.36}],"paper_citation":"Test"}'
            if path.endswith("coefficients.json"):
                return b'{"status":"success","estimates":[{"name":"nj_post","point_estimate":2.8,"std_error":1.3,"p_value":0.03}]}'
            raise SandboxFilesystemNotFoundError("missing")

        fs.read_bytes.side_effect = read_bytes

        agent = MagicMock()
        agent.invoke.return_value = {"messages": []}
        mock_create_agent.return_value = agent

        with patch("replicate_ai.runner.run.extract_paper_locally") as mock_extract:
            extract_dir = tmp_path / "extract"
            extract_dir.mkdir()
            (extract_dir / "paper_text.md").write_text("# x", encoding="utf-8")
            (extract_dir / "paper_tables.json").write_text("[]", encoding="utf-8")
            mock_extract.return_value = (extract_dir, "Extracted 1 pages and 0 tables.")

            with patch("replicate_ai.runner.run.upload_extract_artifacts", return_value=["/workspace/paper_text.md"]):
                result = run_replication(
                    RunConfig(example_dir=tmp_path, skip_pdf_extract=False),
                    emit=emit,
                )

        assert result.get("replication_audit_md") == "# Audit\n\nok"
        phases = [e.phase for e in events if isinstance(e, PhaseChanged)]
        assert phases[0] == Phase.preflight
        assert Phase.seeding in phases
        assert Phase.agent in phases
        assert Phase.audit in phases
        assert Phase.done in phases
        assert any(isinstance(e, AuditReady) for e in events)
        finished = [e for e in events if isinstance(e, RunFinished)]
        assert finished[-1].success is True

    @patch("replicate_ai.runner.run.create_deep_agent")
    @patch("replicate_ai.runner.run.modal.Sandbox.create")
    @patch("replicate_ai.runner.run.modal.App.lookup")
    @patch("replicate_ai.runner.run.build_sandbox_image")
    @patch("replicate_ai.runner.run.seed_example_to_sandbox")
    def test_run_finished_false_without_audit(
        self,
        mock_seed,
        mock_image,
        mock_lookup,
        mock_sandbox_create,
        mock_create_agent,
        tmp_path: Path,
        collected_events,
    ):
        events, emit = collected_events
        mock_seed.return_value = []
        sandbox = MagicMock()
        fs = MagicMock()
        sandbox.filesystem = fs
        mock_sandbox_create.return_value = sandbox

        def read_bytes(path: str) -> bytes:
            raise SandboxFilesystemNotFoundError("missing")

        fs.read_bytes.side_effect = read_bytes

        agent = MagicMock()
        agent.invoke.return_value = {}
        mock_create_agent.return_value = agent

        run_replication(RunConfig(example_dir=None, skip_pdf_extract=True), emit=emit)

        finished = [e for e in events if isinstance(e, RunFinished)]
        assert finished[-1].success is False
