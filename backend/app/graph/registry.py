"""
AgentRegistry: singleton + factory pattern for dynamic prompt/tool injection.

Architecture (matching AI_TRAVEL):
- AgentRegistry: singleton, caches compiled graphs by agent_type
- PromptFactory: dynamically builds step-level prompts injecting user memory
- ToolFactory: builds tool sets per agent type
- GraphFactory: builds compiled graph with correct node topology

This enables:
1. Business logic decoupled from framework code
2. Dynamic prompt/tool injection per AgentType
3. Graph compilation caching (avoid re-compilation)
4. Easy A/B testing (swap prompts/tools without changing graph)
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, CompiledGraph
from langchain_core.tools import BaseTool


class AgentType(str, Enum):
    """Agent types in the irrigation system."""
    DAILY_DECISION = "daily_decision"
    HISTORY_QUERY = "history_query"
    MANUAL_OVERRIDE = "manual_override"
    WEEKLY_SUMMARY = "weekly_summary"
    FALLBACK_QA = "fallback_qa"
    COLLECT = "collect"
    PLAN = "plan"
    REVIEW = "review"


@dataclass
class AgentConfig:
    """Configuration for agent creation."""
    session_id: str = ""
    user_id: str = ""
    user_profile: Optional[dict] = None
    date: str = ""
    options: Optional[dict] = field(default_factory=dict)


class PromptFactory:
    """
    Factory for building step-level prompts dynamically.
    Injects user memory and context into prompt templates.
    """

    # Prompt templates per agent type
    _templates: Dict[AgentType, str] = {
        AgentType.COLLECT: """你是温室黄瓜灌溉系统的需求采集助手。
你的任务是收集灌溉决策所需的信息，包括：
1. 灌溉日期
2. 环境数据（温度、湿度、光照等）
3. 植株图像（今日 + 昨日）
4. 生长阶段

当前已采集信息：
{collected_info}

请判断信息是否完整。如果完整，调用 transfer_to_search_agent 工具；否则继续追问用户。""",

        AgentType.PLAN: """你是温室黄瓜灌溉方案生成专家。
根据以下信息生成灌溉方案：

## 环境数据
{env_data}

## YOLO 植株分析
{yolo_metrics}

## TSMixer 预测
{tsmixer_prediction}

## RAG 参考知识
{rag_advice}

## 上一轮审核意见（如有）
{critique}

请生成详细的灌溉方案（Markdown格式），包括：
1. 推荐灌水量 (L/m²)
2. 灌溉时间
3. 依据说明
4. 注意事项""",

        AgentType.REVIEW: """你是温室黄瓜灌溉方案审核专家。
请对以下灌溉方案进行评分（每项25分）：

方案：{plan}
环境数据：{env_data}
YOLO指标：{yolo_metrics}
TSMixer预测：{tsmixer_prediction}

评分维度：
1. 完整性：是否包含灌水量、时间、依据、注意事项
2. 可行性：灌水量是否在合理范围内（0.5-10 L/m²）
3. 科学性：是否基于 TSMixer 预测和 FAO56 标准
4. 一致性：是否与植株长势趋势一致

输出 JSON：{{"scores": {{...}}, "total": 0-100, "critique": "改进建议"}}""",

        AgentType.DAILY_DECISION: """你是温室黄瓜灌溉决策系统。
执行今日灌溉决策流程：
1. 加载环境数据
2. 运行 YOLO 植株分割
3. 运行 TSMixer 预测
4. 检索 RAG 知识
5. 生成灌溉方案
6. 审核与验证
7. 输出最终决策""",

        AgentType.FALLBACK_QA: """你是温室黄瓜种植专家。
