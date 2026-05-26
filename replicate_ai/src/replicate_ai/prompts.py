"""Load system prompts from markdown files next to this module."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "system_prompts"


def load_prompt(name: str) -> str:
    path = _PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


ECONOMETRICIAN_PROMPT = load_prompt("ECONOMETRICIAN_PROMPT.md")
AUDITOR_PROMPT = load_prompt("AUDITOR.md")
