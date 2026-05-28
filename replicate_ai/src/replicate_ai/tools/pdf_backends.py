"""PDF backend selection for host preflight."""

from __future__ import annotations

import os
from typing import Literal

PdfBackend = Literal["docling", "legacy"]

PDF_BACKENDS: tuple[PdfBackend, ...] = ("docling", "legacy")
DEFAULT_PDF_BACKEND: PdfBackend = "docling"


def resolve_pdf_backend(value: str | None = None) -> PdfBackend:
    """Resolve backend from explicit value, REPLICATE_AI_PDF_BACKEND, or default."""
    raw = (value or os.getenv("REPLICATE_AI_PDF_BACKEND") or DEFAULT_PDF_BACKEND).strip().lower()
    if raw not in PDF_BACKENDS:
        raise ValueError(
            f"Unknown PDF backend {raw!r}; choose one of: {', '.join(PDF_BACKENDS)}"
        )
    return raw  # type: ignore[return-value]
