"""Date tool for the statistical auditor subagent."""

from __future__ import annotations

from datetime import UTC, datetime

from langchain_core.tools import tool


@tool
def get_current_date() -> str:
    """Return today's date in ISO 8601 format (YYYY-MM-DD, UTC).

    Use this for the **Date** field in replication_audit.md. Do not guess the date.
    """
    return datetime.now(UTC).date().isoformat()
