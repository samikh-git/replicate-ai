"""Modal sandbox backend using the current Sandbox.filesystem API (Modal >= 1.4)."""

from __future__ import annotations

import modal
from deepagents.backends.protocol import FileDownloadResponse, FileUploadResponse
from langchain_modal import ModalSandbox
from modal.exception import (
    SandboxFilesystemError,
    SandboxFilesystemIsADirectoryError,
    SandboxFilesystemNotFoundError,
)


class ReplicateModalSandbox(ModalSandbox):
    """ModalSandbox that reads/writes via ``sandbox.filesystem`` instead of deprecated ``open()``."""

    def _read_file(self, path: str) -> FileDownloadResponse:
        if not path.startswith("/"):
            return FileDownloadResponse(path=path, content=None, error="invalid_path")

        try:
            content_bytes = self._sandbox.filesystem.read_bytes(path)
            return FileDownloadResponse(path=path, content=content_bytes, error=None)
        except SandboxFilesystemNotFoundError:
            return FileDownloadResponse(path=path, content=None, error="file_not_found")
        except SandboxFilesystemIsADirectoryError:
            return FileDownloadResponse(path=path, content=None, error="is_directory")
        except SandboxFilesystemError:
            return FileDownloadResponse(path=path, content=None, error="file_not_found")

    def _write_file(self, path: str, content: bytes) -> FileUploadResponse:
        if not path.startswith("/"):
            return FileUploadResponse(path=path, error="invalid_path")

        try:
            self._sandbox.filesystem.write_bytes(content, path)
            return FileUploadResponse(path=path, error=None)
        except SandboxFilesystemIsADirectoryError:
            return FileUploadResponse(path=path, error="permission_denied")
        except SandboxFilesystemNotFoundError:
            return FileUploadResponse(path=path, error="file_not_found")
        except SandboxFilesystemError as e:
            msg = str(e).lower()
            if "permission" in msg:
                return FileUploadResponse(path=path, error="permission_denied")
            return FileUploadResponse(path=path, error="file_not_found")


def create_modal_backend(sandbox: modal.Sandbox) -> ReplicateModalSandbox:
    return ReplicateModalSandbox(sandbox=sandbox)
