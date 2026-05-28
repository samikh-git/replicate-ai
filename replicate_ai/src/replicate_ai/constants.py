"""Shared runtime constants."""

from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "replicate_ai"
SANDBOX_TIMEOUT_SECONDS = int(os.getenv("REPLICATE_AI_SANDBOX_TIMEOUT_SECONDS", "1800"))

DEFAULT_USER_MESSAGE = (
    "Replicate the paper's headline empirical coefficient using "
    "/workspace/data.csv and /workspace/paper_text.md.\n\n"
    "If /workspace/target_spec_reference.json exists, treat it as the "
    "curator benchmark: your /workspace/target_specification.json must "
    "target the same coefficient(s) and published values unless the paper "
    "clearly names a different headline result (log any change in "
    "/workspace/notes.md).\n\n"
    "Use the econometric method the paper uses for that result (OLS, IV, "
    "DiD, reduced form, etc.)—do not assume difference-in-differences unless "
    "the paper does. Recover published point estimates and SEs from "
    "/workspace/paper_tables.json when readable; if tables are garbled, say "
    "so in notes.md and cite paper_text.md / reference JSON explicitly.\n\n"
    "On success: /workspace/results/coefficients.json, then delegate to "
    "statistical_auditor for /workspace/replication_audit.md."
)


def resolve_user_message(
    *,
    user_message: str | None,
    example_dir: Path | None,
) -> str:
    """CLI -m override, else pack hint file, else reference JSON field, else default."""
    if user_message and user_message.strip():
        return user_message.strip()

    if example_dir is not None:
        directory = example_dir.resolve()
        hint_file = directory / "user_message.txt"
        if hint_file.is_file():
            text = hint_file.read_text(encoding="utf-8").strip()
            if text:
                return text

        reference = directory / "target_spec_reference.json"
        if reference.is_file():
            try:
                data = json.loads(reference.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
            pack_msg = data.get("user_message")
            if isinstance(pack_msg, str) and pack_msg.strip():
                return pack_msg.strip()

    return DEFAULT_USER_MESSAGE
