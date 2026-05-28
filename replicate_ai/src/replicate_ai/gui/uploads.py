"""Host-side upload handling for ad-hoc example packs (no size cap)."""

from __future__ import annotations

import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from replicate_ai.example_assets import find_example_data_csv, find_example_pdf

_UPLOAD_ROOT: Path | None = None


def upload_root() -> Path:
    global _UPLOAD_ROOT
    if _UPLOAD_ROOT is None:
        _UPLOAD_ROOT = Path(tempfile.gettempdir()) / "replicate_ai_uploads"
        _UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return _UPLOAD_ROOT


def cleanup_upload_root() -> None:
    global _UPLOAD_ROOT
    if _UPLOAD_ROOT is not None and _UPLOAD_ROOT.is_dir():
        shutil.rmtree(_UPLOAD_ROOT, ignore_errors=True)
        _UPLOAD_ROOT = None


def new_pack_dir() -> Path:
    pack_id = uuid.uuid4().hex[:12]
    dest = upload_root() / f"pack_{pack_id}"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _safe_relative_path(rel: str) -> Path:
    """Reject path traversal in uploaded relative paths."""
    parts = []
    for part in Path(rel).parts:
        if part in ("", ".", ".."):
            continue
        parts.append(part)
    if not parts:
        raise ValueError(f"Invalid relative path: {rel!r}")
    return Path(*parts)


@dataclass(frozen=True)
class UploadResult:
    pack_path: Path
    paper_filename: str
    data_filename: str
    total_bytes: int
    warnings: list[str]


def _resolve_pack(pack_dir: Path) -> UploadResult:
    pdf = find_example_pdf(pack_dir)
    csv = find_example_data_csv(pack_dir)
    if pdf is None:
        raise ValueError("No PDF found in upload (expected paper.pdf or a single *.pdf)")
    if csv is None:
        raise ValueError("No CSV found in upload (expected data.csv or a single *.csv)")
    total = sum(f.stat().st_size for f in pack_dir.rglob("*") if f.is_file())
    warnings: list[str] = []
    mb = total / (1024 * 1024)
    if mb >= 1000:
        warnings.append(f"Very large upload ({mb:.0f} MB)")
    elif mb >= 100:
        warnings.append(f"Large upload ({mb:.0f} MB)")
    return UploadResult(
        pack_path=pack_dir.resolve(),
        paper_filename=pdf.name,
        data_filename=csv.name,
        total_bytes=total,
        warnings=warnings,
    )


async def save_uploaded_file(dest: Path, stream) -> int:
    """Stream an upload body to *dest*; return bytes written."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    nbytes = 0
    with dest.open("wb") as fh:
        read = getattr(stream, "read", None)
        if callable(read):
            while True:
                chunk = await read(1024 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
                nbytes += len(chunk)
        else:
            async for chunk in stream:
                if chunk:
                    fh.write(chunk)
                    nbytes += len(chunk)
    return nbytes


async def ingest_files_mode(
    *,
    paper_stream,
    paper_filename: str,
    data_stream,
    data_filename: str,
) -> UploadResult:
    pack_dir = new_pack_dir()
    paper_dest = pack_dir / "paper.pdf"
    data_dest = pack_dir / "data.csv"
    await save_uploaded_file(paper_dest, paper_stream)
    await save_uploaded_file(data_dest, data_stream)
    result = _resolve_pack(pack_dir)
    return result


async def ingest_directory_mode(
    files: list[tuple[str, object]],
) -> UploadResult:
    """*files* is (relative_path, async stream) pairs."""
    pack_dir = new_pack_dir()
    for rel, stream in files:
        rel_path = _safe_relative_path(rel)
        dest = pack_dir / rel_path
        await save_uploaded_file(dest, stream)
    return _resolve_pack(pack_dir)
