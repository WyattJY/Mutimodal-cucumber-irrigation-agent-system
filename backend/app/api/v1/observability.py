"""
Observability API — expose key metrics as JSON for the frontend dashboard.

Also provides Prometheus /metrics endpoint integration.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.observability.metrics import (
    ACTIVE_GRAPH_RUNS,
    COMPONENT_UP,
    HTTP_REQUESTS,
    KNOWLEDGE_CHUNKS_INDEXED,
    KNOWLEDGE_UPLOADS,
    LLM_CALLS,
    LLM_ERRORS,
    LLM_LATENCY,
    LLM_TOKENS,
    MCP_TOOL_CALLS,
    MCP_TOOLS_AVAILABLE,
    MEMORY_EPISODES,
    NODE_DURATION,
    PIPELINE_RUNS,
    RAG_CACHE_HITS,
    RAG_QUERIES,
)

router = APIRouter(prefix="/observability", tags=["Observability"])


def _counter_value(counter, *label_values) -> float:
    """Safely extract a counter's current value."""
    try:
        if label_values:
            return counter.labels(*label_values)._value.get()
        return counter._value.get()
    except Exception:
        return 0.0


def _histogram_stats(histogram, *label_values) -> dict:
    """Extract count and sum from a histogram."""
    try:
        if label_values:
            h = histogram.labels(*label_values)
        else:
            h = histogram
        count = h._sum._value.get() if hasattr(h, '_sum') else 0
        return {"count": h._count._value.get() if hasattr(h, '_count') else 0, "sum": count}
    except Exception:
        return {"count": 0, "sum": 0}


def _collect_total(metric) -> float:
    total = 0.0
    try:
        for sample in metric.collect()[0].samples:
            if sample.name.endswith("_total"):
                total += sample.value
    except Exception:
        pass
    return total


@router.get("/summary")
async def get_metrics_summary():
    """
    Return key metrics as JSON for frontend dashboard cards.

    Provides aggregated metrics without requiring Prometheus/Grafana setup.
    """
    # Pipeline stats
    pipeline_v2_success = _counter_value(PIPELINE_RUNS, "v2", "success")
    pipeline_v2_error = _counter_value(PIPELINE_RUNS, "v2", "error")
    pipeline_v2_fallback = _counter_value(PIPELINE_RUNS, "v2", "fallback")
    pipeline_v1_success = _counter_value(PIPELINE_RUNS, "v1", "success")
    pipeline_total = pipeline_v2_success + pipeline_v2_error + pipeline_v2_fallback + pipeline_v1_success

    # LLM stats — aggregate across models/purposes
    llm_total_calls = 0
    llm_total_tokens_in = 0
    llm_total_tokens_out = 0
    try:
        for sample in LLM_CALLS.collect()[0].samples:
            if sample.name.endswith("_total"):
                llm_total_calls += sample.value
        for sample in LLM_TOKENS.collect()[0].samples:
            if sample.name.endswith("_total"):
                if sample.labels.get("direction") == "input":
                    llm_total_tokens_in += sample.value
                else:
                    llm_total_tokens_out += sample.value
    except Exception:
        pass

    # LLM average latency
    llm_avg_latency = 0
    try:
        for sample in LLM_LATENCY.collect()[0].samples:
            if sample.name.endswith("_sum"):
                llm_sum = sample.value
            if sample.name.endswith("_count"):
                llm_count = sample.value
                if llm_count > 0:
                    llm_avg_latency = llm_sum / llm_count
    except Exception:
        pass

    # RAG stats
    rag_total = 0
    rag_cache = _counter_value(RAG_CACHE_HITS)
    try:
        for sample in RAG_QUERIES.collect()[0].samples:
            if sample.name.endswith("_total"):
                rag_total += sample.value
    except Exception:
        pass

    # Node latency breakdown
    node_latencies = {}
    try:
        for sample in NODE_DURATION.collect()[0].samples:
            if sample.name.endswith("_sum"):
                node = sample.labels.get("node_name", "unknown")
                node_latencies.setdefault(node, {"sum": 0, "count": 0})
                node_latencies[node]["sum"] += sample.value
            if sample.name.endswith("_count"):
                node = sample.labels.get("node_name", "unknown")
                node_latencies.setdefault(node, {"sum": 0, "count": 0})
                node_latencies[node]["count"] += sample.value
    except Exception:
        pass

    node_avg = {
        k: round(v["sum"] / v["count"], 3) if v["count"] > 0 else 0
        for k, v in node_latencies.items()
    }
    component_up = {}
    try:
        for sample in COMPONENT_UP.collect()[0].samples:
            component = sample.labels.get("component", "unknown")
            backend = sample.labels.get("backend", "unknown")
            component_up[component] = {"backend": backend, "up": bool(sample.value)}
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "http": {
                "total_requests": int(_collect_total(HTTP_REQUESTS)),
            },
            "pipeline": {
                "total_runs": int(pipeline_total),
                "v2_success": int(pipeline_v2_success),
                "v2_error": int(pipeline_v2_error),
                "v2_fallback": int(pipeline_v2_fallback),
                "v1_success": int(pipeline_v1_success),
                "success_rate": round(
                    (pipeline_v2_success + pipeline_v1_success) / pipeline_total * 100, 1
                ) if pipeline_total > 0 else 0,
                "active_runs": ACTIVE_GRAPH_RUNS._value.get(),
            },
            "llm": {
                "total_calls": int(llm_total_calls),
                "total_tokens_input": int(llm_total_tokens_in),
                "total_tokens_output": int(llm_total_tokens_out),
                "total_tokens": int(llm_total_tokens_in + llm_total_tokens_out),
                "avg_latency_ms": round(llm_avg_latency * 1000, 1),
            },
            "rag": {
                "total_queries": int(rag_total),
                "cache_hits": int(rag_cache),
                "cache_hit_rate": round(
                    rag_cache / rag_total * 100, 1
                ) if rag_total > 0 else 0,
            },
            "mcp": {
                "tool_calls": int(_collect_total(MCP_TOOL_CALLS)),
                "tools_available": int(MCP_TOOLS_AVAILABLE._value.get()),
            },
            "knowledge": {
                "uploads": int(_collect_total(KNOWLEDGE_UPLOADS)),
                "chunks_indexed": int(_collect_total(KNOWLEDGE_CHUNKS_INDEXED)),
            },
            "components": component_up,
            "nodes": {
                "avg_latency_ms": {k: round(v * 1000, 1) for k, v in node_avg.items()},
            },
            "memory": {
                "episodes_count": int(MEMORY_EPISODES._value.get()),
            },
        },
    }


