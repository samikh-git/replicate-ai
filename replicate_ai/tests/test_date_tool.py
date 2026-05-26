"""Tests for auditor date tool."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from unittest.mock import patch

from replicate_ai.tools.date_tool import get_current_date


class TestGetCurrentDate:
    def test_returns_iso_8601_date(self):
        fixed = datetime(2026, 5, 25, 15, 30, tzinfo=UTC)
        with patch("replicate_ai.tools.date_tool.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            result = get_current_date.invoke({})
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result)
        assert result == "2026-05-25"

    def test_tool_name_and_description(self):
        assert get_current_date.name == "get_current_date"
        assert "ISO 8601" in (get_current_date.description or "")
