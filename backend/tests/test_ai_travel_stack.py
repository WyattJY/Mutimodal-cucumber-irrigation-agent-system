"""Focused tests for the AI_TRAVEL-stack irrigation refactor."""
from __future__ import annotations

import sys
import types
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


try:
    import loguru  # noqa: F401
except Exception:
    class _Logger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass

    sys.modules["loguru"] = types.SimpleNamespace(logger=_Logger())


def test_multimodal_feature_contract_is_resume_aligned():
    from app.graph.feature_builder import build_feature_vector, build_feature_window, describe_feature_contract

    env = {"temperature": 25, "humidity": 70, "light": 50000}
    yolo = {
        "leaf Instance Count": 8,
        "leaf average mask": 5000,
        "flower Instance Count": 2,
        "flower Mask Pixel Count": 1000,
        "terminal average Mask Pixel Count": 500,
        "fruit Mask average": 300,
        "all leaf mask": 40000,
    }

    assert len(build_feature_vector(env, yolo, 5.0)) == 11
    assert len(build_feature_window(env, yolo, [4.0, 4.5, 5.0])) == 96
    contract = describe_feature_contract()
    assert contract["feature_count"] == 11
    assert contract["window_size"] == 96
    assert "vision_yolo11n_fchl" in contract["modalities"]


def test_router_defaults_to_irrigation_decision_without_llm_key():
    import asyncio
    from app.graph.router import classify_intent

    result = asyncio.run(classify_intent("run irrigation decision", "2024-05-07"))
    assert result["intent"] == "daily_decision"
    assert result["confidence"] >= 0.8


def test_graph_compiles_with_ai_travel_runtime():
    from app.graph.builder_v2 import irrigation_graph
    from app.graph.runtime import graph_runtime

    assert hasattr(irrigation_graph, "ainvoke")
    assert graph_runtime.backend in {"memory", "postgres"}


def test_send_subagent_dispatch_contract():
    from app.graph.builder_v2 import route_to_perception_agents, route_to_prediction_agents

    state = {
        "date": "2024-05-07",
        "env_data": {"temperature": 25, "humidity": 70, "light": 50000, "growth_stage": "fruiting"},
        "image_today_path": None,
        "image_yesterday_path": None,
        "yolo_today": {"leaf Instance Count": 8},
        "options": {"history_irrigation": [4.0, 5.0]},
    }

    perception = route_to_perception_agents(state)
    prediction = route_to_prediction_agents(state)

    assert len(perception) == 2
    assert len(prediction) == 2
    assert {send.node for send in perception} == {"yolo_agent", "rag_perception_agent"}
    assert {send.node for send in prediction} == {"tsmixer_agent", "rag_prediction_agent"}
