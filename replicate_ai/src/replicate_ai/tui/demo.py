from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from replicate_ai.tui.events import (
    AuditReady,
    CoefficientsParsed,
    DeliverableWritten,
    LogChunk,
    Phase,
    PhaseChanged,
    RunFinished,
    Status,
)


async def demo_event_stream() -> AsyncIterator[object]:
    """Deterministic fake event stream to validate the UI shell.

    This intentionally mirrors docs/DESIGN_TUI.md §6.1 and §6.2.
    """
    yield PhaseChanged(Phase.preflight)
    yield LogChunk("[host] Local PDF extract: 26 pages · 0 tables · paper_text.md 108k chars", source="host")
    yield Status("Camelot yielded 0 tables; relying on paper_text.md.", source="host")
    await asyncio.sleep(0.5)

    yield PhaseChanged(Phase.seeding)
    yield LogChunk("[host] Seeded 2 file(s) into /workspace", source="host")
    yield LogChunk("[host] Uploaded 2 artifact(s) to /workspace", source="host")
    await asyncio.sleep(0.5)

    yield PhaseChanged(Phase.agent)
    yield LogChunk("[agent] Reading paper_text.md and drafting target_specification.json…", source="agent")
    await asyncio.sleep(0.6)
    yield DeliverableWritten("target_specification.json")

    yield LogChunk("[agent] Writing scripts/00_inspect.py and running it…", source="agent")
    await asyncio.sleep(0.6)
    yield LogChunk("[sandbox] 00_inspect.py: df.shape=(410, 46)", source="sandbox")
    await asyncio.sleep(0.4)

    yield LogChunk("[agent] Writing scripts/attempt_01.py…", source="agent")
    await asyncio.sleep(0.7)
    yield LogChunk("[sandbox] attempt_01.py: KeyError: 'wage_st' (nbsp bug)", source="sandbox")
    await asyncio.sleep(0.6)
    yield LogChunk("[agent] Fixing column normalization and re-running…", source="agent")
    await asyncio.sleep(0.6)

    yield DeliverableWritten("results/coefficients.json")
    yield CoefficientsParsed(
        model_spec="fte_it = α + β · nj_i × post_t + γ · chain_i + δ · co_owned_i + ε_it",
        estimate_label="β̂ (NJ × Post)",
        estimate=2.85,
        estimate_se=1.32,
        estimate_stars="**",
        published=2.76,
        published_se=1.36,
        published_stars="*",
        delta=0.09,
        verdict="ok",
        citation_line="Card & Krueger (1994), AER 84(4), Table 3, row 4",
    )
    await asyncio.sleep(0.6)

    yield PhaseChanged(Phase.audit)
    yield DeliverableWritten("replication_audit.md")
    yield AuditReady(
        markdown=(
            "## Replication audit\n\n"
            "**Verdict**: ✓ within tolerance\n\n"
            "- Published (Table 3, row 4): **2.76** (SE **1.36**)\n"
            "- Replicated: **2.85** (SE **1.32**)\n"
            "- Difference: **+0.09**\n\n"
            "### Notes\n"
            "- `paper_tables.json` was sparse; table values were recovered from `paper_text.md`.\n"
            "- The planted `nbsp` bug in the `wage_st` header required a normalization pass.\n"
        )
    )
    await asyncio.sleep(0.8)

    yield PhaseChanged(Phase.done)
    yield RunFinished(success=True)

