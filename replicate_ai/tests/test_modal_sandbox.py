"""Tests for ReplicateModalSandbox filesystem backend."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from modal.exception import (
    SandboxFilesystemIsADirectoryError,
    SandboxFilesystemNotFoundError,
)

from replicate_ai.modal_sandbox import ReplicateModalSandbox


@pytest.fixture
def backend() -> ReplicateModalSandbox:
    sandbox = MagicMock()
    sandbox.filesystem = MagicMock()
    return ReplicateModalSandbox(sandbox=sandbox)


class TestReplicateModalSandbox:
    def test_read_bytes_success(self, backend: ReplicateModalSandbox):
        backend._sandbox.filesystem.read_bytes.return_value = b"hello"
        resp = backend._read_file("/workspace/data.csv")
        assert resp.content == b"hello"
        assert resp.error is None
        backend._sandbox.filesystem.read_bytes.assert_called_once_with(
            "/workspace/data.csv"
        )

    def test_read_not_found(self, backend: ReplicateModalSandbox):
        backend._sandbox.filesystem.read_bytes.side_effect = (
            SandboxFilesystemNotFoundError("missing")
        )
        resp = backend._read_file("/workspace/nope.csv")
        assert resp.content is None
        assert resp.error == "file_not_found"

    def test_write_bytes_success(self, backend: ReplicateModalSandbox):
        resp = backend._write_file("/workspace/out.txt", b"data")
        assert resp.error is None
        backend._sandbox.filesystem.write_bytes.assert_called_once_with(
            b"data", "/workspace/out.txt"
        )

    def test_write_is_directory(self, backend: ReplicateModalSandbox):
        backend._sandbox.filesystem.write_bytes.side_effect = (
            SandboxFilesystemIsADirectoryError("dir")
        )
        resp = backend._write_file("/workspace", b"x")
        assert resp.error == "permission_denied"
