"""Tests for LLM provider selection."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from replicate_ai.models import (
    DEFAULT_MODELS,
    get_chat_model,
    normalize_provider,
    provider_summary,
)


class TestNormalizeProvider:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("anthropic", "anthropic"),
            ("claude", "anthropic"),
            ("cloudflare-kimi", "cloudflare-kimi"),
            ("kimi", "cloudflare-kimi"),
            ("cloudflare-glm", "cloudflare-glm"),
            ("glm", "cloudflare-glm"),
            ("gemini", "gemini"),
            ("groq", "groq"),
        ],
    )
    def test_aliases(self, raw: str, expected: str):
        assert normalize_provider(raw) == expected

    def test_defaults_to_anthropic(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        assert normalize_provider(None) == "anthropic"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            normalize_provider("openai")


class TestGetChatModel:
    @patch("langchain_anthropic.ChatAnthropic")
    def test_anthropic(self, mock_anthropic, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_anthropic.return_value = MagicMock()
        model = get_chat_model("anthropic")
        mock_anthropic.assert_called_once_with(
            model=DEFAULT_MODELS["anthropic"],
            temperature=0,
            max_tokens=8192,
        )
        assert model is mock_anthropic.return_value

    @patch("langchain_cloudflare.chat_models.ChatCloudflareWorkersAI")
    def test_cloudflare_kimi(self, mock_cf, monkeypatch):
        monkeypatch.setenv("CF_ACCOUNT_ID", "acct")
        monkeypatch.setenv("CF_AI_API_TOKEN", "token")
        mock_cf.return_value = MagicMock()
        get_chat_model("cloudflare-kimi")
        mock_cf.assert_called_once_with(
            model=DEFAULT_MODELS["cloudflare-kimi"],
            temperature=0,
            max_tokens=8192,
        )

    @patch("langchain_cloudflare.chat_models.ChatCloudflareWorkersAI")
    def test_cloudflare_glm(self, mock_cf, monkeypatch):
        monkeypatch.setenv("CF_ACCOUNT_ID", "acct")
        monkeypatch.setenv("CF_AI_API_TOKEN", "token")
        mock_cf.return_value = MagicMock()
        get_chat_model("glm")
        mock_cf.assert_called_once_with(
            model=DEFAULT_MODELS["cloudflare-glm"],
            temperature=0,
            max_tokens=8192,
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_gemini(self, mock_gemini, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        mock_gemini.return_value = MagicMock()
        get_chat_model("gemini")
        mock_gemini.assert_called_once_with(
            model=DEFAULT_MODELS["gemini"],
            temperature=0,
            max_output_tokens=8192,
            api_key="test-key",
            thinking_level="medium",
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_gemini_vertex(self, mock_gemini, monkeypatch):
        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proj")
        mock_gemini.return_value = MagicMock()
        get_chat_model("gemini")
        mock_gemini.assert_called_once_with(
            model=DEFAULT_MODELS["gemini"],
            temperature=0,
            max_output_tokens=8192,
            vertexai=True,
            project="proj",
            location=None,
            thinking_level="medium",
        )

    def test_gemini_missing_credentials(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
        with pytest.raises(ValueError, match="Gemini requires"):
            get_chat_model("gemini")

    @patch("langchain_groq.ChatGroq")
    def test_groq(self, mock_groq, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        mock_groq.return_value = MagicMock()
        get_chat_model("groq")
        mock_groq.assert_called_once_with(
            model=DEFAULT_MODELS["groq"],
            temperature=0,
            max_tokens=8192,
        )

    def test_groq_missing_credentials(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            get_chat_model("groq")

    def test_cloudflare_missing_credentials(self, monkeypatch):
        monkeypatch.delenv("CF_ACCOUNT_ID", raising=False)
        monkeypatch.delenv("CF_AI_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="CF_ACCOUNT_ID"):
            get_chat_model("cloudflare-glm")


class TestProviderSummary:
    def test_summary_anthropic(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        assert provider_summary() == "anthropic/claude-sonnet-4-6"

    def test_summary_kimi(self):
        assert provider_summary("kimi").startswith("cloudflare/@cf/moonshotai/")

    def test_summary_gemini(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-custom")
        assert provider_summary() == "gemini/gemini-custom"

    def test_summary_groq(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_MODEL", "groq-custom")
        assert provider_summary() == "groq/groq-custom"
