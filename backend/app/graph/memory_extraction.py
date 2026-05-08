"""
Post-conversation memory extraction module.

Architecture (matching AI_TRAVEL):
- After conversation ends, async LLM extracts structured memory
- recency_wins merge strategy: new information overrides old
- 90-day decay: old unused preferences are downweighted
- Memory stored in PostgreSQL Store (user-level, cross-session)

Memory types:
1. irrigation_preferences — 用户灌溉偏好
2. growth_patterns — 植株生长模式
3. anomaly_history — 异常处理历史
4. decision_feedback — 决策反馈（用户是否采纳）
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from pydantic import BaseModel, Field


# ── Memory Schema ──────────────────────────────────────────

class IrrigationMemory(BaseModel):
    """Structured memory extracted from conversation."""
    user_id: str
    session_id: str
    extracted_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Irrigation preferences
    preferred_irrigation_time: Optional[str] = None  # e.g., "morning", "evening"
    preferred_amount_range: Optional[tuple[float, float]] = None  # e.g., (2.0, 5.0)
    risk_tolerance: Optional[str] = None  # "conservative", "moderate", "aggressive"

    # Growth patterns observed
    common_growth_stage: Optional[str] = None
    typical_leaf_count: Optional[float] = None
    typical_flower_count: Optional[float] = None

    # Anomaly patterns
    frequent_anomalies: List[str] = Field(default_factory=list)
    anomaly_resolution_patterns: Dict[str, str] = Field(default_factory=dict)

    # Decision feedback
    decisions_accepted: int = 0
    decisions_rejected: int = 0
    common_override_reasons: List[str] = Field(default_factory=list)

    # Environmental patterns
    typical_temperature_range: Optional[tuple[float, float]] = None
    typical_humidity_range: Optional[tuple[float, float]] = None


class MemoryExtractionPrompt:
    """Prompt template for memory extraction."""

    SYSTEM = """你是温室黄瓜灌溉系统的记忆提取专家。
从以下对话历史中提取有价值的记忆片段。

## 提取维度
1. **灌溉偏好** — 用户喜欢的灌溉时间、灌水量范围、风险偏好
2. **生长模式** — 植株的典型生长指标（叶片数、花数等）
3. **异常模式** — 常见异常类型及处理方式
4. **决策反馈** — 用户是否采纳系统建议，拒绝的原因
5. **环境模式** — 典型的温湿度范围

## 输出格式
严格输出 JSON，不要添加任何其他文本：
{{
    "preferred_irrigation_time": "morning/evening/noon 或 null",
    "preferred_amount_range": [min, max] 或 null,
    "risk_tolerance": "conservative/moderate/aggressive 或 null",
    "common_growth_stage": "seedling/flowering/fruiting/harvest 或 null",
    "typical_leaf_count": 数字或null,
    "typical_flower_count": 数字或null,
    "frequent_anomalies": ["A1", "A2"],
    "anomaly_resolution_patterns": {{"A1": "处理方式"}},
    "decisions_accepted": 数字,
    "decisions_rejected": 数字,
    "common_override_reasons": ["原因1"],
    "typical_temperature_range": [min, max] 或 null,
    "typical_humidity_range": [min, max] 或 null
}}

## 规则
- 只提取有明确证据的信息，不要推测
- 如果对话中没有相关信息，该字段设为 null
- 数值字段取对话中提到的平均值
"""

    USER = "以下是本次对话历史：\n\n{messages}"


# ── Memory Merge Strategy ──────────────────────────────────

def merge_memories(
    existing: Optional[Dict[str, Any]],
    new: Dict[str, Any],
    strategy: str = "recency_wins",
) -> Dict[str, Any]:
    """
    Merge new memory with existing memory.

    Strategy:
    - recency_wins: new values override old values for scalar fields
    - append: list fields are merged (deduplicated)
    - numeric_avg: numeric fields are averaged with recency bias
    """
    if existing is None:
        return new

    merged = existing.copy()

    for key, new_value in new.items():
        if new_value is None:
            continue

        old_value = merged.get(key)

        if old_value is None:
            # No existing value → use new
            merged[key] = new_value
        elif isinstance(new_value, list) and isinstance(old_value, list):
            # List fields: merge and deduplicate
            merged[key] = list(set(old_value + new_value))
        elif isinstance(new_value, dict) and isinstance(old_value, dict):
            # Dict fields: merge (new overrides old)
            merged[key] = {**old_value, **new_value}
        elif isinstance(new_value, (int, float)) and isinstance(old_value, (int, float)):
            # Numeric fields: weighted average (70% new, 30% old)
            merged[key] = new_value * 0.7 + old_value * 0.3
        else:
            # Scalar fields: recency_wins (new overrides old)
            if strategy == "recency_wins":
                merged[key] = new_value

    return merged


# ── Memory Decay ───────────────────────────────────────────

def apply_memory_decay(
    memory: Dict[str, Any],
    decay_days: int = 90,
) -> Dict[str, Any]:
    """
    Apply decay to memory fields based on last update time.

    Fields not updated within decay_days are downweighted:
    - Numeric fields are multiplied by 0.5
    - List fields have stale items removed
    - Scalar fields are kept (decay doesn't remove them)
    """
    now = datetime.now()
    last_updated = memory.get("_last_updated", now.isoformat())

    try:
        last_update_time = datetime.fromisoformat(last_updated)
        days_since_update = (now - last_update_time).days
    except (ValueError, TypeError):
        days_since_update = 0

    if days_since_update < decay_days:
        return memory  # No decay needed

    # Apply decay
    decayed = memory.copy()
    decay_factor = max(0.1, 1.0 - (days_since_update - decay_days) / decay_days)

    for key, value in decayed.items():
        if key.startswith("_"):  # Skip metadata fields
            continue
        if isinstance(value, (int, float)):
            decayed[key] = value * decay_factor

    decayed["_last_updated"] = now.isoformat()
    decayed["_decay_applied"] = True

    return decayed


# ── Memory Extraction Pipeline ─────────────────────────────

async def extract_and_update_memory(
    session_id: str,
    user_id: str,
    messages: list,
    store=None,
) -> Optional[IrrigationMemory]:
    """
    Post-conversation memory extraction pipeline.

    1. Get complete conversation from Checkpointer
    2. LLM extracts structured memory
    3. Merge with existing memory (recency_wins)
    4. Apply 90-day decay
    5. Save to Store

    This runs asynchronously after the conversation ends (asyncio.create_task).
    """
    from app.services.llm_service import llm_service

    try:
        logger.info(f"[memory_extraction] 开始提取记忆: session={session_id}, user={user_id}")

        # Step 1: Format messages for extraction
        formatted_messages = []
        for msg in messages:
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")
            formatted_messages.append(f"[{role}]: {content}")

        messages_text = "\n".join(formatted_messages[-50:])  # Last 50 messages

        # Step 2: LLM extracts structured memory
        response = await llm_service.call_llm(
            system=MemoryExtractionPrompt.SYSTEM,
            user=MemoryExtractionPrompt.USER.format(messages=messages_text),
            response_format={"type": "json_object"},
            model="gpt-4o-mini",  # Use lightweight model for extraction
        )

        import json
        extracted_data = json.loads(response)

        # Add metadata
        extracted_data["user_id"] = user_id
        extracted_data["session_id"] = session_id
        extracted_data["_last_updated"] = datetime.now().isoformat()

        # Step 3: Create memory object
        new_memory = IrrigationMemory(**{
            k: v for k, v in extracted_data.items()
            if k in IrrigationMemory.model_fields
        })

        logger.info(f"[memory_extraction] 提取完成: {len(extracted_data)} 个字段")

        # Step 4: Merge with existing memory
        if store:
            existing = await store.aget(
                namespace=("irrigation_memory", user_id),
                key="profile",
            )

            merged = merge_memories(
                existing.value if existing else None,
                extracted_data,
                strategy="recency_wins",
            )

            # Step 5: Apply decay
            aged = apply_memory_decay(merged, decay_days=90)

            # Step 6: Save to store
            await store.aput(
                namespace=("irrigation_memory", user_id),
                key="profile",
                value=aged,
            )

            logger.info(f"[memory_extraction] 记忆已保存: user={user_id}")

        return new_memory

    except Exception as e:
        logger.error(f"[memory_extraction] 失败: {e}")
        return None


def schedule_memory_extraction(
    session_id: str,
    user_id: str,
    messages: list,
    store=None,
):
    """
    Schedule async memory extraction (non-blocking).

    Uses asyncio.create_task to run extraction in background.
    This is called after the conversation response is sent to the user.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                extract_and_update_memory(session_id, user_id, messages, store)
            )
        else:
            loop.run_until_complete(
                extract_and_update_memory(session_id, user_id, messages, store)
            )
    except RuntimeError:
        # No event loop running, create a new one
        asyncio.run(extract_and_update_memory(session_id, user_id, messages, store))
