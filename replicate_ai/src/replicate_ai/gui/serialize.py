"""JSON serialization of TUI view state for the browser GUI."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from replicate_ai.tui.events import CoefficientsParsed, RunFinished
from replicate_ai.tui.handler import TuiViewState

LOG_LINE_CAP = 5000
PHASES_DISPLAY = ["Read paper", "Specify", "Estimate", "Audit"]


def _coeffs_to_dict(c: CoefficientsParsed) -> dict[str, Any]:
    return asdict(c)


def _finished_to_dict(f: RunFinished) -> dict[str, Any]:
    return {"success": f.success, "error": f.error}


def view_state_to_json(
    state: TuiViewState,
    *,
    started_at: float | None = None,
    example_dir: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Snapshot of dashboard state for REST/SSE clients."""
    logs = state.log_lines[-LOG_LINE_CAP:]
    return {
        "internal_phase": state.internal_phase.value if state.internal_phase else None,
        "phase_display": state.phase_display,
        "phases": PHASES_DISPLAY,
        "deliverables": sorted(state.deliverables),
        "coeffs": _coeffs_to_dict(state.coeffs) if state.coeffs else None,
        "audit_md": state.audit_md,
        "running_head": state.running_head,
        "finished": _finished_to_dict(state.finished) if state.finished else None,
        "log_lines": logs,
        "started_at": started_at,
        "example_dir": example_dir,
        "provider": provider,
    }
