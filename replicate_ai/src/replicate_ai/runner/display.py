"""Map runner-internal phases to journal-styled display labels (docs/DESIGN_TUI.md §6.1)."""

from __future__ import annotations

from replicate_ai.tui.events import Phase


def display_phase_label(phase: Phase, deliverables: set[str]) -> str:
    if phase in (Phase.preflight, Phase.seeding):
        return "Read paper"
    if phase == Phase.agent:
        if "target_specification.json" in deliverables:
            return "Estimate"
        return "Specify"
    if phase in (Phase.audit, Phase.done):
        return "Audit"
    return "Read paper"
