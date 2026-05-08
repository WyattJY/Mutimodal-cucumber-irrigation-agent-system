"""
Assemble and compile the daily irrigation StateGraph.

Exports a singleton `daily_graph` ready for .ainvoke() / .astream_events().
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import PipelineState
from app.graph.nodes import (
    load_env,
    yolo_segment,
    tsmixer_predict,
    rag_retrieve,
    plant_response,
    anomaly_detect,
    sanity_check,
    finalize,
)
from app.graph.edges import (
    route_after_load_env,
    route_after_anomaly,
    route_after_sanity,
)


def build_daily_graph() -> StateGraph:
    """Build and compile the daily irrigation pipeline graph."""
    g = StateGraph(PipelineState)

    # ── Add nodes ───────────────────────────────────────
    g.add_node("load_env", load_env.run)
    g.add_node("yolo_segment", yolo_segment.run)
    g.add_node("tsmixer_predict", tsmixer_predict.run)
    g.add_node("rag_retrieve", rag_retrieve.run)
    g.add_node("plant_response", plant_response.run)
    g.add_node("anomaly_detect", anomaly_detect.run)
    g.add_node("sanity_check", sanity_check.run)
    g.add_node("finalize", finalize.run)
    g.add_node("finalize_emergency", finalize.run_emergency)

    # ── Entry point ─────────────────────────────────────
    g.set_entry_point("load_env")

    # ── Conditional: cold start may skip YOLO ───────────
    g.add_conditional_edges("load_env", route_after_load_env, {
        "yolo_segment": "yolo_segment",
        "rag_retrieve": "rag_retrieve",
    })

    # ── Sequential flow ─────────────────────────────────
    g.add_edge("yolo_segment", "tsmixer_predict")
    g.add_edge("tsmixer_predict", "rag_retrieve")
    g.add_edge("rag_retrieve", "plant_response")
    g.add_edge("plant_response", "anomaly_detect")

    # ── Conditional: severe anomaly → emergency ─────────
    g.add_conditional_edges("anomaly_detect", route_after_anomaly, {
        "sanity_check": "sanity_check",
        "finalize_emergency": "finalize_emergency",
    })

    # ── Conditional: sanity retry loop ──────────────────
    g.add_conditional_edges("sanity_check", route_after_sanity, {
        "finalize": "finalize",
        "plant_response": "plant_response",
    })

    # ── Terminal edges ──────────────────────────────────
    g.add_edge("finalize", END)
    g.add_edge("finalize_emergency", END)

    return g.compile()


# Singleton compiled graph
daily_graph = build_daily_graph()
