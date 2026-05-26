"""Run replication with structured TUI events."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import modal
from deepagents import create_deep_agent
from modal.exception import SandboxFilesystemNotFoundError

from replicate_ai.constants import APP_NAME, DEFAULT_USER_MESSAGE, SANDBOX_TIMEOUT_SECONDS
from replicate_ai.modal_sandbox import create_modal_backend
from replicate_ai.models import get_chat_model, provider_summary
from replicate_ai.preflight import (
    cleanup_extract_dir,
    extract_paper_locally,
    find_example_pdf,
    upload_extract_artifacts,
)
from replicate_ai.prompts import ECONOMETRICIAN_PROMPT
from replicate_ai.runner.log_poll import LogTailer
from replicate_ai.runner.parse import parse_coefficients_event
from replicate_ai.sandbox_image import build_sandbox_image
from replicate_ai.subagents.auditor import auditor_subagent
from replicate_ai.tui.events import (
    AuditReady,
    DeliverableWritten,
    LogChunk,
    Phase,
    PhaseChanged,
    RunFinished,
    Status,
)
from replicate_ai.workspace import (
    SANDBOX_WORKSPACE,
    seed_example_to_sandbox,
    set_modal_sandbox,
    set_sandbox_backend,
)

EmitFn = Callable[[object], None]

DELIVERABLE_PATHS: dict[str, str] = {
    "target_specification.json": f"{SANDBOX_WORKSPACE}/target_specification.json",
    "results/coefficients.json": f"{SANDBOX_WORKSPACE}/results/coefficients.json",
    "replication_audit.md": f"{SANDBOX_WORKSPACE}/replication_audit.md",
}


@dataclass(frozen=True)
class RunConfig:
    example_dir: Path | None = None
    provider: str | None = None
    user_message: str | None = None
    skip_pdf_extract: bool = False


def _noop_emit(_: object) -> None:
    return None


def _read_file(fs, path: str) -> str | None:
    try:
        return fs.read_bytes(path).decode("utf-8", errors="replace")
    except SandboxFilesystemNotFoundError:
        return None
    except Exception:
        return None


def _read_nonempty_file(fs, path: str, *, min_len: int = 3) -> str | None:
    text = _read_file(fs, path)
    if text is None or len(text.strip()) < min_len:
        return None
    return text


def _emit_coefficients_if_ready(fs, *, emit: EmitFn) -> bool:
    coeff_text = _read_nonempty_file(fs, DELIVERABLE_PATHS["results/coefficients.json"])
    if coeff_text is None:
        return False
    target_text = _read_nonempty_file(fs, DELIVERABLE_PATHS["target_specification.json"])
    if target_text is None:
        return False
    parsed = parse_coefficients_event(target_text, coeff_text)
    if parsed is not None:
        emit(parsed)
        return True
    return False


def _poll_deliverables(
    fs,
    *,
    seen: set[str],
    emit: EmitFn,
    coeffs_emitted: list[bool],
) -> None:
    for name, path in DELIVERABLE_PATHS.items():
        if name in seen:
            continue
        text = _read_nonempty_file(fs, path)
        if text is None:
            continue
        seen.add(name)
        emit(DeliverableWritten(name))  # type: ignore[arg-type]
        if name == "replication_audit.md":
            emit(AuditReady(text))

    if not coeffs_emitted[0]:
        if _emit_coefficients_if_ready(fs, emit=emit):
            coeffs_emitted[0] = True


def _agent_poll_loop(
    fs,
    *,
    stop: threading.Event,
    emit: EmitFn,
    deliverables_seen: set[str],
    coeffs_emitted: list[bool],
    poll_interval: float = 1.5,
) -> None:
    tailer = LogTailer()
    while not stop.is_set():
        _poll_deliverables(
            fs,
            seen=deliverables_seen,
            emit=emit,
            coeffs_emitted=coeffs_emitted,
        )
        for line in tailer.poll(fs):
            emit(LogChunk(f"[sandbox] {line}", source="sandbox"))
        stop.wait(poll_interval)


def run_replication(
    config: RunConfig,
    *,
    emit: EmitFn | None = None,
) -> dict[str, Any]:
    """Run the full replication pipeline, emitting TUI events when ``emit`` is set."""
    emit = emit or _noop_emit
    extract_dir: Path | None = None
    modal_sandbox = None
    success = False
    error: str | None = None
    invoke_result: dict[str, Any] | None = None

    try:
        emit(PhaseChanged(Phase.preflight))
        if config.example_dir is not None and not config.skip_pdf_extract:
            pdf = find_example_pdf(config.example_dir)
            if pdf is not None:
                extract_dir, summary = extract_paper_locally(pdf)
                emit(LogChunk(f"[host] Local PDF extract: {summary}", source="host"))
                if "0 tables" in summary.lower():
                    emit(
                        Status(
                            "Camelot found no tables; agent will rely on paper_text.md.",
                            source="host",
                        )
                    )

        emit(PhaseChanged(Phase.seeding))
        app = modal.App.lookup(APP_NAME, create_if_missing=True)
        image = build_sandbox_image()
        modal_sandbox = modal.Sandbox.create(
            app=app,
            image=image,
            timeout=SANDBOX_TIMEOUT_SECONDS,
        )
        backend = create_modal_backend(modal_sandbox)
        set_sandbox_backend(backend)
        set_modal_sandbox(modal_sandbox)
        fs = modal_sandbox.filesystem

        seeded = seed_example_to_sandbox(config.example_dir)
        if seeded:
            emit(
                LogChunk(
                    f"[host] Seeded {len(seeded)} file(s) into /workspace from {config.example_dir}",
                    source="host",
                )
            )

        if extract_dir is not None:
            uploaded = upload_extract_artifacts(extract_dir)
            emit(
                LogChunk(
                    f"[host] Uploaded {len(uploaded)} extraction artifact(s) to /workspace",
                    source="host",
                )
            )

        emit(PhaseChanged(Phase.agent))
        deliverables_seen: set[str] = set()
        coeffs_emitted = [False]
        stop_poll = threading.Event()
        poll_thread = threading.Thread(
            target=_agent_poll_loop,
            kwargs={
                "fs": fs,
                "stop": stop_poll,
                "emit": emit,
                "deliverables_seen": deliverables_seen,
                "coeffs_emitted": coeffs_emitted,
            },
            daemon=True,
        )
        poll_thread.start()

        agent = create_deep_agent(
            model=get_chat_model(config.provider),
            tools=[],
            system_prompt=ECONOMETRICIAN_PROMPT,
            subagents=[auditor_subagent],
            backend=backend,
        )
        invoke_result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": config.user_message or DEFAULT_USER_MESSAGE,
                    }
                ]
            }
        )

        stop_poll.set()
        poll_thread.join(timeout=5.0)
        _poll_deliverables(
            fs,
            seen=deliverables_seen,
            emit=emit,
            coeffs_emitted=coeffs_emitted,
        )

        emit(PhaseChanged(Phase.audit))
        audit_md = _read_nonempty_file(fs, DELIVERABLE_PATHS["replication_audit.md"])
        if audit_md:
            if "replication_audit.md" not in deliverables_seen:
                emit(DeliverableWritten("replication_audit.md"))
            emit(AuditReady(audit_md))
        else:
            error = "Agent finished without writing replication_audit.md"

        if not coeffs_emitted[0]:
            _emit_coefficients_if_ready(fs, emit=emit)

        emit(PhaseChanged(Phase.done))
        success = audit_md is not None
        if isinstance(invoke_result, dict):
            invoke_result = {**invoke_result, "replication_audit_md": audit_md}
        else:
            invoke_result = {"result": invoke_result, "replication_audit_md": audit_md}
        return invoke_result
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        emit(RunFinished(success=success, error=error))
        cleanup_extract_dir(extract_dir)
        set_sandbox_backend(None)
        set_modal_sandbox(None)
        if modal_sandbox is not None:
            modal_sandbox.terminate()


def provider_label(provider: str | None) -> str:
    return provider_summary(provider)
