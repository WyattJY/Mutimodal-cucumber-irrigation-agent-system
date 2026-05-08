"""OpenAI-compatible provider request helpers."""
from __future__ import annotations


def completion_token_kwargs(model: str | None, token_limit: int) -> dict[str, int]:
    """Return the provider-compatible completion token limit parameter."""
    model_name = (model or "").lower()
    if "gpt-chat" in model_name:
        return {"max_completion_tokens": token_limit}
    return {"max_tokens": token_limit}


def temperature_kwargs(model: str | None, temperature: float) -> dict[str, float]:
    """Return temperature only for models/providers that accept custom values."""
    model_name = (model or "").lower()
    if "gpt-chat" in model_name:
        return {}
    return {"temperature": temperature}
