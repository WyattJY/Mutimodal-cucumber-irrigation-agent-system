"""LangGraph runtime factory for checkpointer/store selection."""
from __future__ import annotations

import inspect
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any

from loguru import logger

from app.core.config import settings


@dataclass
class GraphRuntime:
    checkpointer: Any
    store: Any
    backend: str
    error: str | None = None
    context_stack: Any | None = None


def _memory_runtime(error: str | None = None) -> GraphRuntime:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.store.memory import InMemoryStore

    return GraphRuntime(
        checkpointer=MemorySaver(),
        store=InMemoryStore(),
        backend="memory",
        error=error,
    )


async def _maybe_setup(component: Any) -> None:
    setup = getattr(component, "setup", None)
    if not callable(setup):
        return
    result = setup()
    if inspect.isawaitable(result):
        await result


async def create_async_graph_runtime() -> GraphRuntime:
    """Create async-compatible LangGraph persistence objects.

    PostgreSQL is preferred when the optional package is installed and the
    backend is explicitly configured. The local memory fallback is intentional:
    it keeps demos and tests runnable without hiding the production contract.
    """
    if settings.graph_backend in {"postgres", "auto"}:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # type: ignore
            from langgraph.store.postgres.aio import AsyncPostgresStore  # type: ignore

            stack = AsyncExitStack()
            checkpointer = await stack.enter_async_context(
                AsyncPostgresSaver.from_conn_string(settings.postgres_dsn)
            )
            store = await stack.enter_async_context(
                AsyncPostgresStore.from_conn_string(settings.postgres_dsn)
            )

            await _maybe_setup(checkpointer)
            await _maybe_setup(store)

            logger.info("[graph_runtime] using async PostgreSQL checkpointer/store")
            return GraphRuntime(
                checkpointer=checkpointer,
                store=store,
                backend="postgres",
                context_stack=stack,
            )
        except Exception as exc:
            if settings.graph_backend == "postgres":
                raise
            logger.warning(f"[graph_runtime] PostgreSQL graph runtime unavailable: {exc}")

    return _memory_runtime(
        None if settings.graph_backend == "memory" else "postgres_optional_dependency_or_connection_unavailable"
    )


async def close_graph_runtime(runtime: GraphRuntime) -> None:
    stack = runtime.context_stack
    if stack is None:
        return
    close = getattr(stack, "aclose", None)
    if callable(close):
        await close()
        return
    close = getattr(stack, "close", None)
    if callable(close):
        close()


graph_runtime = _memory_runtime("async_runtime_not_initialized")


def set_graph_runtime(runtime: GraphRuntime) -> None:
    global graph_runtime
    graph_runtime = runtime
