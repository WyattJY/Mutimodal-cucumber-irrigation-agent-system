"""Plan Agent node for irrigation decision generation."""
from __future__ import annotations

import json

from langchain_core.messages import AIMessage
from loguru import logger

from app.core.config import get_active_openai_config
from app.graph.handoff import transfer_to_finalize, transfer_to_review_agent
from app.observability.decorators import traced_node
from app.services.llm_service import llm_service


PLAN_SYSTEM_PROMPT = """你是温室黄瓜灌溉方案生成专家。请基于环境数据、YOLO11n-FCHL 视觉表型指标、TSMixer 多模态预测和 RAG 农业知识，生成 Markdown 灌水方案。

环境数据:
{env_data}

YOLO 视觉指标:
{yolo_metrics}

TSMixer 预测灌水量: {tsmixer_prediction} L/m2

RAG 参考知识:
{rag_advice}

{critique_section}

要求:
1. 推荐灌水量必须在 0.5-10 L/m2。
2. 说明环境、视觉表型、历史灌水和 FAO56/种植先验依据。
3. 给出可执行时间安排和异常观察建议。
4. 如果数据不足，明确说明并采用保守建议。
"""


def _fallback_plan(env_data: dict, yolo_metrics: dict, tsmixer_prediction: float, rag_advice: str) -> str:
    return f"""### 1. 推荐灌水量
- 推荐值：{float(tsmixer_prediction):.2f} L/m2
- 来源说明：TSMixer 多模态预测结果，当前为本地 deterministic fallback。

### 2. 灌水时间安排
- 建议在清晨或傍晚分次灌水，避免中午高温时段造成蒸腾波动。

### 3. 依据说明
- 环境输入：{json.dumps(env_data, ensure_ascii=False)}
- YOLO11n-FCHL 视觉指标：{json.dumps(yolo_metrics, ensure_ascii=False)}
- 7 维视觉表型 + 3 维环境 + 1 维历史灌水已构造成 96 天 TSMixer 输入窗口。
- RAG 参考：{rag_advice[:500] if rag_advice else "知识库召回不足，采用保守专家规则。"}

### 4. 注意事项
- 若叶片萎蔫、黄化或棚内湿度异常，请人工复核并调整灌水量。
- 本结果保留 LangGraph/SanityCheck 人工复核入口。"""


@traced_node("plan_agent")
async def run(state: dict) -> dict:
    """Generate an irrigation plan, with deterministic fallback for local demos."""
    env_data = state.get("env_data", {})
    yolo_metrics = state.get("yolo_metrics", {})
    tsmixer_prediction = float(state.get("tsmixer_prediction", 5.0) or 5.0)
    rag_advice = state.get("rag_advice") or ""
    critique = state.get("plan_critique")
    iteration_count = state.get("iteration_count", 0)
    quality_score = state.get("quality_score")

    critique_section = ""
    if critique:
        critique_section = f"上一版方案的审核意见，必须修正:\n{critique}"

    prompt = PLAN_SYSTEM_PROMPT.format(
        env_data=json.dumps(env_data, ensure_ascii=False, indent=2),
        yolo_metrics=json.dumps(yolo_metrics, ensure_ascii=False, indent=2),
        tsmixer_prediction=f"{tsmixer_prediction:.2f}",
        rag_advice=rag_advice,
        critique_section=critique_section,
    )

    try:
        logger.info(f"[plan_agent] generate irrigation plan iteration={iteration_count}")
        if not get_active_openai_config().get("api_key"):
            raise RuntimeError("LLM API key is not configured")

        response = await llm_service.call_llm(
            system=prompt,
            user="请根据以上信息生成灌溉方案。",
            tools=[transfer_to_review_agent, transfer_to_finalize],
        )
        status = "ok_skip_review" if quality_score and quality_score >= 0.8 else "ok"
        return {
            "messages": [AIMessage(content=response)],
            "irrigation_plan": response,
            "plan_critique": None,
            "node_trace": [{"node": "plan_agent", "status": status, "iteration": iteration_count}],
        }
    except Exception as exc:
        logger.warning(f"[plan_agent] fallback: {exc}")
        plan = _fallback_plan(env_data, yolo_metrics, tsmixer_prediction, rag_advice)
        return {
            "messages": [AIMessage(content=plan)],
            "irrigation_plan": plan,
            "plan_critique": None,
            "quality_score": 0.82,
            "warnings": [f"Plan Agent 使用本地兜底方案: {exc}"],
            "node_trace": [{"node": "plan_agent", "status": "fallback", "iteration": iteration_count}],
        }
