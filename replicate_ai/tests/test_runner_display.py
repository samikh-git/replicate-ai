"""Tests for journal-style display phase labels."""

from __future__ import annotations

from replicate_ai.runner.display import display_phase_label
from replicate_ai.tui.events import Phase


class TestDisplayPhaseLabel:
    def test_read_paper_during_preflight_and_seeding(self):
        assert display_phase_label(Phase.preflight, set()) == "Read paper"
        assert display_phase_label(Phase.seeding, set()) == "Read paper"

    def test_specify_during_agent_without_target(self):
        assert display_phase_label(Phase.agent, set()) == "Specify"

    def test_estimate_after_target_spec(self):
        deliverables = {"target_specification.json"}
        assert display_phase_label(Phase.agent, deliverables) == "Estimate"

    def test_audit_phase(self):
        assert display_phase_label(Phase.audit, set()) == "Audit"
        assert display_phase_label(Phase.done, set()) == "Audit"
