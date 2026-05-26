"""Tail sandbox log files under /workspace/logs (best-effort)."""

from __future__ import annotations

from modal.exception import SandboxFilesystemNotFoundError

LOG_DIR = "/workspace/logs"
KNOWN_LOGS = (
    "00_inspect.log",
    *[f"attempt_{i:02d}.log" for i in range(1, 11)],
)


class LogTailer:
    """Track byte offsets for known log paths and return new text."""

    def __init__(self) -> None:
        self._offsets: dict[str, int] = {}

    def poll(self, filesystem) -> list[str]:
        new_lines: list[str] = []
        for name in KNOWN_LOGS:
            path = f"{LOG_DIR}/{name}"
            try:
                data = filesystem.read_bytes(path)
            except SandboxFilesystemNotFoundError:
                continue
            except Exception:
                continue

            offset = self._offsets.get(path, 0)
            if offset >= len(data):
                continue
            chunk = data[offset:]
            self._offsets[path] = len(data)
            text = chunk.decode("utf-8", errors="replace")
            for line in text.splitlines():
                stripped = line.rstrip()
                if stripped:
                    new_lines.append(stripped)
        return new_lines
