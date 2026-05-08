"""Unified OpenAI-compatible JSON caller for prompt-driven subagents."""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import time
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import PROJECT_ROOT, get_active_openai_config
from app.core.openai_compat import temperature_kwargs
from app.observability.metrics import LLM_CALLS, LLM_ERRORS, LLM_LATENCY, LLM_TOKENS


PROMPT_DIR = PROJECT_ROOT / "prompts" / "subagents"


def load_agent_prompt(filename: str) -> str:
    """Load a subagent system prompt from prompts/subagents."""
    path = PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


def _image_to_data_url(image_path: str | Path) -> str | None:
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class LLMAgentService:
    """Prompt-driven JSON analysis with deterministic fallback."""

    async def analyze_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        schema_name: str,
        fallback: dict[str, Any],
        *,
        image_paths: list[str | Path] | None = None,
        use_vision: bool = False,
    ) -> dict[str, Any]:
        config = get_active_openai_config()
        model = config.get("vision_model") if use_vision else config.get("model")
        model = model or config.get("model") or "unknown"
        if not config.get("api_key"):
            return {**fallback, "llm_status": "skipped_no_api_key", "schema_name": schema_name}

        LLM_CALLS.labels(model=model, purpose=schema_name).inc()
        started = time.perf_counter()
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=config["api_key"], base_url=config.get("base_url"))

            payload_text = json.dumps(
                {"schema_name": schema_name, "payload": user_payload},
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            user_content: str | list[dict[str, Any]]
            if use_vision and image_paths:
                blocks: list[dict[str, Any]] = [{"type": "text", "text": payload_text}]
                for image_path in image_paths:
                    data_url = _image_to_data_url(image_path)
                    if data_url:
                        blocks.append({"type": "image_url", "image_url": {"url": data_url}})
                user_content = blocks
            else:
                user_content = payload_text

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                **temperature_kwargs(model, 0.1),
            )
            content = response.choices[0].message.content or "{}"
            parsed = _extract_json_object(content)
            usage = getattr(response, "usage", None)
            if usage:
                LLM_TOKENS.labels(model=model, direction="input").inc(int(getattr(usage, "prompt_tokens", 0) or 0))
                LLM_TOKENS.labels(model=model, direction="output").inc(int(getattr(usage, "completion_tokens", 0) or 0))
            LLM_LATENCY.labels(model=model, purpose=schema_name).observe(time.perf_counter() - started)
            parsed.setdefault("llm_status", "ok")
            parsed.setdefault("schema_name", schema_name)
            return parsed
        except Exception as exc:
            LLM_LATENCY.labels(model=model, purpose=schema_name).observe(time.perf_counter() - started)
            LLM_ERRORS.labels(model=model, purpose=schema_name, error_type=type(exc).__name__).inc()
            logger.warning(f"[llm_agent_service] {schema_name} fallback: {exc}")
            return {
                **fallback,
                "llm_status": "fallback_error",
                "llm_error": str(exc),
                "schema_name": schema_name,
            }


llm_agent_service = LLMAgentService()
