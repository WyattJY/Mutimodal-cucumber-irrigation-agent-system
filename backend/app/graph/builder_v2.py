"""AI_TRAVEL-style LangGraph for greenhouse cucumber irrigation.

Business domain remains "基于多模态融合的温室黄瓜灌水决策智能体研究".
The engineering pattern is the AI_TRAVEL stack:

- Router + Handoff + Subagent
- LangGraph Send API fan-out/fan-in
- PostgreSQL checkpointer/store when available, memory fallback locally
- YOLO11n-FCHL, TSMixer and Agentic RAG as independent subagents
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from app.graph.edges import route_after_anomaly, route_after_load_env, route_after_rag, route_after_sanity
from app.graph.agent_schemas import MainAgentDecision, validate_report
from app.graph.handoff import route_after_collect, route_after_plan
from app.graph.router import classify_intent, route_by_intent
from app.graph.runtime import GraphRuntime, graph_runtime
from app.graph.state import PipelineState
from app.graph.subagent import rag_agent_node, tsmixer_agent_node, yolo_agent_node
from app.graph.nodes import anomaly_detect, collect_agent, finalize, load_env, plant_response, sanity_check
from app.graph.nodes import plan_agent
from app.observability.metrics import AGENT_INTENT_ROUTES
from app.services.llm_agent_service import load_agent_prompt, llm_agent_service


def _perception_query(state: dict) -> str:
    env = state.get("env_data", {}) or {}
    stage = env.get("growth_stage", "fruiting")
    return (
        f"greenhouse cucumber {stage} irrigation visual phenotype FAO56 "
        f"temperature {env.get('temperature', '')} humidity {env.get('humidity', '')}"
    )


def _prediction_query(state: dict) -> str:
    env = state.get("env_data", {}) or {}
    stage = env.get("growth_stage", "fruiting")
    prediction = state.get("tsmixer_prediction", "")
    return f"FAO56 cucumber {stage} irrigation threshold water stress TSMixer prediction {prediction}"


async def perception_dispatch_node(state: PipelineState) -> dict:
    return {"node_trace": [{"node": "perception_dispatch", "status": "fanout"}]}


def route_to_perception_agents(state: PipelineState):
    return [
        Send(
            "yolo_agent",
            {
                "image_today_path": state.get("image_today_path"),
                "image_yesterday_path": state.get("image_yesterday_path"),
                "date": state.get("date", ""),
                "phase": "perception",
            },
        ),
        Send(
            "rag_perception_agent",
            {
                "query": _perception_query(state),
                "top_k": 5,
                "phase": "perception",
                "filters": {"domain": "cucumber_irrigation"} if state.get("options", {}).get("use_rag_filters") else None,
            },
        ),
    ]


async def perception_join_node(state: PipelineState) -> dict:
    return {"node_trace": [{"node": "perception_join", "status": "merged"}]}


async def prediction_dispatch_node(state: PipelineState) -> dict:
    return {"node_trace": [{"node": "prediction_dispatch", "status": "fanout"}]}


def route_to_prediction_agents(state: PipelineState):
    history = (state.get("options") or {}).get("history_irrigation", [])
    return [
        Send(
            "tsmixer_agent",
            {
                "env_data": state.get("env_data", {}),
                "yolo_metrics": state.get("yolo_today", {}),
                "yolo_agent_report": state.get("yolo_agent_report"),
                "history_irrigation": history,
            },
        ),
        Send(
            "rag_prediction_agent",
            {
                "query": _prediction_query(state),
                "top_k": 5,
                "phase": "prediction",
                "filters": {"domain": "cucumber_irrigation"} if state.get("options", {}).get("use_rag_filters") else None,
                "yolo_agent_report": state.get("yolo_agent_report"),
                "tsmixer_prediction": state.get("tsmixer_prediction"),
            },
        ),
    ]


async def prediction_join_node(state: PipelineState) -> dict:
    prediction = float(state.get("tsmixer_prediction") or 5.0)
    final_value = max(0.5, min(10.0, prediction))
    rag_reports = state.get("rag_agent_reports") or []
    references = state.get("rag_references") or state.get("retrieved_docs") or []
    subagent_summary = {
        "yolo": state.get("yolo_agent_report"),
        "tsmixer": state.get("tsmixer_agent_report"),
        "rag": rag_reports,
    }
    fallback_decision = validate_report(
        MainAgentDecision,
        {
            "agent_name": "MainAgent",
            "status": "ok" if state.get("tsmixer_agent_report") else "degraded",
            "final_irrigation_l_per_m2": final_value,
            "confidence": 0.76 if state.get("tsmixer_agent_report") else 0.5,
            "explanation": "Aggregated YOLOAgent, TSMixerAgent and RAGAgent outputs; TSMixer prediction is used as the base irrigation value.",
            "references": references[:8],
            "subagent_summary": subagent_summary,
            "risk_flags": [],
        },
    )
    decision_raw = await llm_agent_service.analyze_json(
        load_agent_prompt("main_agent_system_v1.md"),
        {
            "date": state.get("date"),
            "env_data": state.get("env_data", {}),
            "yolo_agent_report": state.get("yolo_agent_report"),
            "tsmixer_agent_report": state.get("tsmixer_agent_report"),
            "rag_agent_reports": rag_reports,
            "tsmixer_prediction": prediction,
            "references": references[:8],
        },
        "main_agent_decision",
        fallback_decision,
    )
    main_agent_decision = validate_report(MainAgentDecision, decision_raw, fallback_decision)
    return {
        "main_agent_decision": main_agent_decision,
        "subagent_summary": main_agent_decision.get("subagent_summary", subagent_summary),
        "node_trace": [
            {
                "node": "prediction_join",
                "status": "merged",
                "main_agent": "ok",
                "final_irrigation": main_agent_decision.get("final_irrigation_l_per_m2"),
            }
        ],
    }


def build_daily_decision_subgraph() -> StateGraph:
    g = StateGraph(PipelineState)

    g.add_node("load_env", load_env.run)
    g.add_node("collect_agent", collect_agent.run)
    g.add_node("perception_dispatch", perception_dispatch_node)
    g.add_node("yolo_agent", yolo_agent_node)
    g.add_node("rag_perception_agent", rag_agent_node)
    g.add_node("perception_join", perception_join_node)
    g.add_node("prediction_dispatch", prediction_dispatch_node)
    g.add_node("tsmixer_agent", tsmixer_agent_node)
    g.add_node("rag_prediction_agent", rag_agent_node)
    g.add_node("prediction_join", prediction_join_node)
    g.add_node("plan_agent", plan_agent.run)
    g.add_node("plant_response", plant_response.run)
    g.add_node("anomaly_detect", anomaly_detect.run)
    g.add_node("sanity_check", sanity_check.run)
    g.add_node("finalize", finalize.run)
    g.add_node("finalize_emergency", finalize.run_emergency)

    g.set_entry_point("load_env")

    g.add_conditional_edges(
        "load_env",
        route_after_load_env,
        {
            "collect_agent": "collect_agent",
            "perception_dispatch": "perception_dispatch",
        },
    )
    g.add_conditional_edges(
        "collect_agent",
        route_after_collect,
        {
            "search_agent": "perception_dispatch",
            "collect_agent": "collect_agent",
        },
    )

    g.add_conditional_edges("perception_dispatch", route_to_perception_agents)
    g.add_edge(["yolo_agent", "rag_perception_agent"], "perception_join")
    g.add_edge("perception_join", "prediction_dispatch")

    g.add_conditional_edges("prediction_dispatch", route_to_prediction_agents)
    g.add_edge(["tsmixer_agent", "rag_prediction_agent"], "prediction_join")
    g.add_conditional_edges(
        "prediction_join",
        route_after_rag,
        {
            "plan_agent": "plan_agent",
            "collect_agent": "collect_agent",
        },
    )

    g.add_conditional_edges(
        "plan_agent",
        route_after_plan,
        {
            "review_agent": "plant_response",
            "finalize": "finalize",
        },
    )
    g.add_edge("plant_response", "anomaly_detect")
    g.add_conditional_edges(
        "anomaly_detect",
        route_after_anomaly,
        {
            "sanity_check": "sanity_check",
            "finalize_emergency": "finalize_emergency",
        },
    )
    g.add_conditional_edges(
        "sanity_check",
        route_after_sanity,
        {
            "finalize": "finalize",
            "plant_response": "plant_response",
        },
    )
    g.add_edge("finalize", END)
    g.add_edge("finalize_emergency", END)
    return g


async def history_query_node(state: PipelineState) -> dict:
    from app.services.memory_service import memory_service

    date = state.get("date")
    episode = await memory_service.get_episode(date) if date else None
    return {
        "suggestions": [f"history_query date={date} found={episode is not None}"],
        "node_trace": [{"node": "history_query", "status": "ok", "found": episode is not None}],
    }


async def manual_override_node(state: PipelineState) -> dict:
    options = state.get("options", {}) or {}
    amount = options.get("override_amount")
    if amount is None:
        return {
            "error": "override_amount is required",
            "warnings": ["人工覆盖失败：缺少 override_amount"],
            "node_trace": [{"node": "manual_override", "status": "error"}],
        }
    return {
        "irrigation_amount": float(amount),
        "prediction_source": "override",
        "suggestions": [f"用户人工覆盖为 {float(amount):.2f} L/m2"],
        "node_trace": [{"node": "manual_override", "status": "ok", "value": float(amount)}],
    }


async def weekly_summary_node(state: PipelineState) -> dict:
    from app.services.memory_service import memory_service

    weekly_context = await memory_service.get_weekly_prompt_block()
    return {
        "suggestions": [weekly_context or "暂无周度记忆摘要"],
        "node_trace": [{"node": "weekly_summary", "status": "ok"}],
    }


async def fallback_qa_node(state: PipelineState) -> dict:
    from app.services.rag_service import rag_service

    query = (state.get("options") or {}).get("user_input", "")
    docs = await rag_service.retrieve(query or "greenhouse cucumber irrigation", top_k=3)
    return {
        "rag_results": docs,
        "suggestions": [getattr(doc, "page_content", "") for doc in docs],
        "node_trace": [{"node": "fallback_qa", "status": "ok", "docs": len(docs)}],
    }


def _compile_subgraph(builder):
    return builder().compile()


def build_history_query_subgraph() -> StateGraph:
    g = StateGraph(PipelineState)
    g.add_node("query", history_query_node)
    g.set_entry_point("query")
    g.add_edge("query", END)
    return g


def build_manual_override_subgraph() -> StateGraph:
    g = StateGraph(PipelineState)
    g.add_node("override", manual_override_node)
    g.set_entry_point("override")
    g.add_edge("override", END)
    return g


def build_weekly_summary_subgraph() -> StateGraph:
    g = StateGraph(PipelineState)
    g.add_node("summary", weekly_summary_node)
    g.set_entry_point("summary")
    g.add_edge("summary", END)
    return g


def build_fallback_qa_subgraph() -> StateGraph:
    g = StateGraph(PipelineState)
    g.add_node("qa", fallback_qa_node)
    g.set_entry_point("qa")
    g.add_edge("qa", END)
    return g


def build_irrigation_graph() -> StateGraph:
    g = StateGraph(PipelineState)

    async def router_node(state: PipelineState) -> dict:
        options = state.get("options", {}) or {}
        classification = await classify_intent(options.get("user_input", ""), state.get("date"))
        AGENT_INTENT_ROUTES.labels(intent=classification["intent"]).inc()
        return {
            "intent": classification["intent"],
            "intent_confidence": classification["confidence"],
            "node_trace": [
                {
                    "node": "router",
                    "intent": classification["intent"],
                    "confidence": classification["confidence"],
                    "reason": classification.get("reason", ""),
                }
            ],
        }

    g.add_node("router", router_node)
    g.add_node("daily_decision_subgraph", _compile_subgraph(build_daily_decision_subgraph))
    g.add_node("history_query_subgraph", _compile_subgraph(build_history_query_subgraph))
    g.add_node("manual_override_subgraph", _compile_subgraph(build_manual_override_subgraph))
    g.add_node("weekly_summary_subgraph", _compile_subgraph(build_weekly_summary_subgraph))
    g.add_node("fallback_qa_subgraph", _compile_subgraph(build_fallback_qa_subgraph))

    g.set_entry_point("router")
    g.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "daily_decision_subgraph": "daily_decision_subgraph",
            "history_query_subgraph": "history_query_subgraph",
            "manual_override_subgraph": "manual_override_subgraph",
            "weekly_summary_subgraph": "weekly_summary_subgraph",
            "fallback_qa_subgraph": "fallback_qa_subgraph",
        },
    )
    g.add_edge("daily_decision_subgraph", END)
    g.add_edge("history_query_subgraph", END)
    g.add_edge("manual_override_subgraph", END)
    g.add_edge("weekly_summary_subgraph", END)
    g.add_edge("fallback_qa_subgraph", END)
    return g


def compile_irrigation_graph(runtime: GraphRuntime | None = None):
    active_runtime = runtime or graph_runtime
    return build_irrigation_graph().compile(
        checkpointer=active_runtime.checkpointer,
        store=active_runtime.store,
        name="cucumber_irrigation_ai_travel_graph",
    )


irrigation_graph = compile_irrigation_graph()


def set_irrigation_graph_runtime(runtime: GraphRuntime):
    global irrigation_graph
    irrigation_graph = compile_irrigation_graph(runtime)
    return irrigation_graph


def get_irrigation_graph():
    return irrigation_graph
