"""Build the Modal sandbox image from [dependency-groups.sandbox] in pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

import modal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def load_sandbox_dependencies(pyproject_path: Path | None = None) -> list[str]:
    """Return sandbox dependency specifiers from pyproject.toml."""
    path = pyproject_path or PYPROJECT_PATH
    with open(path, "rb") as f:
        data = tomllib.load(f)
    try:
        return list(data["dependency-groups"]["sandbox"])
    except KeyError as e:
        raise ValueError(
            f"Missing [dependency-groups.sandbox] in {path}"
        ) from e


def build_sandbox_image(
    *,
    python_version: str = "3.12",
    pyproject_path: Path | None = None,
) -> modal.Image:
    """Modal image with econometrics stack only (PDF parsing runs on the host)."""
    deps = load_sandbox_dependencies(pyproject_path)
    return modal.Image.debian_slim(python_version=python_version).uv_pip_install(
        *deps
    )
