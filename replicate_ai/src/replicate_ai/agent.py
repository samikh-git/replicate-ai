"""ReplicateAI agent: builds and runs a Deep Agent on a Modal sandbox."""

from __future__ import annotations

from pathlib import Path

from replicate_ai.constants import DEFAULT_USER_MESSAGE
from replicate_ai.models import provider_summary
from replicate_ai.runner.run import RunConfig, run_replication


def run_agent(
    *,
    user_message: str | None = None,
    provider: str | None = None,
    example_dir: Path | None = None,
    skip_pdf_extract: bool = False,
    pdf_backend: str | None = None,
    emit=None,
) -> dict:
    """Create a Modal sandbox, build the deep agent, and invoke it once."""
    print(f"LLM: {provider_summary(provider)}")

    return run_replication(
        RunConfig(
            example_dir=example_dir,
            provider=provider,
            user_message=user_message,
            skip_pdf_extract=skip_pdf_extract,
            pdf_backend=pdf_backend,
        ),
        emit=emit,
    )
