"""Tests for default and pack-specific user messages."""

from __future__ import annotations

import json
from pathlib import Path

from replicate_ai.constants import DEFAULT_USER_MESSAGE, resolve_user_message


class TestResolveUserMessage:
    def test_cli_override_wins(self, tmp_path: Path):
        (tmp_path / "target_spec_reference.json").write_text(
            json.dumps({"user_message": "from json"}),
            encoding="utf-8",
        )
        assert (
            resolve_user_message(user_message="from cli", example_dir=tmp_path)
            == "from cli"
        )

    def test_user_message_txt(self, tmp_path: Path):
        (tmp_path / "user_message.txt").write_text("from file\n", encoding="utf-8")
        assert (
            resolve_user_message(user_message=None, example_dir=tmp_path)
            == "from file"
        )

    def test_target_spec_reference_user_message(self, tmp_path: Path):
        (tmp_path / "target_spec_reference.json").write_text(
            json.dumps({"user_message": "from reference"}),
            encoding="utf-8",
        )
        assert (
            resolve_user_message(user_message=None, example_dir=tmp_path)
            == "from reference"
        )

    def test_default_when_no_pack_hints(self, tmp_path: Path):
        assert resolve_user_message(user_message=None, example_dir=tmp_path) == (
            DEFAULT_USER_MESSAGE
        )

    def test_default_when_no_example_dir(self):
        msg = resolve_user_message(user_message=None, example_dir=None)
        assert "target_spec_reference.json" in msg
        assert "difference-in-differences unless" in msg
