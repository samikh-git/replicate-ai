from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Markdown, RichLog, Static

from replicate_ai.audit_export import maybe_save_audit
from replicate_ai.runner.run import RunConfig, run_replication
from replicate_ai.tui.demo import demo_event_stream
from replicate_ai.tui.format import format_ci_strip, format_headline_card, format_model_spec
from replicate_ai.tui.handler import TuiViewState, apply_event
from replicate_ai.tui.theme import TOKENS


@dataclass
class HeaderState:
    example_dir: str = "examples/card_krueger"
    provider: str = "Anthropic / Sonnet 4.6"
    phase_display: str = "Read paper"
    started_at: float = 0.0


class Header(Static):
    def __init__(self, state: HeaderState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state

    def render(self) -> Text:
        elapsed = "00:00:00"
        if self.state.started_at:
            dt = max(0, int(time.time() - self.state.started_at))
            h, rem = divmod(dt, 3600)
            m, s = divmod(rem, 60)
            elapsed = f"{h:02d}:{m:02d}:{s:02d}"

        title = Text("ReplicateAI", style=TOKENS.accent)
        meta = Text(
            f"{self.state.example_dir}  ·  {self.state.provider}  ·  {elapsed}",
            style=TOKENS.dim,
        )

        phases = ["Read paper", "Specify", "Estimate", "Audit"]
        row = Text()
        for p in phases:
            is_active = p == self.state.phase_display
            glyph = "●" if is_active else "○"
            glyph_style = TOKENS.accent if is_active else TOKENS.dim
            row.append(f"{glyph} ", style=glyph_style)
            row.append(p, style=(TOKENS.accent if is_active else TOKENS.dim))
            row.append("    ", style=TOKENS.dim)

        out = Text()
        out.append_text(title)
        out.append("\n")
        out.append_text(meta)
        out.append("\n\n")
        out.append_text(row)
        return out


class ReplicateTuiApp(App):
    """ReplicateAI dashboard TUI (docs/DESIGN_TUI.md)."""

    CSS = """
    Screen {
        padding: 1 2;
    }

    #header {
        height: 6;
        padding: 0 0 1 0;
    }

    #main {
        height: 1fr;
    }

    #logPane {
        width: 1fr;
        margin-right: 1;
        border: round $panel;
    }

    #detailPane {
        width: 1fr;
        margin-left: 1;
        border: round $panel;
    }

    #detailScroll {
        height: 1fr;
    }

    #runningHead {
        height: 1;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "quit"),
        ("r", "rerun", "rerun"),
        ("s", "save_audit", "save audit"),
        ("tab", "focus_next", "focus next"),
        ("shift+tab", "focus_previous", "focus prev"),
        ("g", "log_top", "log top"),
        ("G", "log_bottom", "log bottom"),
    ]

    def __init__(
        self,
        *,
        demo: bool = False,
        run_config: RunConfig | None = None,
        audit_out: Path | None = None,
        save_audit: bool = True,
    ) -> None:
        super().__init__()
        self._demo = demo
        self._run_config = run_config
        self._audit_out = audit_out
        self._save_audit = save_audit
        self._audit_saved_path: Path | None = None
        self._view = TuiViewState()
        self._header_state = HeaderState()
        if run_config is not None and run_config.example_dir is not None:
            self._header_state.example_dir = str(run_config.example_dir)
        if run_config is not None:
            from replicate_ai.runner.run import provider_label

            self._header_state.provider = provider_label(run_config.provider)

    def compose(self) -> ComposeResult:
        yield Header(self._header_state, id="header")
        with Horizontal(id="main"):
            with Vertical(id="logPane"):
                yield Static("Run log", classes="title")
                yield RichLog(id="log", highlight=False, markup=False, wrap=True)
            with Vertical(id="detailPane"):
                yield Static("Detail", classes="title")
                with VerticalScroll(id="detailScroll"):
                    yield Static(id="detailTop")
                    yield Markdown(id="detailMarkdown")
        yield Static("", id="runningHead")
        yield Footer()

    async def on_mount(self) -> None:
        self._header_state.started_at = time.time()
        self.set_interval(0.25, self._tick_header)
        if self._demo:
            self.run_worker(self._run_demo(), exclusive=True, name="demo")
        elif self._run_config is not None:
            self.run_worker(self._run_real(), exclusive=True, name="replication")
        else:
            await self._append_log("[agent] No run configuration. Pass an example directory.")

    def _tick_header(self) -> None:
        self._header_state.phase_display = self._view.phase_display
        self.query_one(Header).refresh()

    async def _append_log(self, line: str) -> None:
        self.query_one("#log", RichLog).write(line)

    def _sync_view_to_widgets(self) -> None:
        self._set_running_head(self._view.running_head)
        self._render_detail()

    def _set_running_head(self, text: str) -> None:
        self.query_one("#runningHead", Static).update(Text(text, style=TOKENS.dim))

    def _render_detail(self) -> None:
        top = self.query_one("#detailTop", Static)
        md = self.query_one("#detailMarkdown", Markdown)
        coeffs = self._view.coeffs
        audit_md = self._view.audit_md

        if coeffs is None and not audit_md:
            top.update(Text("Waiting for target specification and estimates…", style=TOKENS.dim))
            md.update("")
            return

        if coeffs is not None:
            top.update(format_model_spec(coeffs.model_spec))
            card = format_headline_card(
                estimate_label=coeffs.estimate_label,
                estimate=coeffs.estimate,
                estimate_se=coeffs.estimate_se,
                estimate_stars=coeffs.estimate_stars,
                published=coeffs.published,
                published_se=coeffs.published_se,
                published_stars=coeffs.published_stars,
                delta=coeffs.delta,
                verdict=coeffs.verdict,
                decimals=2,
            )
            ci = format_ci_strip(
                estimate=coeffs.estimate,
                estimate_se=coeffs.estimate_se,
                published=coeffs.published,
                published_se=coeffs.published_se,
            )
            blocks = ["```text", card, "", ci, "```", "", coeffs.citation_line]
            if audit_md:
                blocks += ["", audit_md]
            md.update("\n".join(blocks))
            return

        top.update(Text("", style=TOKENS.dim))
        md.update(audit_md or "")

    async def _apply_and_refresh(self, ev: object) -> None:
        from replicate_ai.tui.events import RunFinished

        prev_log_len = len(self._view.log_lines)
        apply_event(self._view, ev)
        if isinstance(ev, RunFinished):
            self._try_save_audit()
        for line in self._view.log_lines[prev_log_len:]:
            await self._append_log(line)
        self._sync_view_to_widgets()

    def _example_dir(self) -> Path | None:
        if self._run_config is None or self._run_config.example_dir is None:
            return None
        return self._run_config.example_dir.resolve()

    def _try_save_audit(self) -> Path | None:
        path = maybe_save_audit(
            markdown=self._view.audit_md,
            example_dir=self._example_dir(),
            audit_out=self._audit_out,
            enabled=self._save_audit,
        )
        if path is not None and path != self._audit_saved_path:
            self._audit_saved_path = path
            self._view.log_lines.append(f"[host] Wrote audit → {path}")
        return path

    def action_save_audit(self) -> None:
        """Write replication_audit.md to disk (default: example_dir)."""
        log = self.query_one("#log", RichLog)
        if not self._view.audit_md:
            log.write("[host] No audit to save yet.")
            return
        path = maybe_save_audit(
            markdown=self._view.audit_md,
            example_dir=self._example_dir(),
            audit_out=self._audit_out,
            enabled=True,
        )
        if path is None:
            log.write("[host] Pass an example directory or use --audit-out PATH.")
            return
        self._audit_saved_path = path
        log.write(f"[host] Wrote audit → {path}")

    async def _run_demo(self) -> None:
        async for ev in demo_event_stream():
            await self._apply_and_refresh(ev)

    async def _run_real(self) -> None:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def emit(ev: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, ev)

        async def drain() -> None:
            while True:
                ev = await queue.get()
                await self._apply_and_refresh(ev)
                from replicate_ai.tui.events import RunFinished

                if isinstance(ev, RunFinished):
                    return

        drain_task = asyncio.create_task(drain())
        try:
            await asyncio.to_thread(
                run_replication,
                self._run_config,
                emit=emit,
            )
        finally:
            await drain_task

    def _reset_run(self) -> None:
        self._view = TuiViewState()
        self._audit_saved_path = None
        self._header_state.started_at = time.time()
        self._header_state.phase_display = "Read paper"
        self.query_one("#log", RichLog).clear()
        self._set_running_head("")
        self._render_detail()

    def action_rerun(self) -> None:
        self._reset_run()
        if self._demo:
            self.run_worker(self._run_demo(), exclusive=True, name="demo")
        elif self._run_config is not None:
            self.run_worker(self._run_real(), exclusive=True, name="replication")

    def action_log_top(self) -> None:
        self.query_one("#log", RichLog).scroll_home(animate=False)

    def action_log_bottom(self) -> None:
        self.query_one("#log", RichLog).scroll_end(animate=False)
