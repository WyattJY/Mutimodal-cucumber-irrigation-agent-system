"""FastAPI, Loguru and runtime health instrumentation."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import Response
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import PROJECT_ROOT
from app.observability.metrics import (
    COMPONENT_ERROR,
    COMPONENT_UP,
    HTTP_EXCEPTIONS,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS,
    HTTP_REQUESTS_IN_PROGRESS,
    SERVICE_INFO,
    SYSTEM_INFO,
)


_LOGURU_CONFIGURED = False


def configure_loguru() -> None:
    """Attach rotating JSON and human-readable file sinks under the project."""
    global _LOGURU_CONFIGURED
    if _LOGURU_CONFIGURED:
        return

    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        logs_dir / "agriagent.log",
        rotation="20 MB",
        retention="14 days",
        enqueue=True,
        encoding="utf-8",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
    )
    logger.add(
        logs_dir / "agriagent.jsonl",
        rotation="20 MB",
        retention="14 days",
        enqueue=True,
        encoding="utf-8",
        level="DEBUG",
        serialize=True,
    )
    _LOGURU_CONFIGURED = True


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", None) or request.url.path


def observe_component_status(component: str, connected: bool, *, backend: str = "unknown", error: str | None = None) -> None:
    """Update Prometheus gauges for one runtime component."""
    backend_label = backend or "unknown"
    COMPONENT_UP.labels(component=component, backend=backend_label).set(1 if connected else 0)
    COMPONENT_ERROR.labels(component=component, backend=backend_label).set(1 if error else 0)


def observe_stack_status(stack: dict[str, Any]) -> None:
    """Update gauges from the health-check stack contract."""
    for component in ("postgres", "redis", "chroma"):
        status = stack.get(component) or {}
        observe_component_status(
            component,
            bool(status.get("connected")),
            backend=str(status.get("backend") or "unknown"),
            error=status.get("error"),
        )
    if "mcp_connected" in stack:
        observe_component_status("mcp", bool(stack.get("mcp_connected")), backend="fastmcp")


def setup_observability(app: FastAPI, *, service_name: str = "agriagent", expose_metrics: bool = True) -> None:
    """Install Loguru sinks, HTTP metrics middleware and an optional /metrics route."""
    configure_loguru()
    if not getattr(app.state, "agri_observability_info_set", False):
        SERVICE_INFO.info(
            {
                "service": service_name,
                "project_root": str(PROJECT_ROOT),
                "stack": "FastAPI LangGraph PostgreSQL Redis ChromaDB MCP Prometheus Grafana",
            }
        )
        SYSTEM_INFO.info({"service": service_name, "domain": "greenhouse_cucumber_irrigation"})
        app.state.agri_observability_info_set = True

    if not getattr(app.state, "agri_http_metrics_installed", False):

        @app.middleware("http")
        async def prometheus_http_middleware(request: Request, call_next):
            path = request.url.path
            if path == "/metrics":
                return await call_next(request)

            method = request.method
            path_label = path
            in_progress_path = path_label
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, path=path_label).inc()
            started = time.perf_counter()
            try:
                response = await call_next(request)
                path_label = _route_path(request)
                elapsed = time.perf_counter() - started
                HTTP_REQUESTS.labels(
                    method=method,
                    path=path_label,
                    status_code=str(response.status_code),
                ).inc()
                HTTP_REQUEST_DURATION.labels(method=method, path=path_label).observe(elapsed)
                return response
            except Exception as exc:
                path_label = _route_path(request)
                elapsed = time.perf_counter() - started
                HTTP_EXCEPTIONS.labels(
                    method=method,
                    path=path_label,
                    error_type=type(exc).__name__,
                ).inc()
                HTTP_REQUESTS.labels(method=method, path=path_label, status_code="500").inc()
                HTTP_REQUEST_DURATION.labels(method=method, path=path_label).observe(elapsed)
                raise
            finally:
                HTTP_REQUESTS_IN_PROGRESS.labels(method=method, path=in_progress_path).dec()

        app.state.agri_http_metrics_installed = True

    if expose_metrics and not any(getattr(route, "path", None) == "/metrics" for route in app.routes):

        @app.get("/metrics", include_in_schema=False)
        async def prometheus_metrics():
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
