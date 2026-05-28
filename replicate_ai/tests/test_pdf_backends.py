"""Tests for PDF backend resolution."""

from __future__ import annotations

import os

import pytest

from replicate_ai.tools.pdf_backends import DEFAULT_PDF_BACKEND, resolve_pdf_backend


def test_default_backend():
    assert DEFAULT_PDF_BACKEND == "docling"


def test_resolve_explicit():
    assert resolve_pdf_backend("legacy") == "legacy"


def test_resolve_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REPLICATE_AI_PDF_BACKEND", "legacy")
    assert resolve_pdf_backend(None) == "legacy"


def test_unknown_backend():
    with pytest.raises(ValueError, match="Unknown PDF backend"):
        resolve_pdf_backend("ocrmypdf")
