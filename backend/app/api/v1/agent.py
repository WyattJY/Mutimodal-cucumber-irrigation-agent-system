"""LangGraph Agent API for AI_TRAVEL-stack irrigation decisions."""
from __future__ import annotations

import json
import time
import uuid
from datetime import date as date_type
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.graph.builder_v2 import get_irrigation_graph
from app.graph.feature_builder import describe_feature_contract
from app.graph import runtime as graph_runtime_module
from app.infra.chroma_store import chroma_manager
from app.infra.redis_cache import redis_cache
from app.observability.metrics import ACTIVE_GRAPH_RUNS, PIPELINE_DURATION, PIPELINE_RUNS, SSE_EVENTS


router = APIRouter(prefix="/agent", tags=["agent"])


class AgentDecisionRequest(BaseModel):
    date: str = Field(default_factory=lambda: date_type.today().isoformat())
    user_input: str = "执行今日温室黄瓜灌水决策"
    env_data: dict = Field(default_factory=lambda: {"temperature": 25.0, "humidity": 70.0, "light": 50000.0, "growth_stage": "fruiting"})
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    history_irrigation: list[float] = Field(default_factory=list)
    user_id: str = "demo_user"
    greenhouse_id: str = "greenhouse_01"
    thread_id: Optional[str] = None
    options: dict = Field(default_factory=dict)


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except TypeError:
        if isinstance(value, list):
            return [_jsonable(v) for v in value]
        if isinstance(value, dict):
            return {k: _jsonable(v) for k, v in value.items()}
        return str(value)


def _compact_result(result: dict) -> dict:
    feature_window = result.get("feature_window") or []
    subagents = {
        "yolo": result.get("yolo_agent_report"),
        "tsmixer": result.get("tsmixer_agent_report"),
        "rag": result.get("rag_agent_reports", []),
    }
    return {
        "thread_id": result.get("thread_id"),
        "date": result.get("date"),
        "intent": result.get("intent"),
        "irrigation_amount": result.get("irrigation_amount"),
        "prediction_source": result.get("prediction_source"),
        "irrigation_plan": result.get("irrigation_plan"),
        "warnings": result.get("warnings", []),
        "suggestions": result.get("suggestions", []),
        "runtime_profile": result.get("runtime_profile"),
        "feature_vector": result.get("feature_vector"),
        "feature_window_shape": [len(feature_window), len(feature_window[0]) if feature_window else 0],
        "feature_contract": result.get("feature_contract"),
        "yolo_today": result.get("yolo_today"),
        "tsmixer_prediction": result.get("tsmixer_prediction"),
        "main_agent_decision": result.get("main_agent_decision"),
        "subagents": subagents,
        "subagent_summary": result.get("subagent_summary"),
        "final_irrigation": (result.get("main_agent_decision") or {}).get("final_irrigation_l_per_m2"),
        "confidence": (result.get("main_agent_decision") or {}).get("confidence"),
        "retrieved_docs": result.get("retrieved_docs", []),
        "subagent_runs": result.get("subagent_runs", []),
        "node_trace": result.get("node_trace", []),
    }


def _initial_state(request: AgentDecisionRequest) -> tuple[dict, dict]:
    thread_id = request.thread_id or f"{request.greenhouse_id}:{request.date}:{uuid.uuid4().hex[:8]}"
    options = {
        "user_input": request.user_input,
        "history_irrigation": request.history_irrigation,
        "skip_llm_review": True,
        "save_episode": request.options.get("save_episode", False),
        "save_response": request.options.get("save_response", False),
        **request.options,
    }
    state = {
        "thread_id": thread_id,
        "user_id": request.user_id,
        "greenhouse_id": request.greenhouse_id,
        "date": request.date,
        "image_path": request.image_path,
        "image_base64": request.image_base64,
        "env_data": request.env_data,
        "options": options,
        "iteration_count": 0,
        "runtime_profile": {
            "graph_backend": graph_runtime_module.graph_runtime.backend,
            "redis_backend": redis_cache.backend,
            "chroma_backend": chroma_manager.backend,
        },
    }
    config = {"configurable": {"thread_id": thread_id, "user_id": request.user_id, "greenhouse_id": request.greenhouse_id}}
    return state, config


@router.get("/stack")
async def stack_status():
    return {
        "success": True,
        "data": {
            "domain": "greenhouse_cucumber_irrigation",
            "graph_backend": graph_runtime_module.graph_runtime.backend,
            "redis": redis_cache.status(),
            "chroma": chroma_manager.status(),
            "feature_contract": describe_feature_contract(),
            "subagent_design": "LangGraph Send fan-out/fan-in: YOLO||RAG then TSMixer||RAG",
        },
    }


@router.post("/decision")
async def run_decision(request: AgentDecisionRequest):
    state, config = _initial_state(request)
    started = time.perf_counter()
    ACTIVE_GRAPH_RUNS.inc()
    try:
        result = await get_irrigation_graph().ainvoke(state, config=config)
        PIPELINE_RUNS.labels(version="v2", status="success").inc()
        return {"success": True, "data": _jsonable(_compact_result(result))}
    except Exception:
        PIPELINE_RUNS.labels(version="v2", status="error").inc()
        raise
    finally:
        PIPELINE_DURATION.labels(version="v2").observe(time.perf_counter() - started)
        ACTIVE_GRAPH_RUNS.dec()


@router.post("/decision/stream")
async def stream_decision(request: AgentDecisionRequest):
    state, config = _initial_state(request)

    async def generate():
        started = time.perf_counter()
        ACTIVE_GRAPH_RUNS.inc()
        SSE_EVENTS.labels(event_type="run_start", status="success").inc()
        yield {"event": "run_start", "data": json.dumps({"thread_id": state["thread_id"]}, ensure_ascii=False)}
        try:
            graph = get_irrigation_graph()
            async for event in graph.astream_events(state, config=config, version="v2"):
                event_name = event.get("event", "")
                name = event.get("name", "")
                if event_name in {"on_chain_start", "on_chain_end", "on_chain_error"}:
                    SSE_EVENTS.labels(event_type=event_name, status="success").inc()
                    yield {
                        "event": "graph_event",
                        "data": json.dumps(
                            {"event": event_name, "name": name, "data": _jsonable(event.get("data", {}))},
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
            final = await graph.ainvoke(state, config=config)
            PIPELINE_RUNS.labels(version="v2_stream", status="success").inc()
            SSE_EVENTS.labels(event_type="final", status="success").inc()
            yield {"event": "final", "data": json.dumps(_jsonable(_compact_result(final)), ensure_ascii=False, default=str)}
        except Exception as exc:
            PIPELINE_RUNS.labels(version="v2_stream", status="error").inc()
            SSE_EVENTS.labels(event_type="error", status="error").inc()
            yield {"event": "error", "data": json.dumps({"message": str(exc)}, ensure_ascii=False)}
        finally:
            PIPELINE_DURATION.labels(version="v2_stream").observe(time.perf_counter() - started)
            ACTIVE_GRAPH_RUNS.dec()

    return EventSourceResponse(generate())