@router.get("/nodes")
async def get_node_metrics():
    """Detailed per-node metrics for the pipeline flow visualization."""
    nodes_data = {}
    try:
        for sample in NODE_DURATION.collect()[0].samples:
            node = sample.labels.get("node_name", "unknown")
            status = sample.labels.get("status", "unknown")
            key = f"{node}:{status}"

            if node not in nodes_data:
                nodes_data[node] = {"statuses": {}}

            if sample.name.endswith("_count"):
                nodes_data[node]["statuses"].setdefault(status, {})["count"] = sample.value
            if sample.name.endswith("_sum"):
                nodes_data[node]["statuses"].setdefault(status, {})["total_seconds"] = sample.value
    except Exception:
        pass

    return {"success": True, "data": nodes_data}


@router.get("/llm")
async def get_llm_metrics():
    """Detailed LLM metrics by model and purpose."""
    calls = {}
    try:
        for sample in LLM_CALLS.collect()[0].samples:
            if sample.name.endswith("_total"):
                key = f"{sample.labels.get('model')}:{sample.labels.get('purpose')}"
                calls[key] = {"count": sample.value}
    except Exception:
        pass

    latencies = {}
    try:
        for sample in LLM_LATENCY.collect()[0].samples:
            key = f"{sample.labels.get('model')}:{sample.labels.get('purpose')}"
            latencies.setdefault(key, {})
            if sample.name.endswith("_sum"):
                latencies[key]["total_seconds"] = sample.value
            if sample.name.endswith("_count"):
                latencies[key]["count"] = sample.value
    except Exception:
        pass

    errors = {}
    try:
        for sample in LLM_ERRORS.collect()[0].samples:
            if sample.name.endswith("_total"):
                key = f"{sample.labels.get('model')}:{sample.labels.get('purpose')}"
                errors.setdefault(key, []).append({
                    "error_type": sample.labels.get("error_type"),
                    "count": sample.value,
                })
    except Exception:
        pass

    return {
        "success": True,
        "data": {"calls": calls, "latencies": latencies, "errors": errors},
    }
