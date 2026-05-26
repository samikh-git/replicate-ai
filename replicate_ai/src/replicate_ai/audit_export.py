"""Write replication_audit.md to the host filesystem."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

AUDIT_FILENAME = "replication_audit.md"


def default_audit_path(example_dir: Path | None) -> Path:
    """Default host path for a completed audit."""
    if example_dir is not None:
        return example_dir.resolve() / AUDIT_FILENAME
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return Path.cwd() / f"replication_audit_{stamp}.md"


def write_audit_file(path: Path, markdown: str) -> Path:
    """Write audit markdown to ``path``; return the resolved path."""
    if not markdown.strip():
        raise ValueError("Refusing to write empty audit markdown")
    dest = path.expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(markdown, encoding="utf-8")
    return dest


def maybe_save_audit(
    *,
    markdown: str | None,
    example_dir: Path | None = None,
    audit_out: Path | None = None,
    enabled: bool = True,
) -> Path | None:
    """Persist audit markdown when ``enabled`` and content is non-empty.

    If ``audit_out`` is set, use it. Else if ``example_dir`` is set, use
    ``<example_dir>/replication_audit.md``. Otherwise do not write (returns None).
    """
    if not enabled or not markdown or not markdown.strip():
        return None
    if audit_out is not None:
        return write_audit_file(audit_out, markdown)
    if example_dir is not None:
        return write_audit_file(default_audit_path(example_dir), markdown)
    return None
