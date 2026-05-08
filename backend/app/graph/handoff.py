"""
Handoff module: explicit control transfer between agents.

Two patterns (matching AI_TRAVEL):
1. Tool-based: Agent calls transfer_to_xxx() tool → conditional edge detects → routes
   - LLM autonomously decides when to handoff based on tool docstring (prompt-defined boundaries)
   - Used for: collect → search, search → plan, plan → review
2. Command-based: Agent returns Command(goto=..., update={...}) → atomic update + route
   - Used for: sanity_check → plant_response (reflection loop), anomaly → emergency

Key Handoff points:
- collect_agent → search_agent (requirements complete, via tool)
- search_agent → plan_agent (retrieval sufficient, via tool)
- plan_agent → review_agent (plan generated, via tool)
- sanity_check → plant_response (reflection: needs re-evaluation, via Command)
- sanity_check → finalize (passed or max iterations, via Command)
- anomaly_detect → finalize_emergency (severe anomaly, via Command)
"""
from __future__ import annotations

from typing import Optional
from langgraph.types import Command
from langchain_core.tools import tool


# ── Pattern 1: Tool-based Handoff ──────────────────────────
# These tools are bound to LLM agents so they can explicitly
# request a handoff to another agent.
# The LLM autonomously decides when to call based on the docstring
# (prompt-defined boundary conditions).

@tool
def transfer_to_search_agent(
    requirements_summary: str,
    missing_fields: str = "",
) -> str:
    """
    当以下条件全部满足时调用此工具完成移交：
    1. 灌溉日期已确认
    2. 环境数据已获取（温度、湿度、光照等）
    3. 植株图像已获取（今日 + 昨日）
    4. 生长阶段已确认

    如果有任何字段缺失，请在 missing_fields 中说明，不要调用此工具。

    Args:
        requirements_summary: 已采集需求的摘要
        missing_fields: 缺失字段（如果有），为空表示需求完整
    """
    if missing_fields:
        return f"需求不完整，缺失：{missing_fields}，继续追问"
    return f"移交给信息检索 Agent，需求：{requirements_summary}"


@tool
def transfer_to_plan_agent(
    retrieval_summary: str,
    recall_sufficient: bool = True,
) -> str:
    """
    当以下条件全部满足时调用此工具完成移交：
    1. YOLO 分割结果已获取
    2. TSMixer 预测结果已获取
    3. RAG 知识检索已完成
    4. 召回结果充足（至少 3 条相关文档）

    如果召回不足，请设置 recall_sufficient=False，不要调用此工具。

    Args:
        retrieval_summary: 检索结果摘要
        recall_sufficient: RAG 召回是否充足
    """
    if not recall_sufficient:
        return "RAG 召回不足，需要补充检索或澄清需求"
    return f"移交给规划生成 Agent，检索摘要：{retrieval_summary}"


@tool
def transfer_to_review_agent(
    plan_summary: str,
) -> str:
    """
    当灌溉方案草稿生成完成时调用此工具，
    将控制权移交给审核 Agent 进行质量评分。

    Args:
        plan_summary: 生成的灌溉方案摘要
    """
    return f"移交给审核 Agent，方案摘要：{plan_summary}"


@tool
def transfer_to_finalize(
    final_decision: str,
    irrigation_amount: float,
) -> str:
    """
    当以下条件之一满足时调用此工具完成移交：
    1. 审核评分 >= 0.8（质量达标）
    2. 已达到最大反思次数（3轮）
    3. 异常检测通过，无需紧急处理

    Args:
        final_decision: 最终决策摘要
        irrigation_amount: 最终灌水量 (L/m²)
    """
    return f"移交最终化，灌水量：{irrigation_amount} L/m²，决策：{final_decision}"


@tool
def transfer_to_emergency(
    anomaly_type: str,
    anomaly_severity: str,
    description: str,
) -> str:
    """
    当检测到严重异常时调用此工具，
    将控制权移交给紧急处理流程。

    Args:
        anomaly_type: 异常类型 (A1/A2/A3)
        anomaly_severity: 异常严重程度 (severe)
        description: 异常描述
    """
    return f"紧急移交: {anomaly_type} ({anomaly_severity}) - {description}"


