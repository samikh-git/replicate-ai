"""Tests for canonical provider listing (GUI dropdown)."""

from __future__ import annotations

from replicate_ai.models import CANONICAL_PROVIDERS, list_provider_options, normalize_provider


class TestProviderOptions:
    def test_no_duplicate_canonical_ids(self):
        options = list_provider_options()
        ids = [o["id"] for o in options]
        assert len(ids) == len(set(ids))
        assert len(options) == len(CANONICAL_PROVIDERS)

    def test_aliases_not_listed_separately(self):
        ids = {o["id"] for o in list_provider_options()}
        assert "kimi" not in ids
        assert "glm" not in ids
        assert "cloudflare-kimi" in ids
        assert "cloudflare-glm" in ids

    def test_aliases_still_normalize(self):
        assert normalize_provider("kimi") == "cloudflare-kimi"
        assert normalize_provider("glm") == "cloudflare-glm"
