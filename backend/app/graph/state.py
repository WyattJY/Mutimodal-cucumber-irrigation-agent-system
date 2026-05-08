"""
Pipeline State — carries all data through the LangGraph execution.

Each node reads what it needs and returns only the keys it updates.
Fields using Annotated[list, operator.add] accumulate across nodes (Reducer merge).

Communication pattern: Shared State (blackboard) + Reducer merge for parallel writes.
"""
from __future__ import annotations

import operator
from typing import TypedDict, Optional, List, Annotated
from langchain_core.messages import BaseMessage


class PipelineState(TypedDict, total=False):
    # Runtime identity for LangGraph checkpointer/store and long-term memory
    thread_id: Optional[str]
    user_id: Optional[str]
    greenhouse_id: Optional[str]
    runtime_profile: Optional[dict]
    # ── Messages (对话历史) ──────────────────────────────
    messages: Annotated[List[BaseMessage], operator.add]

    # ── Router / Intent ─────────────────────────────────
    intent: Optional[str]
    intent_confidence: Optional[float]

    # ── Collect Agent (需求采集) ─────────────────────────
    user_requirements: Optional[dict]  # 采集到的灌溉决策需求
    requirements_complete: bool        # 需求是否完整

    # ── Inputs ──────────────────────────────────────────
    date: str
    image_path: Optional[str]
    image_base64: Optional[str]
    env_data: Optional[dict]
    options: Optional[dict]

    # ── Image data ──────────────────────────────────────
    image_today_path: Optional[str]
    image_today_b64: Optional[str]
    image_yesterday_path: Optional[str]
    image_yesterday_b64: Optional[str]

    # ── YOLO output (Sub-agent 并行写入) ────────────────
    yolo_today: Optional[dict]
    yolo_yesterday: Optional[dict]
    yolo_metrics: Optional[dict]
    yolo_agent_report: Optional[dict]
    yolo_results: Annotated[List[dict], operator.add]  # Reducer: parallel sub-agent writes

    # ── Cold start ──────────────────────────────────────
    is_cold_start: bool

    # ── TSMixer (Sub-agent) ─────────────────────────────
    tsmixer_prediction: Optional[float]
    tsmixer_results: Annotated[List[dict], operator.add]  # Reducer: parallel sub-agent writes
    feature_vector: Optional[list]
    feature_window: Optional[list]
    feature_contract: Optional[dict]
    tsmixer_agent_report: Optional[dict]

    # ── RAG (Sub-agent) ─────────────────────────────────
    rag_results: Optional[list]
    rag_advice: Optional[str]
    retrieved_docs: Annotated[list, operator.add]
    rag_references: Annotated[list, operator.add]
    rag_agent_report: Optional[dict]
    rag_agent_reports: Annotated[List[dict], operator.add]
    rag_recall_sufficient: bool  # RAG 召回是否充足

    # ── Plan Agent (内容生成) ────────────────────────────
    irrigation_plan: Optional[str]  # 生成的灌溉方案（Markdown）
    plan_critique: Optional[str]    # 审核意见（反思循环）
    quality_score: Optional[float]  # 方案质量评分

    # ── LLM PlantResponse ──────────────────────────────
    plant_response: Optional[dict]

    # ── Anomaly ─────────────────────────────────────────
    anomaly_result: Optional[dict]
    has_anomaly: bool
    anomaly_severity: Optional[str]

    # ── SanityCheck ─────────────────────────────────────
    sanity_check: Optional[dict]
    sanity_passed: bool

    # ── Final ───────────────────────────────────────────
    irrigation_amount: Optional[float]
    prediction_source: Optional[str]
    main_agent_decision: Optional[dict]
    subagent_summary: Optional[dict]
    warnings: Annotated[list, operator.add]
    suggestions: Annotated[list, operator.add]

    # ── Persistence ─────────────────────────────────────
    episode_id: Optional[str]
    response_saved_path: Optional[str]

    # ── Memory ──────────────────────────────────────────
    user_memory: Optional[dict]  # 长期用户记忆（注入用）

    # ── Graph metadata ──────────────────────────────────
    iteration_count: int
    error: Optional[str]
    node_trace: Annotated[list, operator.add]
    subagent_runs: Annotated[list, operator.add]
    started_at: Optional[str]
