"""Scan curated example packs under the repo examples/ directory."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from replicate_ai.example_assets import find_example_data_csv, find_example_pdf

_SKIP_DIRS = {"__pycache__", "_common"}


def find_examples_root(start: Path | None = None) -> Path | None:
    """Locate examples/ by walking up from *start* (default cwd)."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        candidate = parent / "examples"
        if candidate.is_dir() and any(p.is_dir() for p in candidate.iterdir()):
            return candidate
    return None


def _first_heading_line(readme: Path) -> str | None:
    if not readme.is_file():
        return None
    for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _citation_from_readme(readme: Path) -> str | None:
    if not readme.is_file():
        return None
    text = readme.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Paper:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    return None


def list_example_packs(examples_root: Path) -> list[dict[str, Any]]:
    """Return metadata for each subdirectory of *examples_root*."""
    packs: list[dict[str, Any]] = []
    for child in sorted(examples_root.iterdir()):
        if not child.is_dir() or child.name.startswith("_") or child.name in _SKIP_DIRS:
            continue
        readme = child / "README.md"
        pdf = find_example_pdf(child)
        csv = find_example_data_csv(child)
        ref_path = child / "target_spec_reference.json"
        packs.append(
            {
                "id": child.name,
                "label": _first_heading_line(readme) or child.name.replace("_", " ").title(),
                "path": str(child.resolve()),
                "citation": _citation_from_readme(readme),
                "has_pdf": pdf is not None,
                "has_csv": csv is not None,
                "has_reference": ref_path.is_file(),
            }
        )
    return packs


def load_providers() -> list[dict[str, str]]:
    from replicate_ai.models import list_provider_options

    return list_provider_options()


def default_provider() -> str:
    from replicate_ai.models import normalize_provider

    return normalize_provider(None)
