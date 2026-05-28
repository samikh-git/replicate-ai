"""Small utilities for persistent GUI log files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LogFile:
    path: Path

    def ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_lines(self, lines: list[str]) -> None:
        if not lines:
            return
        self.ensure_parent()
        payload = "\n".join(lines) + "\n"
        with self.path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(payload)


def read_tail(path: Path, *, max_bytes: int = 200_000) -> str:
    """Read last max_bytes of a text file (UTF-8, replacement)."""
    if not path.exists():
        return ""
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[-max_bytes:]
    return data.decode("utf-8", errors="replace")

