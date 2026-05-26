"""Tests for TUI view-state event handling."""

from __future__ import annotations

from replicate_ai.tui.events import (
    AuditReady,
    CoefficientsParsed,
    DeliverableWritten,
    Phase,
    PhaseChanged,
    RunFinished,
)
from replicate_ai.tui.handler import TuiViewState, apply_event


class TestApplyEvent:
    def test_deliverable_advances_display_phase_during_agent(self):
        state = TuiViewState()
        apply_event(state, PhaseChanged(Phase.agent))
        assert state.phase_display == "Specify"

        apply_event(state, DeliverableWritten("target_specification.json"))
        assert state.phase_display == "Estimate"
        assert "  ●  wrote target_specification.json" in state.log_lines[-1]

    def test_coefficients_set_running_head(self):
        state = TuiViewState()
        apply_event(
            state,
            CoefficientsParsed(
                model_spec="y = α + β·x + ε",
                estimate_label="β̂ (NJ × Post)",
                estimate=2.85,
                estimate_se=1.32,
                estimate_stars="**",
                published=2.76,
                published_se=1.36,
                published_stars="*",
                delta=0.09,
                verdict="ok",
                citation_line="Card & Krueger (1994), AER 84(4)",
            ),
        )
        assert "Card & Krueger" in state.running_head

    def test_audit_ready_without_coefficients(self):
        state = TuiViewState()
        apply_event(state, AuditReady("## Replication audit\n\n**Verdict**: ok"))
        assert state.coeffs is None
        assert "Replication audit" in (state.audit_md or "")

    def test_run_finished_banner_without_coefficients(self):
        state = TuiViewState()
        apply_event(state, AuditReady("## Audit"))
        apply_event(state, RunFinished(success=True))
        assert state.audit_md is not None
        assert state.audit_md.startswith("Run complete\n\n")
