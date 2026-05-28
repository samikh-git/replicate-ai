from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Phase(str, Enum):
    """Runner-internal phases (see docs/DESIGN_TUI.md §6.1)."""

    preflight = "preflight"
    seeding = "seeding"
    agent = "agent"
    audit = "audit"
    done = "done"


LogSource = Literal["host", "agent", "sandbox"]
DeliverableName = Literal[
    "target_specification.json",
    "results/coefficients.json",
    "replication_audit.md",
]
Verdict = Literal["ok", "borderline", "fail"]


@dataclass(frozen=True)
class PhaseChanged:
    phase: Phase


@dataclass(frozen=True)
class Status:
    message: str
    source: LogSource = "agent"


@dataclass(frozen=True)
class LogChunk:
    text: str
    source: LogSource


@dataclass(frozen=True)
class DeliverableWritten:
    name: DeliverableName


@dataclass(frozen=True)
class CoefficientsParsed:
    model_spec: str
    estimate_label: str
    estimate: float
    estimate_se: float
    estimate_stars: str
    published: float
    published_se: float | None
    published_stars: str
    delta: float
    verdict: Verdict
    citation_line: str


@dataclass(frozen=True)
class AuditReady:
    markdown: str


@dataclass(frozen=True)
class RunFinished:
    success: bool
    error: str | None = None

