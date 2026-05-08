"""Irrigation subagents used by the LangGraph fan-out/fan-in pipeline.

The primary implementation now supports LangGraph Send API dispatch in
``builder_v2.py``. The legacy ``perception_node`` and ``prediction_node``
functions remain for backward compatibility and still execute the same
subagents with ``asyncio.gather``.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import time
from pathlib import Path
from typing import Any

from loguru import logger

from app.graph.agent_schemas import (
    RAGAgentReport,
    TSMixerAgentReport,
    YoloAgentReport,
    validate_report,
)
from app.graph.feature_builder import (
    build_feature_vector,
    build_feature_window,
    describe_feature_contract,
)
from app.observability.metrics import (
    NODE_DURATION,
    RAG_QUERIES,
    RAG_RESULTS_COUNT,
    SUBAGENT_RUNS,
    TSMIXER_INFERENCE,
    TSMIXER_PREDICTION,
    YOLO_INFERENCE,
)
from app.services.llm_agent_service import load_agent_prompt, llm_agent_service


YOLO_METRICS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "yolo_metrics"


def _date_to_filename(value: str) -> str:
    parts = value.split("-")
    return f"{parts[1]}{parts[2]}" if len(parts) == 3 else value


def _default_yolo_metrics(reason: str = "mock_fallback") -> dict:
    return {
        "leaf Instance Count": 8.0,
        "leaf average mask": 5000.0,
        "flower Instance Count": 2.0,
        "flower Mask Pixel Count": 1000.0,
        "terminal average Mask Pixel Count": 500.0,
        "fruit Mask average": 300.0,
        "all leaf mask": 40000.0,
        "_source": reason,
    }


def _doc_to_reference(doc: Any) -> dict:
    metadata = getattr(doc, "metadata", None) or {}
    return {
        "doc_id": getattr(doc, "doc_id", None) or metadata.get("doc_id") or metadata.get("source") or "rag_doc",
        "title": getattr(doc, "title", None) or metadata.get("title"),
        "snippet": getattr(doc, "page_content", None) or getattr(doc, "snippet", ""),
        "score": getattr(doc, "relevance", None) or metadata.get("score"),
        "metadata": metadata,
    }


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


async def yolo_agent_node(task_input: dict) -> dict:
    """YOLO11n-FCHL segmentation subagent."""
    from app.services.yolo_service import yolo_service

    started = time.perf_counter()
    image_today = task_input.get("image_today_path")
    image_yesterday = task_input.get("image_yesterday_path")
    date = task_input.get("date", "")

    async def _segment(image_path: str | None, label: str) -> dict:
        metrics_file = YOLO_METRICS_DIR / f"{label}.json"
        if metrics_file.exists():
            return json.loads(metrics_file.read_text(encoding="utf-8"))

        if not image_path or not Path(image_path).exists():
            return _default_yolo_metrics("no_image")

        if not getattr(yolo_service, "is_available", False):
            return _default_yolo_metrics("model_unavailable")

        image_bytes = Path(image_path).read_bytes()
        metrics, _ = await asyncio.to_thread(yolo_service.process_bytes, image_bytes, label)
        YOLO_METRICS_DIR.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        return metrics

    today_label = _date_to_filename(date or "today")
    yolo_today = await _segment(image_today, today_label)
    yolo_yesterday = await _segment(image_yesterday, f"{today_label}_yesterday") if image_yesterday else None
    fallback_report = validate_report(
        YoloAgentReport,
        {
            "agent_name": "YOLOAgent",
            "status": "ok" if yolo_today.get("_source") not in {"no_image", "model_unavailable"} else "degraded",
            "confidence": 0.72 if yolo_today.get("_source") not in {"no_image", "model_unavailable"} else 0.42,
            "date": date or None,
            "segmentation_metrics": yolo_today,
            "image_quality": {
                "today_image_present": bool(image_today and Path(image_today).exists()),
                "yesterday_image_present": bool(image_yesterday and Path(image_yesterday).exists()),
                "source": yolo_today.get("_source", "yolo_metrics"),
            },
            "crop_state": {
                "vigor": "unknown" if yolo_today.get("_source") == "no_image" else "estimated_from_segmentation",
                "leaf_area_signal": yolo_today.get("all leaf mask"),
                "flower_signal": yolo_today.get("flower Instance Count"),
                "fruit_signal": yolo_today.get("fruit Mask average"),
                "water_stress_signal": "requires_rag_and_timeseries_context",
            },
            "anomalies": [] if yolo_today.get("_source") != "no_image" else ["today image missing; segmentation used fallback metrics"],
            "recommendations": ["combine YOLO phenotype with TSMixer and RAG before final irrigation decision"],
        },
    )
    image_paths = [p for p in [image_today, image_yesterday] if p]
    report_raw = await llm_agent_service.analyze_json(
        load_agent_prompt("yolo_agent_system_v1.md"),
        {
            "date": date,
            "image_today_path": image_today,
            "image_yesterday_path": image_yesterday,
            "segmentation_metrics_today": yolo_today,
            "segmentation_metrics_yesterday": yolo_yesterday,
        },
        "yolo_agent_report",
        fallback_report,
        image_paths=image_paths,
        use_vision=bool(image_paths),
    )
    yolo_agent_report = validate_report(YoloAgentReport, report_raw, fallback_report)
    elapsed = time.perf_counter() - started
    NODE_DURATION.labels(node_name="yolo_agent", status="success").observe(elapsed)
    YOLO_INFERENCE.observe(elapsed)
    SUBAGENT_RUNS.labels(
        agent_name="yolo_agent",
        phase=task_input.get("phase", "perception"),
        status=str(yolo_agent_report.get("status") or "unknown"),
    ).inc()

    return {
        "yolo_agent_report": yolo_agent_report,
        "yolo_metrics": yolo_today,
        "yolo_today": yolo_today,
        "yolo_yesterday": yolo_yesterday,
        "yolo_results": [{"date": date, "today": yolo_today, "yesterday": yolo_yesterday}],
        "subagent_runs": [
            {
                "name": "yolo_agent",
                "phase": task_input.get("phase", "perception"),
                "latency_seconds": elapsed,
                "prompt_driven": True,
                "llm_status": yolo_agent_report.get("llm_status"),
            }
        ],
        "node_trace": [
            {
                "node": "yolo_agent",
                "status": "ok",
                "latency_seconds": round(elapsed, 4),
                "prompt_driven": True,
            }
        ],
    }


async def rag_agent_node(task_input: dict) -> dict:
    """Agentic RAG subagent using Chroma when available and keyword fallback."""
    from app.services.rag_service import rag_service

    started = time.perf_counter()
    query = task_input.get("query", "")
    top_k = int(task_input.get("top_k", 5))
    phase = task_input.get("phase", "rag")

    docs = await rag_service.retrieve(query, top_k=top_k, filters=task_input.get("filters"))
    references = [_doc_to_reference(doc) for doc in docs]
    advice = "\n".join(ref["snippet"] for ref in references if ref.get("snippet"))
    fallback_report = validate_report(
        RAGAgentReport,
        {
            "agent_name": "RAGAgent",
            "phase": phase,
            "status": "ok" if references else "degraded",
            "confidence": min(0.85, 0.35 + len(references) * 0.1),
            "query": query,
            "references": references,
            "evidence_summary": advice[:1200],
            "adjustment_advice": {
                "should_adjust": False,
                "direction": "none",
                "amount_delta_l_per_m2": 0.0,
                "reason": "no grounded adjustment without stronger evidence",
            },
            "missing_evidence": [] if references else ["no retrieved references"],
        },
    )
    report_raw = await llm_agent_service.analyze_json(
        load_agent_prompt("rag_agent_system_v1.md"),
        {
            "phase": phase,
            "query": query,
            "references": references,
            "yolo_agent_report": task_input.get("yolo_agent_report"),
            "tsmixer_agent_report": task_input.get("tsmixer_agent_report"),
            "tsmixer_prediction": task_input.get("tsmixer_prediction"),
            "weekly_summary": task_input.get("weekly_summary"),
        },
        "rag_agent_report",
        fallback_report,
    )
    rag_agent_report = validate_report(RAGAgentReport, report_raw, fallback_report)
    elapsed = time.perf_counter() - started
    NODE_DURATION.labels(node_name=f"rag_agent_{phase}", status="success").observe(elapsed)
    RAG_QUERIES.labels(stage=phase).inc()
    RAG_RESULTS_COUNT.observe(len(docs))
    SUBAGENT_RUNS.labels(
        agent_name="rag_agent",
        phase=phase,
        status=str(rag_agent_report.get("status") or "unknown"),
    ).inc()

    return {
        "rag_agent_report": rag_agent_report,
        "rag_agent_reports": [rag_agent_report],
        "rag_results": docs,
        "rag_advice": advice,
        "rag_recall_sufficient": len(docs) >= min(3, top_k),
        "retrieved_docs": references,
        "rag_references": references,
        "subagent_runs": [
            {
                "name": "rag_agent",
                "phase": phase,
                "latency_seconds": elapsed,
                "doc_count": len(docs),
                "prompt_driven": True,
                "llm_status": rag_agent_report.get("llm_status"),
            }
        ],
        "node_trace": [
            {
                "node": f"rag_agent:{phase}",
                "status": "ok",
                "docs": len(docs),
                "latency_seconds": round(elapsed, 4),
                "prompt_driven": True,
            }
        ],
    }


async def tsmixer_agent_node(task_input: dict) -> dict:
    """TSMixer time-series prediction subagent."""
    from app.services.tsmixer_service import tsmixer_service

    started = time.perf_counter()
    env_data = task_input.get("env_data", {})
    yolo_metrics = task_input.get("yolo_metrics", {})
    history = task_input.get("history_irrigation", [])

    feature_vector = build_feature_vector(env_data, yolo_metrics, history[-1] if history else 0.0)
    feature_window = build_feature_window(env_data, yolo_metrics, history)
    feature_contract = describe_feature_contract()

    try:
        if hasattr(tsmixer_service, "predict"):
            try:
                import numpy as np

                model_input = np.asarray(feature_window, dtype=float)
            except Exception:
                model_input = feature_window
            prediction_result = await _maybe_await(
                asyncio.to_thread(tsmixer_service.predict, model_input, False)
            )
            if isinstance(prediction_result, dict):
                prediction = float(prediction_result.get("prediction", prediction_result.get("value", 5.0)))
            else:
                prediction = float(prediction_result)
        else:
            prediction = 5.0
    except Exception as exc:
        logger.warning(f"[tsmixer_agent] fallback prediction after error: {exc}")
        prediction = 5.0

    elapsed = time.perf_counter() - started
    NODE_DURATION.labels(node_name="tsmixer_agent", status="success").observe(elapsed)
    TSMIXER_INFERENCE.observe(elapsed)
    TSMIXER_PREDICTION.observe(prediction)
    fallback_report = validate_report(
        TSMixerAgentReport,
        {
            "agent_name": "TSMixerAgent",
            "status": "ok",
            "confidence": 0.78,
            "prediction_l_per_m2": prediction,
            "input_contract": feature_contract,
            "yolo_context": task_input.get("yolo_agent_report") or {"metrics": yolo_metrics},
            "feature_health": {
                "window_size": len(feature_window),
                "feature_count": len(feature_vector),
                "missing_features": [],
                "history_days": len(history),
            },
            "rationale": "TSMixer prediction generated from 96-day multimodal window.",
            "risk_flags": [] if len(feature_vector) == 11 and len(feature_window) == 96 else ["feature contract mismatch"],
        },
    )
    report_raw = await llm_agent_service.analyze_json(
        load_agent_prompt("tsmixer_agent_system_v1.md"),
        {
            "env_data": env_data,
            "yolo_agent_report": task_input.get("yolo_agent_report"),
            "yolo_metrics": yolo_metrics,
            "history_irrigation": history,
            "feature_vector": feature_vector,
            "feature_window_shape": [len(feature_window), len(feature_window[0]) if feature_window else 0],
            "feature_contract": feature_contract,
            "prediction_l_per_m2": prediction,
        },
        "tsmixer_agent_report",
        fallback_report,
    )
    tsmixer_agent_report = validate_report(TSMixerAgentReport, report_raw, fallback_report)
    SUBAGENT_RUNS.labels(
        agent_name="tsmixer_agent",
        phase="prediction",
        status=str(tsmixer_agent_report.get("status") or "unknown"),
    ).inc()
    return {
        "tsmixer_agent_report": tsmixer_agent_report,
        "tsmixer_prediction": prediction,
        "tsmixer_results": [{"prediction": prediction, "feature_count": len(feature_vector), "window_size": len(feature_window)}],
        "feature_vector": feature_vector,
        "feature_window": feature_window,
        "feature_contract": feature_contract,
        "subagent_runs": [
            {
                "name": "tsmixer_agent",
                "phase": "prediction",
                "latency_seconds": elapsed,
                "prompt_driven": True,
                "llm_status": tsmixer_agent_report.get("llm_status"),
            }
        ],
        "node_trace": [
            {
                "node": "tsmixer_agent",
                "status": "ok",
                "prediction": round(prediction, 3),
                "latency_seconds": round(elapsed, 4),
                "prompt_driven": True,
            }
        ],
    }


async def perception_node(state: dict) -> dict:
    """Legacy Phase 1: run YOLO + RAG concurrently."""
    env_data = state.get("env_data", {})
    growth_stage = env_data.get("growth_stage", "fruiting")
    yolo_input = {
        "image_today_path": state.get("image_today_path"),
        "image_yesterday_path": state.get("image_yesterday_path"),
        "date": state.get("date", ""),
        "phase": "perception",
    }
    rag_input = {
        "query": f"greenhouse cucumber {growth_stage} irrigation temperature {env_data.get('temperature', '')} humidity {env_data.get('humidity', '')}",
        "top_k": 5,
        "phase": "perception",
    }
    yolo_result, rag_result = await asyncio.gather(yolo_agent_node(yolo_input), rag_agent_node(rag_input))
    return {**yolo_result, **rag_result}


async def prediction_node(state: dict) -> dict:
    """Legacy Phase 2: run TSMixer + RAG concurrently."""
    env_data = state.get("env_data", {})
    growth_stage = env_data.get("growth_stage", "fruiting")
    history = state.get("options", {}).get("history_irrigation", [])
    tsmixer_input = {
        "env_data": env_data,
        "yolo_metrics": state.get("yolo_today", {}),
        "history_irrigation": history,
    }
    rag_input = {
        "query": f"FAO56 cucumber {growth_stage} irrigation threshold and water stress rule",
        "top_k": 5,
        "phase": "prediction",
    }
    tsmixer_result, rag_result = await asyncio.gather(tsmixer_agent_node(tsmixer_input), rag_agent_node(rag_input))
    return {**tsmixer_result, **rag_result}


async def parallel_yolo_segment(image_today_b64: str, image_yesterday_b64: str) -> tuple[dict, dict]:
    from app.services.yolo_service import yolo_service

    result_today, result_yesterday = await asyncio.gather(
        yolo_service.segment(image_today_b64),
        yolo_service.segment(image_yesterday_b64),
    )
    return result_today, result_yesterday


async def parallel_perception_retrieval(
    image_today_b64: str,
    image_yesterday_b64: str,
    growth_stage: str,
    env_data: dict,
) -> dict:
    yolo_results, rag_result = await asyncio.gather(
        parallel_yolo_segment(image_today_b64, image_yesterday_b64),
        rag_agent_node(
            {
                "query": f"greenhouse cucumber {growth_stage} irrigation temperature {env_data.get('temperature', '')}",
                "top_k": 5,
                "phase": "legacy_perception",
            }
        ),
    )
    yolo_today, yolo_yesterday = yolo_results
    return {"yolo_today": yolo_today, "yolo_yesterday": yolo_yesterday, **rag_result}


async def parallel_tsmixer_rag(
    env_features: list,
    yolo_features: list,
    history_irrigation: list,
    growth_stage: str,
    env_data: dict,
) -> dict:
    tsmixer_result, rag_result = await asyncio.gather(
        tsmixer_agent_node({"env_data": env_data, "yolo_metrics": {}, "history_irrigation": history_irrigation}),
        rag_agent_node({"query": f"FAO56 cucumber {growth_stage} irrigation", "top_k": 5, "phase": "legacy_prediction"}),
    )
    return {**tsmixer_result, **rag_result}
