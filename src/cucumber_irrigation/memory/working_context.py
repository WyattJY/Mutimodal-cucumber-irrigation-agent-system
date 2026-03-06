from __future__ import annotations
"""L1 工作上下文构建器

组装单次 LLM 调用的完整输入上下文
参考: task1.md P3-03, requirements1.md 4.3节
"""

from typing import Optional, List

from .budget_controller import WorkingContext, BudgetController


class WorkingContextBuilder:
    """L1 工作上下文构建器

    组装单次 LLM 调用的完整输入上下文:
    - System Prompt (~500 tokens)
    - Weekly Context (≤800 tokens, from L3.prompt_block)
    - Today Input (~2000 tokens)
    - Retrieval (~1000 tokens, TopK=3-5)
    """

    def __init__(
        self,
        budget_controller: BudgetController,
        weekly_store=None,  # WeeklySummaryStore
        knowledge_retriever=None  # KnowledgeRetriever
    ):
        """
        初始化构建器

        Args:
            budget_controller: 预算控制器
            weekly_store: 周摘要存储 (可选)
            knowledge_retriever: 知识检索器 (可选)
        """
        self.budget = budget_controller
        self.weekly_store = weekly_store
        self.retriever = knowledge_retriever

    def build(
        self,
        system_prompt: str,
        today_input: dict,
        retrieval_query: Optional[str] = None,
        weekly_context: Optional[str] = None,
        retrieval_results: Optional[List[str]] = None
    ) -> WorkingContext:
        """
        构建工作上下文

        Args:
            system_prompt: System Prompt
            today_input: 今日输入数据
            retrieval_query: RAG 检索查询 (可选)
            weekly_context: 周摘要 (可选，如不提供则从 store 获取)
            retrieval_results: 检索结果 (可选，如不提供则执行检索)

        Returns:
            构建并压缩后的 WorkingContext
        """
        # 1. 获取周摘要
        if weekly_context is None and self.weekly_store:
            latest_summary = self.weekly_store.get_latest()
            if latest_summary:
                weekly_context = latest_summary.prompt_block

        # 2. 执行知识检索
        if retrieval_results is None and retrieval_query and self.retriever:
            retrieval_results = self.retriever.search(
                query=retrieval_query,
                top_k=self.budget.config.retrieval_default_k
            )
            # 提取 snippet
            retrieval_results = [r.snippet for r in retrieval_results]

        # 3. 构建上下文
        context = WorkingContext(
            system_prompt=system_prompt,
            weekly_context=weekly_context,
            today_input=today_input,
            retrieval_results=retrieval_results or [],
            total_tokens=0
        )

        # 4. 应用预算控制
        context = self.budget.apply(context)

        return context

    def build_simple(
        self,
        system_prompt: str,
        today_input: dict
    ) -> WorkingContext:
        """
        简单构建 (不包含周摘要和检索)

        Args:
            system_prompt: System Prompt
            today_input: 今日输入数据

        Returns:
            WorkingContext
        """
        return self.build(
            system_prompt=system_prompt,
            today_input=today_input,
            retrieval_query=None,
            weekly_context=None,
            retrieval_results=None
        )

    def build_with_retrieval(
        self,
        system_prompt: str,
        today_input: dict,
        retrieval_query: str
    ) -> WorkingContext:
        """
        带检索的构建

        Args:
            system_prompt: System Prompt
            today_input: 今日输入数据
            retrieval_query: 检索查询

        Returns:
            WorkingContext
        """
        return self.build(
            system_prompt=system_prompt,
            today_input=today_input,
            retrieval_query=retrieval_query
        )

    def build_full(
        self,
        system_prompt: str,
        today_input: dict,
        retrieval_query: str
    ) -> WorkingContext:
        """
        完整构建 (包含周摘要和检索)

        Args:
            system_prompt: System Prompt
            today_input: 今日输入数据
            retrieval_query: 检索查询

        Returns:
            WorkingContext
        """
        return self.build(
            system_prompt=system_prompt,
            today_input=today_input,
            retrieval_query=retrieval_query
        )
