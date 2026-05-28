"""LLM provider selection for ReplicateAI (Anthropic vs Cloudflare vs Google)."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.language_models import BaseChatModel

ProviderName = Literal["anthropic", "cloudflare-kimi", "cloudflare-glm", "gemini", "groq"]

PROVIDER_ALIASES: dict[str, ProviderName] = {
    "anthropic": "anthropic",
    "claude": "anthropic",
    "cloudflare-kimi": "cloudflare-kimi",
    "kimi": "cloudflare-kimi",
    "cloudflare-glm": "cloudflare-glm",
    "glm": "cloudflare-glm",
    "gemini": "gemini",
    "groq": "groq",
}

DEFAULT_MODELS: dict[ProviderName, str] = {
    "anthropic": "claude-sonnet-4-6",
    "cloudflare-kimi": "@cf/moonshotai/kimi-k2.6",
    "cloudflare-glm": "@cf/zai-org/glm-4.7-flash",
    "gemini": "gemini-3.5-flash",
    "groq": "llama-3.3-70b-versatile",
}

# One entry per backend; CLI aliases (kimi, glm, claude) map via PROVIDER_ALIASES.
CANONICAL_PROVIDERS: tuple[ProviderName, ...] = (
    "anthropic",
    "cloudflare-kimi",
    "cloudflare-glm",
    "gemini",
    "groq",
)

ENV_PROVIDER = "LLM_PROVIDER"
ENV_ANTHROPIC_MODEL = "ANTHROPIC_MODEL"
ENV_CF_KIMI_MODEL = "CLOUDFLARE_KIMI_MODEL"
ENV_CF_GLM_MODEL = "CLOUDFLARE_GLM_MODEL"
ENV_CF_ACCOUNT = "CF_ACCOUNT_ID"
ENV_CF_TOKEN = "CF_AI_API_TOKEN"
ENV_GEMINI_MODEL = "GEMINI_MODEL"
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"
ENV_GEMINI_API_KEY = "GEMINI_API_KEY"
ENV_GOOGLE_USE_VERTEXAI = "GOOGLE_GENAI_USE_VERTEXAI"
ENV_GOOGLE_CLOUD_PROJECT = "GOOGLE_CLOUD_PROJECT"
ENV_GOOGLE_CLOUD_LOCATION = "GOOGLE_CLOUD_LOCATION"
ENV_GEMINI_THINKING_LEVEL = "GEMINI_THINKING_LEVEL"
ENV_GROQ_API_KEY = "GROQ_API_KEY"
ENV_GROQ_MODEL = "GROQ_MODEL"


def normalize_provider(name: str | None) -> ProviderName:
    """Map CLI/env provider string to a canonical provider name."""
    raw = (name or os.getenv(ENV_PROVIDER) or "anthropic").strip().lower()
    try:
        return PROVIDER_ALIASES[raw]
    except KeyError as e:
        allowed = ", ".join(sorted(set(PROVIDER_ALIASES.keys())))
        raise ValueError(
            f"Unknown LLM provider {raw!r}. Choose one of: {allowed}"
        ) from e


def get_chat_model(
    provider: str | None = None,
    *,
    temperature: float = 0,
    max_tokens: int = 8192,
) -> BaseChatModel:
    """Build the chat model for create_deep_agent from provider + env."""
    resolved = normalize_provider(provider)

    if resolved == "anthropic":
        from langchain_anthropic import ChatAnthropic

        model_id = os.getenv(ENV_ANTHROPIC_MODEL, DEFAULT_MODELS["anthropic"])
        return ChatAnthropic(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if resolved == "gemini":
        return _get_gemini_chat_model(
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if resolved == "groq":
        return _get_groq_chat_model(
            temperature=temperature,
            max_tokens=max_tokens,
        )

    from langchain_cloudflare.chat_models import ChatCloudflareWorkersAI

    _require_cloudflare_credentials()

    if resolved == "cloudflare-kimi":
        model_id = os.getenv(ENV_CF_KIMI_MODEL, DEFAULT_MODELS["cloudflare-kimi"])
    else:
        model_id = os.getenv(ENV_CF_GLM_MODEL, DEFAULT_MODELS["cloudflare-glm"])

    return ChatCloudflareWorkersAI(
        model=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _require_cloudflare_credentials() -> None:
    missing = [
        name
        for name, value in (
            (ENV_CF_ACCOUNT, os.getenv(ENV_CF_ACCOUNT)),
            (ENV_CF_TOKEN, os.getenv(ENV_CF_TOKEN)),
        )
        if not value
    ]
    if missing:
        raise ValueError(
            f"Cloudflare Workers AI requires: {', '.join(missing)}. "
            "Set them in replicate_ai/.env (see .env.example)."
        )


def _env_truthy(name: str) -> bool:
    value = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _require_gemini_credentials(*, vertex_forced: bool) -> None:
    """
    Credential validation for Gemini.

    When Vertex AI is forced, we require at least `GOOGLE_CLOUD_PROJECT`.
    When Vertex AI is not forced, we require an API key.
    """

    if vertex_forced:
        if not os.getenv(ENV_GOOGLE_CLOUD_PROJECT):
            raise ValueError(
                "Gemini Vertex AI mode requires: "
                f"{ENV_GOOGLE_CLOUD_PROJECT}. "
                f"Set it in replicate_ai/.env (see .env.example)."
            )
        return

    api_key = os.getenv(ENV_GOOGLE_API_KEY) or os.getenv(ENV_GEMINI_API_KEY)
    if not api_key:
        raise ValueError(
            "Gemini requires an API key. Set either "
            f"{ENV_GOOGLE_API_KEY} or {ENV_GEMINI_API_KEY} in replicate_ai/.env "
            "(see .env.example)."
        )


def _get_gemini_chat_model(*, temperature: float, max_tokens: int) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    vertex_forced = _env_truthy(ENV_GOOGLE_USE_VERTEXAI)
    _require_gemini_credentials(vertex_forced=vertex_forced)

    model_id = os.getenv(ENV_GEMINI_MODEL, DEFAULT_MODELS["gemini"])

    api_key = os.getenv(ENV_GOOGLE_API_KEY) or os.getenv(ENV_GEMINI_API_KEY)
    thinking_level = os.getenv(ENV_GEMINI_THINKING_LEVEL, "medium").strip().lower()

    if vertex_forced:
        # Vertex mode supports both API-key and ADC credentials; we only
        # require `GOOGLE_CLOUD_PROJECT` here and let the SDK resolve the rest.
        return ChatGoogleGenerativeAI(
            model=model_id,
            temperature=temperature,
            max_output_tokens=max_tokens,
            vertexai=True,
            project=os.getenv(ENV_GOOGLE_CLOUD_PROJECT),
            location=os.getenv(ENV_GOOGLE_CLOUD_LOCATION) or None,
            thinking_level=thinking_level,
        )

    return ChatGoogleGenerativeAI(
        model=model_id,
        temperature=temperature,
        max_output_tokens=max_tokens,
        api_key=api_key,
        thinking_level=thinking_level,
    )


def _require_groq_credentials() -> None:
    if not os.getenv(ENV_GROQ_API_KEY):
        raise ValueError(
            f"Groq requires: {ENV_GROQ_API_KEY}. "
            "Set it in replicate_ai/.env (see .env.example)."
        )


def _get_groq_chat_model(*, temperature: float, max_tokens: int) -> BaseChatModel:
    from langchain_groq import ChatGroq

    _require_groq_credentials()
    model_id = os.getenv(ENV_GROQ_MODEL, DEFAULT_MODELS["groq"])
    return ChatGroq(
        model=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def list_provider_options() -> list[dict[str, str]]:
    """Provider dropdown options for the GUI (canonical ids, no alias duplicates)."""
    return [
        {"id": p, "label": provider_summary(p)}
        for p in CANONICAL_PROVIDERS
    ]


def provider_summary(provider: str | None = None) -> str:
    """Human-readable line for logging which model will run."""
    resolved = normalize_provider(provider)
    if resolved == "anthropic":
        model_id = os.getenv(ENV_ANTHROPIC_MODEL, DEFAULT_MODELS["anthropic"])
        return f"anthropic/{model_id}"
    if resolved == "cloudflare-kimi":
        model_id = os.getenv(ENV_CF_KIMI_MODEL, DEFAULT_MODELS["cloudflare-kimi"])
        return f"cloudflare/{model_id}"
    if resolved == "gemini":
        model_id = os.getenv(ENV_GEMINI_MODEL, DEFAULT_MODELS["gemini"])
        return f"gemini/{model_id}"
    if resolved == "groq":
        model_id = os.getenv(ENV_GROQ_MODEL, DEFAULT_MODELS["groq"])
        return f"groq/{model_id}"
    model_id = os.getenv(ENV_CF_GLM_MODEL, DEFAULT_MODELS["cloudflare-glm"])
    return f"cloudflare/{model_id}"