用户问了一个非灌溉决策的问题，请根据知识库回答。
如果无法回答，建议用户联系种植专家。""",
    }

    @classmethod
    def build(cls, agent_type: AgentType, user_profile: Optional[dict] = None) -> str:
        """Build prompt for given agent type, injecting user profile if available."""
        template = cls._templates.get(agent_type, "你是温室黄瓜灌溉系统助手。")

        # Inject user profile into template if available
        if user_profile:
            profile_context = "\n## 用户偏好\n"
            for key, value in user_profile.items():
                profile_context += f"- {key}: {value}\n"
            template += profile_context

        return template


class ToolFactory:
    """
    Factory for building tool sets per agent type.
    Tools are bound to LLM agents for Function Calling.
    """

    @classmethod
    def build(cls, agent_type: AgentType, mcp_client=None) -> List[BaseTool]:
        """Build tool set for given agent type."""
        from app.graph.handoff import (
            transfer_to_search_agent,
            transfer_to_plan_agent,
            transfer_to_review_agent,
            transfer_to_finalize,
            transfer_to_emergency,
        )

        tools_map = {
            AgentType.COLLECT: [
                transfer_to_search_agent,
            ],
            AgentType.PLAN: [
                transfer_to_review_agent,
                transfer_to_finalize,
            ],
            AgentType.REVIEW: [
                transfer_to_finalize,
            ],
            AgentType.DAILY_DECISION: [
                transfer_to_emergency,
            ],
            AgentType.FALLBACK_QA: [],  # No tools for QA
        }

        tools = tools_map.get(agent_type, [])

        # Add MCP tools if available
        if mcp_client and agent_type in [AgentType.DAILY_DECISION, AgentType.PLAN]:
            try:
                mcp_tools = mcp_client.get_tools()
                tools.extend(mcp_tools)
            except Exception:
                pass  # MCP tools are optional

        return tools


class GraphFactory:
    """
    Factory for building compiled graphs per agent type.
    Each agent type has its own graph topology.
    """

    @classmethod
    def build(
        cls,
        agent_type: AgentType,
        prompt: str,
        tools: List[BaseTool],
    ) -> StateGraph:
        """Build StateGraph for given agent type."""
        from app.graph.state import PipelineState

        g = StateGraph(PipelineState)

        if agent_type == AgentType.COLLECT:
            cls._build_collect_graph(g, prompt, tools)
        elif agent_type == AgentType.PLAN:
            cls._build_plan_graph(g, prompt, tools)
        elif agent_type == AgentType.REVIEW:
            cls._build_review_graph(g, prompt, tools)
        else:
            # Default: single-node graph
            async def default_node(state: dict) -> dict:
                return {"node_trace": [f"{agent_type.value}_default"]}
            g.add_node("default", default_node)
            g.set_entry_point("default")

        return g

    @staticmethod
    def _build_collect_graph(g: StateGraph, prompt: str, tools: list):
        """Build collect agent graph with multi-turn dialogue."""
        from langgraph.prebuilt import ToolNode

        async def collect_node(state: dict) -> dict:
            from app.services.llm_service import llm_service
            from langchain_core.messages import AIMessage, HumanMessage

            # Build context from state
            collected = []
            if state.get("date"):
                collected.append(f"日期: {state['date']}")
            if state.get("env_data"):
                collected.append(f"环境数据: {state['env_data']}")
            if state.get("image_today_path"):
                collected.append("今日图像: 已获取")
            if state.get("image_yesterday_path"):
                collected.append("昨日图像: 已获取")

            collected_info = "\n".join(collected) if collected else "暂无"

            full_prompt = prompt.format(collected_info=collected_info)

            messages = state.get("messages", [])
            response = await llm_service.call_llm(
                system=full_prompt,
                user=messages[-1].content if messages else "",
                tools=tools,
            )

            return {
                "messages": [AIMessage(content=response)],
                "requirements_complete": len(collected) >= 3,
            }

        g.add_node("collect", collect_node)
        if tools:
            g.add_node("tools", ToolNode(tools))
            g.add_edge("collect", "tools")
        g.set_entry_point("collect")

    @staticmethod
    def _build_plan_graph(g: StateGraph, prompt: str, tools: list):
        """Build plan agent graph with critique injection."""
        async def plan_node(state: dict) -> dict:
            from app.services.llm_service import llm_service
            from langchain_core.messages import AIMessage

            critique = state.get("plan_critique", "")
            critique_section = f"\n## 上一版问题（必须修正）\n{critique}" if critique else ""

            full_prompt = prompt.format(
                env_data=state.get("env_data", {}),
                yolo_metrics=state.get("yolo_metrics", {}),
                tsmixer_prediction=state.get("tsmixer_prediction", "N/A"),
                rag_advice=state.get("rag_advice", "无"),
                critique=critique_section,
            )

            response = await llm_service.call_llm(
                system=full_prompt,
                user="请生成灌溉方案。",
                tools=tools,
            )

            return {
                "messages": [AIMessage(content=response)],
                "irrigation_plan": response,
                "plan_critique": None,  # 清空 critique
            }

        g.add_node("plan", plan_node)
        g.set_entry_point("plan")

    @staticmethod
    def _build_review_graph(g: StateGraph, prompt: str, tools: list):
        """Build review agent graph with structured scoring."""
        async def review_node(state: dict) -> dict:
            from app.services.llm_service import llm_service
            from langgraph.types import Command

            full_prompt = prompt.format(
                plan=state.get("irrigation_plan", ""),
                env_data=state.get("env_data", {}),
                yolo_metrics=state.get("yolo_metrics", {}),
                tsmixer_prediction=state.get("tsmixer_prediction", "N/A"),
            )

            response = await llm_service.call_llm(
                system=full_prompt,
                user="请评分。",
                response_format={"type": "json_object"},
            )

            import json
            result = json.loads(response)
            total = result.get("total", 0)
            critique = result.get("critique", "")
            iteration_count = state.get("iteration_count", 0)

            if total >= 80 or iteration_count >= 3:
                return Command(
                    update={"quality_score": total / 100, "sanity_passed": True},
                    goto="finalize",
                )
            else:
                return Command(
                    update={
                        "quality_score": total / 100,
                        "plan_critique": critique,
                        "iteration_count": iteration_count + 1,
                    },
                    goto="plan",
                )

        g.add_node("review", review_node)
        g.set_entry_point("review")


class AgentRegistry:
    """
    Singleton Agent registry with factory pattern.
    Caches compiled graphs by agent_type to avoid re-compilation.

    Usage:
        graph = AgentRegistry.get_or_create(
            agent_type=AgentType.DAILY_DECISION,
            config=AgentConfig(session_id="abc", user_id="user-1"),
        )
        result = await graph.ainvoke(state, config)
    """

    _instances: Dict[str, CompiledGraph] = {}

    @classmethod
    def get_or_create(
        cls,
        agent_type: AgentType,
        config: AgentConfig,
        mcp_client=None,
    ) -> CompiledGraph:
        """Get or create a compiled graph for the given agent type."""
        key = f"{agent_type}:{config.session_id}"

        if key not in cls._instances:
            # Build prompt dynamically (injects user memory)
            prompt = PromptFactory.build(agent_type, config.user_profile)

            # Build tools for this agent type
            tools = ToolFactory.build(agent_type, mcp_client)

            # Build and compile graph
            graph = GraphFactory.build(agent_type, prompt, tools)

            cls._instances[key] = graph.compile()

        return cls._instances[key]

    @classmethod
    def clear(cls, session_id: Optional[str] = None):
        """Clear cached graphs. If session_id given, clear only that session."""
        if session_id:
            keys_to_remove = [k for k in cls._instances if k.endswith(f":{session_id}")]
            for key in keys_to_remove:
                del cls._instances[key]
        else:
            cls._instances.clear()

    @classmethod
    def list_instances(cls) -> List[str]:
        """List all cached graph keys."""
        return list(cls._instances.keys())
