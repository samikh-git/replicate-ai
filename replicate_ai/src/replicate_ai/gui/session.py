"""Run session: replication worker + view state for GUI clients."""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from replicate_ai.audit_export import maybe_save_audit
from replicate_ai.gui.logfiles import LogFile
from replicate_ai.gui.serialize import view_state_to_json
from replicate_ai.runner.run import RunConfig, provider_label, run_replication
from replicate_ai.tui.demo import demo_event_stream
from replicate_ai.tui.handler import TuiViewState, apply_event


@dataclass
class RunSession:
    run_id: str
    config: RunConfig
    view: TuiViewState = field(default_factory=TuiViewState)
    started_at: float = field(default_factory=time.time)
    demo: bool = False
    save_audit: bool = True
    audit_out: Path | None = None
    audit_saved_path: Path | None = None
    log_file: LogFile | None = None
    _log_written_idx: int = 0
    _log_lock: threading.Lock = field(default_factory=threading.Lock)
    _subscribers: list[asyncio.Queue[dict]] = field(default_factory=list)
    _task: asyncio.Task | None = None
    _loop: asyncio.AbstractEventLoop | None = None

    @property
    def example_dir_display(self) -> str | None:
        if self.config.example_dir is None:
            return None
        return str(self.config.example_dir.resolve())

    @property
    def provider_display(self) -> str:
        return provider_label(self.config.provider)

    def snapshot(self) -> dict:
        return view_state_to_json(
            self.view,
            started_at=self.started_at,
            example_dir=self.example_dir_display,
            provider=self.provider_display,
        )

    def subscribe(self) -> asyncio.Queue[dict]:
        q: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers.append(q)
        q.put_nowait({"type": "snapshot", "state": self.snapshot()})
        return q

    def unsubscribe(self, q: asyncio.Queue[dict]) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def _broadcast(self) -> None:
        msg = {"type": "snapshot", "state": self.snapshot()}
        for q in list(self._subscribers):
            try:
                q.put_nowait(msg)
            except Exception:
                pass

    def _flush_new_log_lines(self) -> None:
        lf = self.log_file
        if lf is None:
            return
        with self._log_lock:
            new = self.view.log_lines[self._log_written_idx :]
            if not new:
                return
            lf.append_lines(new)
            self._log_written_idx = len(self.view.log_lines)

    def _emit(self, ev: object) -> None:
        apply_event(self.view, ev)
        from replicate_ai.tui.events import RunFinished

        if isinstance(ev, RunFinished):
            self._try_save_audit()
        self._flush_new_log_lines()
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._broadcast)

    def _try_save_audit(self) -> None:
        example_dir = self.config.example_dir
        path = maybe_save_audit(
            markdown=self.view.audit_md,
            example_dir=example_dir.resolve() if example_dir else None,
            audit_out=self.audit_out,
            enabled=self.save_audit,
        )
        if path is not None and path != self.audit_saved_path:
            self.audit_saved_path = path
            self.view.log_lines.append(f"[host] Wrote audit → {path}")

    async def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        if self.demo:
            async for ev in demo_event_stream():
                self._emit(ev)
            return

        def emit(ev: object) -> None:
            self._emit(ev)

        await asyncio.to_thread(run_replication, self.config, emit=emit)

    async def wait(self) -> None:
        if self._task is not None:
            await self._task


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, RunSession] = {}

    def create(
        self,
        config: RunConfig,
        *,
        demo: bool = False,
        save_audit: bool = True,
        audit_out: Path | None = None,
    ) -> RunSession:
        run_id = uuid.uuid4().hex[:12]
        base = config.example_dir.resolve() if config.example_dir else Path.cwd().resolve()
        log_path = base / ".replicate_ai" / "runs" / f"{run_id}.log"
        session = RunSession(
            run_id=run_id,
            config=config,
            demo=demo,
            save_audit=save_audit,
            audit_out=audit_out,
            log_file=LogFile(log_path),
        )
        self._sessions[run_id] = session
        return session

    def get(self, run_id: str) -> RunSession | None:
        return self._sessions.get(run_id)