# ── Pattern 2: Command-based Handoff ───────────────────────
# These functions return Command objects for atomic state update + routing.
# Used for: sanity_check reflection loop, anomaly emergency route

def command_handoff_to_reflect(
    sanity_result: dict,
    adjusted_value: float,
    iteration_count: int,
) -> Command:
    """
    SanityCheck → plant_response: atomic state update + route to reflection.

    This is more efficient than tool-based handoff because it:
    1. Updates state atomically (no intermediate checkpoint)
    2. Routes directly without LLM re-evaluation
    """
    return Command(
        goto="plant_response",
        update={
            "sanity_check": sanity_result,
            "sanity_passed": False,
            "iteration_count": iteration_count + 1,
            "plan_critique": f"SanityCheck 建议调整至 {adjusted_value} L/m²",
            "suggestions": [f"SanityCheck 建议调整至 {adjusted_value} L/m²"],
        }
    )


def command_handoff_to_emergency(
    anomaly_result: dict,
    anomaly_severity: str,
    warnings: list,
) -> Command:
    """
    anomaly_detect → finalize_emergency: atomic state update + emergency route.
    """
    return Command(
        goto="finalize_emergency",
        update={
            "anomaly_result": anomaly_result,
            "has_anomaly": True,
            "anomaly_severity": anomaly_severity,
            "warnings": warnings,
        }
    )


def command_handoff_to_finalize(
    sanity_result: dict,
    iteration_count: int,
) -> Command:
    """
    SanityCheck → finalize: passed or max iterations reached.
    """
    return Command(
        goto="finalize",
        update={
            "sanity_check": sanity_result,
            "sanity_passed": True,
            "iteration_count": iteration_count,
        }
    )


# ── Tool-based Handoff routing function ────────────────────
# Conditional edge inspects last AI message's tool_calls to detect handoff signal

def route_after_collect(state: dict) -> str:
    """
    Conditional edge after collect_agent:
    - Detects transfer_to_search_agent tool call → search_agent
    - Otherwise → stay in collect_agent (continue multi-turn dialogue)
    """
    from langchain_core.messages import AIMessage

    last_message = state.get("messages", [{}])[-1] if state.get("messages") else None

    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls"):
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "transfer_to_search_agent":
                return "search_agent"
            elif tool_call["name"] == "transfer_to_plan_agent":
                return "plan_agent"

    if state.get("requirements_complete"):
        return "search_agent"

    options = state.get("options", {}) or {}
    if options.get("allow_default_collection", True):
        return "search_agent"

    return "collect_agent"  # 继续追问


def route_after_search(state: dict) -> str:
    """
    Conditional edge after search_agent (perception + retrieval):
    - Detects transfer_to_plan_agent tool call → plan_agent
    - RAG recall insufficient → back to collect_agent for clarification
    - Otherwise → plan_agent (default)
    """
    from langchain_core.messages import AIMessage

    last_message = state.get("messages", [{}])[-1] if state.get("messages") else None

    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls"):
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "transfer_to_plan_agent":
                if not tool_call.get("args", {}).get("recall_sufficient", True):
                    return "collect_agent"  # RAG 召回不足，回到采集
                return "plan_agent"

    # Check RAG recall sufficiency
    if not state.get("rag_recall_sufficient", True):
        return "collect_agent"  # 召回不足，回到采集

    return "plan_agent"


def route_after_plan(state: dict) -> str:
    """
    Conditional edge after plan_agent:
    - Detects transfer_to_review_agent tool call → review_agent
    - Detects transfer_to_finalize tool call → finalize (quality sufficient)
    - Otherwise → review_agent (default)
    """
    from langchain_core.messages import AIMessage

    last_message = state.get("messages", [{}])[-1] if state.get("messages") else None

    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls"):
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "transfer_to_finalize":
                return "finalize"
            elif tool_call["name"] == "transfer_to_review_agent":
                return "review_agent"

    options = state.get("options", {}) or {}
    if options.get("skip_llm_review", True):
        return "finalize"

    if state.get("quality_score", 0) >= 0.8:
        return "finalize"

    return "review_agent"  # 默认进入审核
