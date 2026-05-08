"""
Collect Agent node: multi-turn dialogue for requirement gathering.

Architecture (matching AI_TRAVEL):
- Uses create_react_agent with Handoff tools
- LLM autonomously decides when requirements are complete
- Calls transfer_to_search_agent when all fields collected
- Continues asking questions if fields are missing

Required fields for irrigation decision:
1. date — 灌溉日期
2. env_data — 环境数据（温度、湿度、光照等）
3. image_today_path — 今日植株图像
4. growth_stage — 生长阶段
"""
from __future__ import annotations

from loguru import logger
from langchain_core.messages import AIMessage, HumanMessage

from app.services.llm_service import llm_service
from app.graph.handoff import transfer_to_search_agent
from app.observability.decorators import traced_node


# Collect Agent system prompt with boundary conditions
COLLECT_SYSTEM_PROMPT = """你是温室黄瓜灌溉系统的需求采集助手。你的任务是收集灌溉决策所需的全部信息。

## 必需字段
1. **灌溉日期** — 用户想查询哪天的灌溉决策
2. **环境数据** — 温度、湿度、光照、CO2浓度等（系统可自动获取）
3. **植株图像** — 今日和昨日的植株照片（系统可自动获取）
4. **生长阶段** — 苗期/花期/果期/采收期

## 当前已采集信息
{collected_info}

## 工作流程
1. 检查上述字段是否齐全
2. 如果齐全，调用 transfer_to_search_agent 工具完成移交
3. 如果不齐全，向用户追问缺失信息（每次只问一个问题）
4. 如果用户说"今天"或没有指定日期，默认为今天的日期

## 边界情况处理
- 如果用户同时提供多个信息，一次性记录
- 如果用户拒绝提供某信息，使用系统默认值并说明
- 如果用户意图不明确，追问确认
"""


@traced_node("collect_agent")
async def run(state: dict) -> dict:
    """
    Collect Agent: multi-turn dialogue for requirement gathering.

    Returns:
        - Updates messages with AI response
        - Updates user_requirements if complete
        - LLM may call transfer_to_search_agent tool (detected by conditional edge)
    """
    date = state.get("date", "")
    env_data = state.get("env_data")
    image_today = state.get("image_today_path")
    image_yesterday = state.get("image_yesterday_path")
    growth_stage = state.get("env_data", {}).get("growth_stage", "") if env_data else ""
    messages = state.get("messages", [])

    # Build collected info summary
    collected = []
    if date:
        collected.append(f"- 灌溉日期: {date}")
    if env_data:
        collected.append(f"- 环境数据: 已获取 ({len(env_data)} 项)")
    if image_today:
        collected.append("- 今日图像: 已获取")
    if image_yesterday:
        collected.append("- 昨日图像: 已获取")
    if growth_stage:
        collected.append(f"- 生长阶段: {growth_stage}")

    collected_info = "\n".join(collected) if collected else "暂无"

    # Check if requirements are complete
    is_complete = bool(date and env_data and image_today and growth_stage)

    if is_complete:
        logger.info("[collect_agent] 需求完整，移交搜索 Agent")
        # Requirements complete → LLM should call transfer_to_search_agent
        system_prompt = COLLECT_SYSTEM_PROMPT.format(collected_info=collected_info)
        user_msg = messages[-1].content if messages else "请执行灌溉决策"

        response = await llm_service.call_llm(
            system=system_prompt,
            user=user_msg,
            tools=[transfer_to_search_agent],
        )

        return {
            "messages": [AIMessage(content=response)],
            "user_requirements": {
                "date": date,
                "env_data": env_data,
                "image_today_path": image_today,
                "image_yesterday_path": image_yesterday,
                "growth_stage": growth_stage,
            },
            "requirements_complete": True,
            "node_trace": [{"node": "collect_agent", "status": "complete"}],
        }
    else:
        logger.info("[collect_agent] 需求不完整，继续追问")
        # Requirements incomplete → ask for missing fields
        missing = []
        if not date:
            missing.append("灌溉日期")
        if not env_data:
            missing.append("环境数据")
        if not image_today:
            missing.append("植株图像")
        if not growth_stage:
            missing.append("生长阶段")

        system_prompt = COLLECT_SYSTEM_PROMPT.format(collected_info=collected_info)
        user_msg = messages[-1].content if messages else ""

        response = await llm_service.call_llm(
            system=system_prompt,
            user=f"用户说：{user_msg}\n\n请追问缺失信息：{', '.join(missing)}",
        )

        return {
            "messages": [AIMessage(content=response)],
            "requirements_complete": False,
            "node_trace": [{"node": "collect_agent", "status": "asking", "missing": missing}],
        }
