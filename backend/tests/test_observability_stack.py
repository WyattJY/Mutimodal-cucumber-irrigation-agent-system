from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_observability_middleware_records_http_and_component_metrics():
    from app.observability.instrumentation import (
        observe_component_status,
        setup_observability,
    )

    app = FastAPI()
    setup_observability(app, service_name="test-agriagent", expose_metrics=True)

    @app.get("/ok")
    async def ok():
        observe_component_status("postgres", True, backend="postgres")
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/ok").status_code == 200

    metrics_text = client.get("/metrics").text
    assert 'agri_http_requests_total{method="GET",path="/ok",status_code="200"}' in metrics_text
    assert 'agri_component_up{backend="postgres",component="postgres"} 1.0' in metrics_text
    assert 'agri_service_info' in metrics_text


def test_prometheus_and_grafana_are_wired_for_local_gdrive_stack():
    root = Path(__file__).resolve().parents[2]
    prometheus = (root / "ops" / "prometheus.yml").read_text(encoding="utf-8")
    compose_override = (root / "docker-compose.gdrive.yml").read_text(encoding="utf-8")
    dashboard = json.loads((root / "ops" / "grafana" / "dashboards" / "agriagent-overview.json").read_text(encoding="utf-8"))

    assert "host.docker.internal:8000" in prometheus
    assert "./data/docker/prometheus:/prometheus" in compose_override
    assert "./data/docker/grafana:/var/lib/grafana" in compose_override

    dashboard_text = json.dumps(dashboard)
    for expr in [
        "agri_http_request_duration_seconds_bucket",
        "agri_llm_calls_total",
        "agri_mcp_tool_calls_total",
        "agri_knowledge_uploads_total",
        "agri_component_up",
    ]:
        assert expr in dashboard_text
