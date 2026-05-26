"""Modal sandbox workspace at /workspace (no host-side workspace directory)."""

from __future__ import annotations

from pathlib import Path

import modal

from replicate_ai.example_assets import find_example_data_csv, find_example_pdf
from replicate_ai.modal_sandbox import ReplicateModalSandbox

SANDBOX_WORKSPACE = "/workspace"

_sandbox_backend: ReplicateModalSandbox | None = None
_modal_sandbox: modal.Sandbox | None = None


def set_sandbox_backend(backend: ReplicateModalSandbox | None) -> None:
    global _sandbox_backend
    _sandbox_backend = backend


def get_sandbox_backend() -> ReplicateModalSandbox | None:
    return _sandbox_backend


def set_modal_sandbox(sandbox: modal.Sandbox | None) -> None:
    global _modal_sandbox
    _modal_sandbox = sandbox


def seed_example_to_sandbox(example_dir: Path | None = None) -> list[str]:
    """Copy paper.pdf and data.csv from an example folder into /workspace."""
    if example_dir is None:
        return []
    directory = example_dir.resolve()

    sandbox = _modal_sandbox
    if sandbox is None:
        raise RuntimeError("Modal sandbox not initialized; cannot seed /workspace")

    fs = sandbox.filesystem
    fs.make_directory(SANDBOX_WORKSPACE, create_parents=True)

    pdf = find_example_pdf(directory)
    if pdf is None:
        raise FileNotFoundError(
            f"No paper PDF found in {directory}. "
            "Add paper.pdf or {dirname}.pdf (see examples/README.md)."
        )
    data_csv = find_example_data_csv(directory)
    if data_csv is None:
        raise FileNotFoundError(
            f"No data.csv found in {directory}. "
            "Run data_population_script.py in the example pack."
        )

    seeded: list[str] = []
    for dest_name, src in (("paper.pdf", pdf), ("data.csv", data_csv)):
        remote = f"{SANDBOX_WORKSPACE}/{dest_name}"
        fs.copy_from_local(src, remote)
        seeded.append(remote)
    return seeded


def upload_local_files_to_sandbox(files: list[tuple[Path, str]]) -> list[str]:
    """Upload (local_path, remote_absolute_path) pairs into the Modal sandbox."""
    sandbox = _modal_sandbox
    if sandbox is None:
        raise RuntimeError("Modal sandbox not initialized; cannot upload files")

    fs = sandbox.filesystem
    fs.make_directory(SANDBOX_WORKSPACE, create_parents=True)
    uploaded: list[str] = []
    for local_path, remote_path in files:
        fs.copy_from_local(local_path.resolve(), remote_path)
        uploaded.append(remote_path)
    return uploaded
