from __future__ import annotations
"""Rule-M1 上下文预算控制器

控制总上下文不超过预算，超限时按优先级压缩
参考: task1.md P3-02, requirements1.md 5.1-5.2节
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json

from ..utils.token_counter import TokenCounter


@dataclass
class WorkingContext:
    """L1 工作上下文"""
    system_prompt: str
    weekly_context: Optional[str] = None
    today_input: dict = field(default_factory=dict)
    retrieval_results: List[str] = field(default_factory=list)
    total_tokens: int = 0

    def to_messages(self) -> List[dict]:
        """转换为 LLM messages 格式"""
        messages = []

        # System prompt
        system_content = self.system_prompt
        if self.weekly_context:
            system_content += f"\n\n<recent_experience>\n{self.weekly_context}\n</recent_experience>"
        messages.append({"role": "system", "content": system_content})

        # User prompt with today input and retrieval
        user_content_parts = []

        # Today input
        if self.today_input:
            user_content_parts.append(
                f"今日数据:\n```json\n{json.dumps(self.today_input, ensure_ascii=False, indent=2)}\n```"
            )

        # Retrieval results
        if self.retrieval_results:
            user_content_parts.append("参考知识:")
            for i, snippet in enumerate(self.retrieval_results, 1):
                user_content_parts.append(f"{i}. {snippet}")

        if user_content_parts:
            messages.append({"role": "user", "content": "\n\n".join(user_content_parts)})

        return messages


@dataclass
class BudgetConfig:
    """预算配置"""
    total_max: int = 4500
    system_fixed: int = 500
    weekly_max: int = 800
    today_max: int = 2000
    retrieval_max: int = 1000
    retrieval_default_k: int = 3

    # 压缩优先级 (数字越小越先压缩)
    compression_priority: dict = field(default_factory=lambda: {
        "retrieval": 1,
        "weekly": 2,
        "today": 3
    })

    # Today 压缩后保留的字段
    today_keep_fields: List[str] = field(default_factory=lambda: [
        "trend", "confidence", "growth_stage", "abnormalities"
    ])

    @classmethod
    def from_yaml(cls, config: dict) -> "BudgetConfig":
        """从 YAML 配置创建"""
        cb = config.get("context_budget", {})
        comp = config.get("compression", {})

        return cls(
            total_max=cb.get("total_max", 4500),
            system_fixed=cb.get("system_fixed", 500),
            weekly_max=cb.get("weekly_max", 800),
            today_max=cb.get("today_max", 2000),
            retrieval_max=cb.get("retrieval_max", 1000),
            retrieval_default_k=cb.get("retrieval_default_k", 3),
            compression_priority=comp.get("priority", {
                "retrieval": 1, "weekly": 2, "today": 3
            }),
            today_keep_fields=comp.get("today_keep_fields", [
                "trend", "confidence", "growth_stage", "abnormalities"
            ])
        )


class BudgetController:
    """Rule-M1 上下文预算控制器

    预算分配:
    - System: ~500 tokens (固定)
    - Weekly: ≤800 tokens (prompt_block)
    - Today: ~2000 tokens (环境+YOLO+对比结论)
    - Retrieval: ~1000 tokens (TopK=3-5)
    - 总计: ≤4500 tokens

    压缩优先级 (数字越小越先压缩):
    1. Retrieval: TopK 5→3→1→删除
    2. Weekly: 只保留 key_insights
    3. Today: 删除 evidence 详情，保留核心字段
    """

    def __init__(
        self,
        config: Optional[BudgetConfig] = None,
        token_counter: Optional[TokenCounter] = None
    ):
        """
        初始化控制器

        Args:
            config: 预算配置
            token_counter: Token 计数器
        """
        self.config = config or BudgetConfig()
        self.token_counter = token_counter or TokenCounter()

    def apply(self, context: WorkingContext) -> WorkingContext:
        """
        应用预算控制

        Args:
            context: 工作上下文

        Returns:
            压缩后的工作上下文
        """
        total = self._count_tokens(context)

        if total <= self.config.total_max:
            context.total_tokens = total
            return context

        # 按优先级压缩
        priority_order = sorted(
            self.config.compression_priority.keys(),
            key=lambda k: self.config.compression_priority[k]
        )

        for component in priority_order:
            if component == "retrieval":
                context = self._compress_retrieval(context)
            elif component == "weekly":
                context = self._compress_weekly(context)
            elif component == "today":
                context = self._compress_today(context)

            total = self._count_tokens(context)
            if total <= self.config.total_max:
                break

        context.total_tokens = total
        return context

    def _count_tokens(self, context: WorkingContext) -> int:
        """计算上下文总 token 数"""
        total = 0

        # System prompt
        total += self.token_counter.count(context.system_prompt)

        # Weekly context
        if context.weekly_context:
            total += self.token_counter.count(context.weekly_context)

        # Today input
        if context.today_input:
            total += self.token_counter.count_dict(context.today_input)

        # Retrieval results
        for snippet in context.retrieval_results:
            total += self.token_counter.count(snippet)

        # 消息格式开销
        total += 50  # 估算的格式开销

        return total

    def _compress_retrieval(self, context: WorkingContext) -> WorkingContext:
        """压缩检索结果: 5→3→1→删除"""
        results = context.retrieval_results

        if len(results) > 3:
            context.retrieval_results = results[:3]
        elif len(results) > 1:
            context.retrieval_results = results[:1]
        else:
            context.retrieval_results = []

        return context

    def _compress_weekly(self, context: WorkingContext) -> WorkingContext:
        """压缩周摘要: 只保留第一条 key_insight"""
        if not context.weekly_context:
            return context

        # 尝试提取第一条 insight
        lines = context.weekly_context.split('\n')
        compressed_lines = []

        for line in lines:
            if line.startswith('##') or line.startswith('# '):
                compressed_lines.append(line)
            elif line.startswith('- '):
                compressed_lines.append(line)
                break  # 只保留第一条

        if compressed_lines:
            context.weekly_context = '\n'.join(compressed_lines)
        else:
            context.weekly_context = None

        return context

    def _compress_today(self, context: WorkingContext) -> WorkingContext:
        """压缩今日输入: 只保留核心字段"""
        if not context.today_input:
            return context

        keep_fields = self.config.today_keep_fields
        compressed = {}

        for key, value in context.today_input.items():
            if key in keep_fields:
                compressed[key] = value
            elif isinstance(value, dict):
                # 对嵌套字典也进行压缩
                nested_compressed = {
                    k: v for k, v in value.items()
                    if k in keep_fields
                }
                if nested_compressed:
                    compressed[key] = nested_compressed

        context.today_input = compressed
        return context

    def check_budget(self, context: WorkingContext) -> dict:
        """
        检查预算使用情况

        Returns:
            {
                "total": 当前总 token,
                "limit": 预算上限,
                "over_budget": 是否超预算,
                "breakdown": 各部分 token 数
            }
        """
        breakdown = {
            "system": self.token_counter.count(context.system_prompt),
            "weekly": self.token_counter.count(context.weekly_context or ""),
            "today": self.token_counter.count_dict(context.today_input) if context.today_input else 0,
            "retrieval": sum(self.token_counter.count(s) for s in context.retrieval_results)
        }

        total = sum(breakdown.values()) + 50  # 格式开销

        return {
            "total": total,
            "limit": self.config.total_max,
            "over_budget": total > self.config.total_max,
            "breakdown": breakdown
        }
