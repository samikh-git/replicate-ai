"""Preflight: PDF extraction on the host, then upload artifacts to Modal /workspace."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from replicate_ai.example_assets import find_example_pdf
from replicate_ai.tools.pdf_core import run_pdf_extraction
from replicate_ai.workspace import SANDBOX_WORKSPACE, upload_local_files_to_sandbox

EXTRACT_ARTIFACTS = ("paper_text.md", "paper_tables.json")


def extract_paper_locally(pdf_path: Path) -> tuple[Path, str]:
    """Extract PDF into a temp dir; returns (temp_dir, summary). Caller deletes temp_dir."""
    tmp = Path(tempfile.mkdtemp(prefix="replicate_ai_extract_"))
    staging_pdf = tmp / "paper.pdf"
    shutil.copy2(pdf_path, staging_pdf)
    summary = run_pdf_extraction(str(staging_pdf))
    return tmp, summary


def run_local_pdf_extract(example_dir: Path) -> Path | None:
    """Run host-side extraction. Returns temp dir with artifacts, or None."""
    pdf = find_example_pdf(example_dir)
    if pdf is None:
        return None
    extract_dir, summary = extract_paper_locally(pdf)
    print(f"Local PDF extract: {summary}")
    return extract_dir


def upload_extract_artifacts(extract_dir: Path) -> list[str]:
    """Upload paper_text.md and paper_tables.json from a local temp dir."""
    uploads: list[tuple[Path, str]] = []
    for name in EXTRACT_ARTIFACTS:
        local = extract_dir / name
        if local.is_file():
            uploads.append((local, f"{SANDBOX_WORKSPACE}/{name}"))
    if not uploads:
        raise RuntimeError(
            f"PDF extraction produced no artifacts in {extract_dir} "
            f"(expected {', '.join(EXTRACT_ARTIFACTS)})"
        )
    return upload_local_files_to_sandbox(uploads)


def cleanup_extract_dir(extract_dir: Path | None) -> None:
    if extract_dir is not None and extract_dir.is_dir():
        shutil.rmtree(extract_dir, ignore_errors=True)
