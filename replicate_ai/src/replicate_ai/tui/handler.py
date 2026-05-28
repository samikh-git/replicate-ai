"""Pure event → view-state updates (testable without Textual)."""

from __future__ import annotations

from dataclasses import dataclass, field

from replicate_ai.runner.display import display_phase_label
from replicate_ai.tui.events import (
    AuditReady,
    CoefficientsParsed,
    DeliverableWritten,
    LogChunk,
    Phase,
    PhaseChanged,
    RunFinished,
    Status,
)


@dataclass
class TuiViewState:
    internal_phase: Phase | None = None
    phase_display: str = "Read paper"
    deliverables: set[str] = field(default_factory=set)
    coeffs: CoefficientsParsed | None = None
    audit_md: str | None = None
    running_head: str = ""
    finished: RunFinished | None = None
    log_lines: list[str] = field(default_factory=list)


def apply_event(state: TuiViewState, ev: object) -> None:
    if isinstance(ev, PhaseChanged):
        state.internal_phase = ev.phase
        state.phase_display = display_phase_label(ev.phase, state.deliverables)
        return

    if isinstance(ev, LogChunk):
        state.log_lines.append(ev.text)
        return

    if isinstance(ev, Status):
        state.log_lines.append(f"[{ev.source}] {ev.message}")
        return

    if isinstance(ev, DeliverableWritten):
        state.deliverables.add(ev.name)
        if state.internal_phase is not None:
            state.phase_display = display_phase_label(
                state.internal_phase,
                state.deliverables,
            )
        state.log_lines.append(f"  ●  wrote {ev.name}")
        return

    if isinstance(ev, CoefficientsParsed):
        state.coeffs = ev
        state.running_head = f"Replicating · {ev.citation_line.replace(',', ' ·')}"
        return

    if isinstance(ev, AuditReady):
        state.audit_md = ev.markdown
        state.deliverables.add("replication_audit.md")
        if state.internal_phase is not None:
            state.phase_display = display_phase_label(
                state.internal_phase,
                state.deliverables,
            )
        else:
            state.phase_display = "Audit"
        return

    if isinstance(ev, RunFinished):
        state.finished = ev
        if state.audit_md:
            if state.coeffs:
                verdict = state.coeffs.verdict
                g = "✓" if verdict == "ok" else ("△" if verdict == "borderline" else "✗")
                banner = f"Run complete · {g} {verdict}"
            else:
                banner = "Run complete"
            if not state.audit_md.startswith("Run complete"):
                state.audit_md = banner + "\n\n" + state.audit_md
