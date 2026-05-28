"""Tests for GUI JSON serialization."""

from __future__ import annotations

from replicate_ai.gui.serialize import view_state_to_json
from replicate_ai.tui.events import (
    AuditReady,
    CoefficientsParsed,
    Phase,
    PhaseChanged,
    RunFinished,
)
from replicate_ai.tui.handler import TuiViewState, apply_event


class TestViewStateToJson:
    def test_empty_state(self):
        state = TuiViewState()
        out = view_state_to_json(state)
        assert out["phase_display"] == "Read paper"
        assert out["coeffs"] is None
        assert out["log_lines"] == []

    def test_coefficients_and_audit(self):
        state = TuiViewState()
        apply_event(state, PhaseChanged(Phase.agent))
        apply_event(
            state,
            CoefficientsParsed(
                model_spec="y = α + β·x",
                estimate_label="β̂",
                estimate=1.0,
                estimate_se=0.5,
                estimate_stars="*",
                published=0.9,
                published_se=0.4,
                published_stars="",
                delta=0.1,
                verdict="ok",
                citation_line="Test (2020)",
            ),
        )
        apply_event(state, AuditReady("## Audit\n\nDone."))
        apply_event(state, RunFinished(success=True))
        out = view_state_to_json(state, example_dir="/tmp/ex", provider="Anthropic")
        assert out["coeffs"]["estimate"] == 1.0
        assert "Audit" in (out["audit_md"] or "")
        assert out["finished"]["success"] is True
        assert out["example_dir"] == "/tmp/ex"
