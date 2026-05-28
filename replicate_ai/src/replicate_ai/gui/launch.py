"""Start the GUI server and open a browser window."""

from __future__ import annotations

import asyncio
import socket
import webbrowser
from pathlib import Path

import uvicorn

from replicate_ai.gui.examples_scan import find_examples_root
from replicate_ai.gui.server import create_app
from replicate_ai.gui.session import RunSession, SessionStore
from replicate_ai.runner.run import RunConfig


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def run_gui(
    *,
    initial: RunConfig | None = None,
    demo: bool = False,
    audit_out: Path | None = None,
    save_audit: bool = True,
    examples_root: Path | None = None,
    open_browser: bool = True,
) -> None:
    """Block until the GUI server is stopped (Ctrl+C)."""
    port = _free_port()
    store = SessionStore()
    initial_session: RunSession | None = None

    if demo or initial is not None:
        config = initial or RunConfig(example_dir=None)
        initial_session = store.create(
            config,
            demo=demo,
            save_audit=save_audit,
            audit_out=audit_out,
        )

    root = examples_root or find_examples_root()
    app = create_app(
        store=store,
        examples_root=root,
        initial_session=initial_session,
    )

    async def _start_initial_run() -> None:
        if initial_session is not None:
            loop = asyncio.get_running_loop()
            await initial_session.start(loop)

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    if initial_session is not None:
        url = f"http://127.0.0.1:{port}/run.html?id={initial_session.run_id}"
    else:
        url = f"http://127.0.0.1:{port}/"

    if open_browser:
        webbrowser.open(url)

    print(f"ReplicateAI GUI at {url}")
    print("Press Ctrl+C to stop.")

    async def serve() -> None:
        await _start_initial_run()
        await server.serve()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass
