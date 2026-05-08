"""Top-level Router Agent for the irrigation LangGraph."""
from __future__ import annotations

import json
import re

from app.core.config import get_active_openai_config
from app.services.llm_service import llm_service


ROUTER_SYSTEM_PROMPT = """你是温室黄瓜灌溉智能决策系统的意图路由器。
只返回 JSON: {"intent": "...", "confidence": 0.0-1.0, "reason": "..."}。
可选 intent:
- daily_decision: 每日灌水决策、预测、重新运行
- history_query: 历史记录、某天方案、趋势查询
- manual_override: 人工覆盖或手动修改灌水量
- weekly_summary: 周报、周度总结
- fallback_qa: 种植知识、系统使用或无法归类的问题
优先级: manual_override > daily_decision > history_query > weekly_summary > fallback_qa。
"""


def _heuristic_intent(user_input: str | None) -> dict:
    text = (user_input or "").strip().lower()
    if not text or re.fullmatch(r"\d{4}-\d{2}-\d{2}|\d{4}|\d{8}", text):
        return {"intent": "daily_decision", "confidence": 1.0, "reason": "empty/date input defaults to daily decision"}

    if any(word in text for word in ["override", "manual", "手动", "覆盖", "改成", "修改"]):
        return {"intent": "manual_override", "confidence": 0.88, "reason": "manual override keyword"}
    if any(word in text for word in ["history", "episode", "历史", "记录", "趋势", "某天"]):
        return {"intent": "history_query", "confidence": 0.82, "reason": "history keyword"}
    if any(word in text for word in ["weekly", "summary", "周报", "周度", "总结"]):
        return {"intent": "weekly_summary", "confidence": 0.82, "reason": "weekly summary keyword"}
    if any(word in text for word in ["灌水", "灌溉", "预测", "决策", "irrigation", "predict", "decision"]):
        return {"intent": "daily_decision", "confidence": 0.86, "reason": "decision keyword"}
    return {"intent": "fallback_qa", "confidence": 0.65, "reason": "fallback heuristic"}


async def classify_intent(user_input: str, date: str | None = None) -> dict:
    """Classify intent with Qwen/OpenAI-compatible LLM and heuristic fallback."""
    fallback = _heuristic_intent(user_input)
    if fallback["confidence"] >= 0.85:
        return fallback

    if not get_active_openai_config().get("api_key"):
        return fallback

    try:
        response = await llm_service.call_llm(
            system=ROUTER_SYSTEM_PROMPT,
            user=f"用户输入: {user_input}\n当前日期: {date or 'unknown'}",
            response_format={"type": "json_object"},
        )
        result = json.loads(response)
        return {
            "intent": result.get("intent", fallback["intent"]),
            "confidence": float(result.get("confidence", fallback["confidence"])),
            "reason": result.get("reason", ""),
        }
    except Exception:
        return fallback


def route_by_intent(state: dict) -> str:
    intent = state.get("intent", "daily_decision")
    return {
        "daily_decision": "daily_decision_subgraph",
        "history_query": "history_query_subgraph",
        "manual_override": "manual_override_subgraph",
        "weekly_summary": "weekly_summary_subgraph",
        "fallback_qa": "fallback_qa_subgraph",
    }.get(intent, "fallback_qa_subgraph")
