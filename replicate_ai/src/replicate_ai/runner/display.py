"""Map runner-internal phases to journal-styled display labels (docs/DESIGN_TUI.md §6.1)."""

from __future__ import annotations

from replicate_ai.tui.events import Phase


def display_phase_label(phase: Phase, deliverables: set[str]) -> str:
    # Poll loop may surface replication_audit.md while internal phase is still agent.
    if "replication_audit.md" in deliverables:
        return "Audit"
    if phase in (Phase.preflight, Phase.seeding):
        return "Read paper"
    if phase == Phase.agent:
        if "target_specification.json" in deliverables:
            return "Estimate"
        return "Specify"
    if phase in (Phase.audit, Phase.done):
        return "Audit"
    return "Read paper"
