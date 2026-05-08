"""
Tracing decorators for graph nodes and service methods.

@traced_node — records node duration, logs entry/exit, updates Prometheus metrics.
@traced_llm_call — records LLM call duration and token usage.
"""
from __future__ import annotations

import time
import functools
import asyncio
from typing import Optional
from loguru import logger

from app.observability.metrics import (
    NODE_DURATION, LLM_CALLS, LLM_LATENCY, LLM_TOKENS, LLM_ERRORS,
)


def traced_node(node_name: str):
    """
    Decorator for graph node functions.

    Records execution duration and status to Prometheus.
    Works with both sync and async node functions.
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(state: dict) -> dict:
            logger.info(f"[Node:{node_name}] START | date={state.get('date')}")
            start = time.perf_counter()
            status = "ok"
            try:
                result = await fn(state)
                elapsed = time.perf_counter() - start
                # Infer status from result
                trace = result.get("node_trace", [{}])
                if trace and isinstance(trace[0], dict):
                    status = trace[0].get("status", "ok")
                NODE_DURATION.labels(node_name=node_name, status=status).observe(elapsed)
                logger.info(f"[Node:{node_name}] DONE | {elapsed:.2f}s | status={status}")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                status = "error"
                NODE_DURATION.labels(node_name=node_name, status=status).observe(elapsed)
                logger.error(f"[Node:{node_name}] FAIL | {elapsed:.2f}s | {e}")
                raise

        @functools.wraps(fn)
        def sync_wrapper(state: dict) -> dict:
            logger.info(f"[Node:{node_name}] START | date={state.get('date')}")
            start = time.perf_counter()
            status = "ok"
            try:
                result = fn(state)
                elapsed = time.perf_counter() - start
                trace = result.get("node_trace", [{}])
                if trace and isinstance(trace[0], dict):
                    status = trace[0].get("status", "ok")
                NODE_DURATION.labels(node_name=node_name, status=status).observe(elapsed)
                logger.info(f"[Node:{node_name}] DONE | {elapsed:.2f}s | status={status}")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                status = "error"
                NODE_DURATION.labels(node_name=node_name, status=status).observe(elapsed)
                logger.error(f"[Node:{node_name}] FAIL | {elapsed:.2f}s | {e}")
                raise

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator


def traced_llm_call(purpose: str):
    """
    Decorator for LLM service methods.

    Records call count, latency, token usage, and errors.
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            model = kwargs.get("model") or "unknown"
            # Try to get model from the first positional arg (self) if it's an LLMService
            if args and hasattr(args[0], 'model'):
                model = args[0].model

            LLM_CALLS.labels(model=model, purpose=purpose).inc()
            start = time.perf_counter()

            try:
                result = await fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                LLM_LATENCY.labels(model=model, purpose=purpose).observe(elapsed)

                # Try to extract token usage from response
                if hasattr(result, 'usage') and result.usage:
                    LLM_TOKENS.labels(model=model, direction="input").inc(
                        result.usage.prompt_tokens or 0
                    )
                    LLM_TOKENS.labels(model=model, direction="output").inc(
                        result.usage.completion_tokens or 0
                    )

                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                LLM_LATENCY.labels(model=model, purpose=purpose).observe(elapsed)
                LLM_ERRORS.labels(
                    model=model, purpose=purpose,
                    error_type=type(e).__name__
                ).inc()
                raise

        return wrapper
    return decorator
