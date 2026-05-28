"""Command-line entry point for ReplicateAI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from replicate_ai.agent import run_agent  # noqa: E402
from replicate_ai.audit_export import maybe_save_audit  # noqa: E402
from replicate_ai.runner.run import RunConfig  # noqa: E402
from replicate_ai.tui.app import ReplicateTuiApp  # noqa: E402

try:
    from replicate_ai.gui.launch import run_gui  # noqa: E402

    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel

    _RICH_AVAILABLE = True
except Exception:  # pragma: no cover
    _RICH_AVAILABLE = False

PROVIDER_CHOICES = [
    "anthropic",
    "cloudflare-kimi",
    "cloudflare-glm",
    "kimi",
    "glm",
    "gemini",
    "groq",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replicate-ai",
        description="Run ReplicateAI on a paper PDF + dataset in an example folder.",
    )
    parser.add_argument(
        "example_dir",
        nargs="?",
        type=Path,
        help="Directory with card_krueger.pdf (or paper.pdf) and data.csv",
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Do not copy example files into the Modal sandbox /workspace",
    )
    parser.add_argument(
        "--skip-pdf-extract",
        action="store_true",
        help="Skip automatic PDF→markdown extraction (paper_text.md must already exist)",
    )
    parser.add_argument(
        "--pdf-backend",
        choices=("docling", "legacy"),
        default=None,
        help=(
            "Host PDF extractor: docling (default, layout-aware tables) or "
            "legacy (pymupdf4llm + Camelot). Overrides REPLICATE_AI_PDF_BACKEND."
        ),
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Override the default user message",
    )
    parser.add_argument(
        "-p",
        "--provider",
        choices=PROVIDER_CHOICES,
        help=(
            "LLM provider (default: LLM_PROVIDER env or anthropic). "
            "Use cloudflare-glm for cheap harness tests; cloudflare-kimi for "
            "full dry runs; anthropic for the canonical demo; gemini for Google AI; "
            "groq for low-latency inference."
        ),
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Force launch the Textual TUI (requires a TTY).",
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Disable the TUI (useful for CI / piping output).",
    )
    parser.add_argument(
        "--tui-demo",
        action="store_true",
        help="Launch the TUI with fake demo data (shell-only milestone).",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the browser GUI (local server on 127.0.0.1).",
    )
    parser.add_argument(
        "--gui-demo",
        action="store_true",
        help="Launch the GUI with fake demo data (no Modal / LLM).",
    )
    parser.add_argument(
        "--audit-out",
        type=Path,
        metavar="PATH",
        help=(
            "Write replication_audit.md to PATH on the host after the run. "
            "Default when example_dir is set: <example_dir>/replication_audit.md"
        ),
    )
    parser.add_argument(
        "--no-save-audit",
        action="store_true",
        help="Do not write replication_audit.md to disk (TUI still allows s to save).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    no_tui_env = os.getenv("REPLICATE_AI_NO_TUI")
    tui_allowed = sys.stdout.isatty() and not args.no_tui and not no_tui_env

    example_dir: Path | None = None
    if args.example_dir is not None:
        example_dir = args.example_dir.resolve()
        if not example_dir.is_dir():
            parser.error(f"Not a directory: {example_dir}")
        if args.no_seed:
            example_dir = None

    if args.gui_demo or args.gui:
        if not _GUI_AVAILABLE:
            parser.error(
                "GUI requires optional dependencies. Run: uv sync --group gui"
            )
        if args.gui_demo:
            run_gui(demo=True, save_audit=not args.no_save_audit, audit_out=args.audit_out)
            return
        initial = None
        if example_dir is not None:
            initial = RunConfig(
                example_dir=example_dir,
                provider=args.provider,
                user_message=args.message,
                skip_pdf_extract=args.skip_pdf_extract,
                pdf_backend=args.pdf_backend,
            )
        run_gui(
            initial=initial,
            save_audit=not args.no_save_audit,
            audit_out=args.audit_out,
        )
        return

    if args.tui_demo:
        ReplicateTuiApp(demo=True).run()
        return

    use_tui = tui_allowed and (args.tui or example_dir is not None) and not args.gui
    if use_tui:
        if example_dir is None and not args.tui_demo:
            parser.error("example_dir is required for the TUI (or use --tui-demo)")
        ReplicateTuiApp(
            run_config=RunConfig(
                example_dir=example_dir,
                provider=args.provider,
                user_message=args.message,
                skip_pdf_extract=args.skip_pdf_extract,
                pdf_backend=args.pdf_backend,
            ),
            audit_out=None if args.no_save_audit else args.audit_out,
            save_audit=not args.no_save_audit,
        ).run()
        return

    result = run_agent(
        user_message=args.message,
        provider=args.provider,
        example_dir=example_dir,
        skip_pdf_extract=args.skip_pdf_extract,
        pdf_backend=args.pdf_backend,
    )
    audit_md = None
    if isinstance(result, dict):
        audit_md = result.get("replication_audit_md")

    saved = maybe_save_audit(
        markdown=audit_md,
        example_dir=args.example_dir.resolve() if args.example_dir else None,
        audit_out=args.audit_out,
        enabled=not args.no_save_audit,
    )
    if saved is not None:
        print(f"Wrote audit → {saved}")

    if _RICH_AVAILABLE and audit_md:
        console = Console()
        console.print(
            Panel.fit(
                Markdown(audit_md),
                title="replication_audit.md",
                border_style="cyan",
            )
        )
    elif audit_md is None:
        print(result)


if __name__ == "__main__":
    main(sys.argv[1:])
