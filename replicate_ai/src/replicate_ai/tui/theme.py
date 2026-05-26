from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    """Named tokens from docs/DESIGN_TUI.md §5.3.

    Textual/Rich will resolve these as best-effort across terminals.
    """

    text: str = "default"
    dim: str = "grey70"
    accent: str = "#A0522D"  # sienna
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"


TOKENS = ThemeTokens()

