"""Tests for GUI HTTP API."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from replicate_ai.gui.examples_scan import list_example_packs
from replicate_ai.gui.server import create_app
from replicate_ai.gui.uploads import ingest_files_mode, new_pack_dir


@pytest.fixture
def examples_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "examples"
    if not root.is_dir():
        pytest.skip("examples/ not found")
    return root


@pytest.fixture
def client(examples_root: Path) -> TestClient:
    return TestClient(create_app(examples_root=examples_root))


class TestGuiApi:
    def test_list_examples(self, client: TestClient, examples_root: Path):
        r = client.get("/api/examples")
        assert r.status_code == 200
        data = r.json()
        assert len(data["examples"]) >= 1
        ids = {e["id"] for e in data["examples"]}
        assert "card_krueger" in ids

    def test_config(self, client: TestClient):
        r = client.get("/api/config")
        assert r.status_code == 200
        assert "providers" in r.json()

    def test_upload_files_mode(self, tmp_path: Path):
        pack = new_pack_dir()
        # minimal fake pdf/csv bytes
        pdf = b"%PDF-1.4\n"
        csv = b"a,b\n1,2\n"

        class _Stream:
            def __init__(self, data: bytes) -> None:
                self._data = data
                self._done = False

            async def read(self, n: int = -1) -> bytes:
                if self._done:
                    return b""
                self._done = True
                return self._data

        import asyncio

        async def _run():
            return await ingest_files_mode(
                paper_stream=_Stream(pdf),
                paper_filename="paper.pdf",
                data_stream=_Stream(csv),
                data_filename="data.csv",
            )

        result = asyncio.run(_run())
        assert result.pack_path.is_dir()
        assert (result.pack_path / "paper.pdf").is_file()

    def test_upload_rejects_missing_csv(self, client: TestClient):
        pdf = ("paper", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")
        r = client.post(
            "/api/upload",
            files={"paper": pdf},
            data={},
        )
        assert r.status_code in (400, 500)
        body = r.json()
        assert "error" in body

    def test_create_run_requires_directory(self, client: TestClient):
        r = client.post("/api/runs", json={})
        assert r.status_code == 400
        r2 = client.post("/api/runs", json={"example_dir": "/nonexistent/path/xyz"})
        assert r2.status_code == 400
