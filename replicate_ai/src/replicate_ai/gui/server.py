"""Starlette application for the ReplicateAI browser GUI."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from replicate_ai.gui.examples_scan import (
    default_provider,
    find_examples_root,
    list_example_packs,
    load_providers,
)
from replicate_ai.gui.logfiles import read_tail
from replicate_ai.gui.session import RunSession, SessionStore
from replicate_ai.gui.uploads import (
    cleanup_upload_root,
    ingest_directory_mode,
    ingest_files_mode,
)
from replicate_ai.runner.run import RunConfig

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _json_error(message: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def create_app(
    *,
    store: SessionStore | None = None,
    examples_root: Path | None = None,
    initial_session: RunSession | None = None,
) -> Starlette:
    sessions = store or SessionStore()
    _examples_root = examples_root

    async def api_config(request: Request) -> JSONResponse:
        root = _examples_root or find_examples_root()
        return JSONResponse(
            {
                "examples_root": str(root) if root else None,
                "default_provider": default_provider(),
                "providers": load_providers(),
                "initial_run_id": initial_session.run_id if initial_session else None,
            }
        )

    async def api_examples(request: Request) -> JSONResponse:
        root = _examples_root or find_examples_root()
        if root is None:
            return JSONResponse({"examples": [], "error": "examples/ directory not found"})
        return JSONResponse({"examples": list_example_packs(root)})

    async def api_upload(request: Request) -> JSONResponse:
        mode = request.query_params.get("mode", "files")
        try:
            if mode == "directory":
                form = await request.form()
                file_items = form.getlist("files")
                if not file_items:
                    return _json_error("No files in directory upload")
                pairs: list[tuple[str, object]] = []
                for item in file_items:
                    rel = getattr(item, "filename", None) or "file"
                    pairs.append((rel, item))
                result = await ingest_directory_mode(pairs)
            else:
                form = await request.form()
                paper = form.get("paper")
                data = form.get("data")
                if paper is None or data is None:
                    return _json_error("Expected multipart fields 'paper' and 'data'")
                result = await ingest_files_mode(
                    paper_stream=paper,
                    paper_filename=getattr(paper, "filename", "paper.pdf"),
                    data_stream=data,
                    data_filename=getattr(data, "filename", "data.csv"),
                )
            return JSONResponse(
                {
                    "pack_path": str(result.pack_path),
                    "paper_filename": result.paper_filename,
                    "data_filename": result.data_filename,
                    "total_bytes": result.total_bytes,
                    "warnings": result.warnings,
                }
            )
        except ValueError as e:
            return _json_error(str(e))
        except Exception as e:
            return _json_error(f"Upload failed: {e}", status=500)

    async def api_create_run(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return _json_error("Invalid JSON body")

        example_dir_raw = body.get("example_dir") or body.get("pack_path")
        if not example_dir_raw:
            return _json_error("example_dir or pack_path is required")

        example_dir = Path(example_dir_raw).resolve()
        if not example_dir.is_dir():
            return _json_error(f"Not a directory: {example_dir}")

        provider = body.get("provider")
        message = body.get("message")
        skip_pdf = bool(body.get("skip_pdf_extract", False))
        pdf_backend = body.get("pdf_backend")

        config = RunConfig(
            example_dir=example_dir,
            provider=provider,
            user_message=message,
            skip_pdf_extract=skip_pdf,
            pdf_backend=pdf_backend,
        )
        session = sessions.create(
            config,
            save_audit=body.get("save_audit", True),
        )
        loop = asyncio.get_running_loop()
        await session.start(loop)
        return JSONResponse({"run_id": session.run_id})

    async def api_get_run(request: Request) -> JSONResponse:
        run_id = request.path_params["run_id"]
        session = sessions.get(run_id)
        if session is None:
            return _json_error("Run not found", status=404)
        return JSONResponse(session.snapshot())

    async def api_run_events(request: Request) -> StreamingResponse:
        run_id = request.path_params["run_id"]
        session = sessions.get(run_id)
        if session is None:
            return _json_error("Run not found", status=404)

        queue = session.subscribe()

        async def event_stream():
            try:
                while True:
                    try:
                        msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
                        continue
                    data = json.dumps(msg)
                    yield f"data: {data}\n\n"
                    finished = msg.get("state", {}).get("finished")
                    if finished is not None:
                        break
            finally:
                session.unsubscribe(queue)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    async def api_save_audit(request: Request) -> JSONResponse:
        run_id = request.path_params["run_id"]
        session = sessions.get(run_id)
        if session is None:
            return _json_error("Run not found", status=404)
        if not session.view.audit_md:
            return _json_error("No audit to save yet")
        session.save_audit = True
        session._try_save_audit()
        if session.audit_saved_path:
            return JSONResponse({"path": str(session.audit_saved_path)})
        return _json_error("Could not save audit (pass example_dir or audit_out)")

    async def api_run_log(request: Request) -> Response:
        run_id = request.path_params["run_id"]
        session = sessions.get(run_id)
        if session is None:
            return _json_error("Run not found", status=404)
        if session.log_file is None:
            return _json_error("No log file configured", status=404)
        tail_kb = request.query_params.get("tail_kb")
        try:
            max_bytes = int(tail_kb) * 1024 if tail_kb else 200_000
        except Exception:
            max_bytes = 200_000
        text = read_tail(session.log_file.path, max_bytes=max_bytes)
        filename = f"replicateai-run-{run_id}.log"
        return Response(
            text,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    routes: list[Any] = [
        Route("/api/config", api_config, methods=["GET"]),
        Route("/api/examples", api_examples, methods=["GET"]),
        Route("/api/upload", api_upload, methods=["POST"]),
        Route("/api/runs", api_create_run, methods=["POST"]),
        Route("/api/runs/{run_id}", api_get_run, methods=["GET"]),
        Route("/api/runs/{run_id}/events", api_run_events, methods=["GET"]),
        Route("/api/runs/{run_id}/log", api_run_log, methods=["GET"]),
        Route("/api/runs/{run_id}/save-audit", api_save_audit, methods=["POST"]),
    ]

    if STATIC_DIR.is_dir():
        routes.append(
            Mount(
                "/",
                StaticFiles(directory=str(STATIC_DIR), html=True),
                name="static",
            )
        )

    @asynccontextmanager
    async def lifespan(app: Starlette):
        yield
        cleanup_upload_root()

    app = Starlette(routes=routes, lifespan=lifespan)

    if initial_session is not None:
        sessions._sessions[initial_session.run_id] = initial_session

    return app
