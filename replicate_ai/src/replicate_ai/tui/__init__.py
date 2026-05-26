"""ReplicateAI terminal UI (Textual)."""

from __future__ import annotations

__all__ = ["ReplicateTuiApp"]


def __getattr__(name: str):
    if name == "ReplicateTuiApp":
        from replicate_ai.tui.app import ReplicateTuiApp

        return ReplicateTuiApp
    raise AttributeError(name)
