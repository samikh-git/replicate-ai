"""Run PDF extraction inside the Modal sandbox: python -m replicate_ai.sandbox.extract_pdf <path>."""

from __future__ import annotations

import sys

from replicate_ai.tools.pdf_core import run_pdf_extraction


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: python -m replicate_ai.sandbox.extract_pdf /workspace/paper.pdf",
            file=sys.stderr,
        )
        return 2
    try:
        print(run_pdf_extraction(sys.argv[1]))
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
