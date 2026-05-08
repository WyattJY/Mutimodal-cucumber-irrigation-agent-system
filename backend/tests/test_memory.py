# T2.8 Phase 2 Integration Tests
"""
Phase 2 集成测试 - 记忆系统
"""
import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.schemas import (
    WeeklySummaryResult,
    WeeklyStatistics,
    RAGReference,
    KnowledgeQueryRequest,
    RAGAnswer,
)


class TestWeeklySummaryResult:
    """测试周报结果模型"""

    def test_weekly_summary_result(self):
        """测试 WeeklySummaryResult 模型"""
        result = WeeklySummaryResult(
            week_start="2024-05-27",
            week_end="2024-06-02",
            patterns=["高温天气灌水量增加", "果实快速膨大期"],
            risk_triggers=["6月1日出现轻微萎蔫"],
            overrides=[{"date": "2024-05-30", "reason": "手动调整"}],
            insights=["本周整体状态良好", "建议增加通风"],
            statistics=WeeklyStatistics(
                total_irrigation=35.5,
                avg_irrigation=5.07,
                max_irrigation=6.5,
                min_irrigation=3.5,
                better_days=4,
                same_days=2,
                worse_days=1
            ),
            prompt_block="[周报摘要] 本周灌水总量35.5L..."
        )
        assert result.week_start == "2024-05-27"
        assert result.week_end == "2024-06-02"
        assert len(result.patterns) == 2
        assert result.statistics.avg_irrigation == 5.07

    def test_weekly_statistics(self):
        """测试 WeeklyStatistics 模型"""
        stats = WeeklyStatistics(
            total_irrigation=42.0,
            avg_irrigation=6.0,
            max_irrigation=8.0,
            min_irrigation=4.0,
            better_days=3,
            same_days=2,
            worse_days=2
        )
        assert stats.total_irrigation == 42.0
        assert stats.better_days + stats.same_days + stats.worse_days == 7


class TestRAGModels:
    """测试 RAG 相关模型"""

    def test_rag_reference(self):
        """测试 RAGReference 模型"""
        ref = RAGReference(
            doc_id="cucumber_guide_001",
            title="黄瓜灌溉指南",
            snippet="黄瓜在开花期需要充足水分...",
            relevance=0.92
        )
        assert ref.doc_id == "cucumber_guide_001"
        assert ref.relevance == 0.92

    def test_knowledge_query_request(self):
        """测试 KnowledgeQueryRequest 模型"""
        request = KnowledgeQueryRequest(
            question="黄瓜开花期需要多少水?",
            top_k=5,
            growth_stage="flowering"
        )
        assert request.question == "黄瓜开花期需要多少水?"
        assert request.top_k == 5
        assert request.growth_stage == "flowering"

    def test_knowledge_query_request_defaults(self):
        """测试 KnowledgeQueryRequest 默认值"""
        request = KnowledgeQueryRequest(question="测试问题")
        assert request.top_k == 5
        assert request.growth_stage is None

    def test_rag_answer(self):
        """测试 RAGAnswer 模型"""
        answer = RAGAnswer(
            question="如何判断黄瓜缺水?",
            answer="黄瓜缺水的主要表现包括：叶片萎蔫、叶色暗绿...",
            references=[
                RAGReference(
                    doc_id="water_stress_001",
                    title="水分胁迫识别",
                    snippet="缺水时叶片会出现萎蔫...",
                    relevance=0.88
                )
            ],
            model="gpt-4"
        )
        assert answer.question == "如何判断黄瓜缺水?"
        assert len(answer.references) == 1
        assert answer.model == "gpt-4"


class TestRAGService:
    """测试 RAG 服务"""

    def test_rag_service_import(self):
        """测试 RAGService 可正确导入"""
        from app.services.rag_service import RAGService, rag_service
        assert RAGService is not None
        assert rag_service is not None

    @pytest.mark.asyncio
    async def test_rag_search(self):
        """测试 RAG 搜索"""
        from app.services.rag_service import RAGService

        service = RAGService()
        results = await service.search("黄瓜灌溉", top_k=3)

        # 应该返回列表
        assert isinstance(results, list)

        # 每个结果应该有必要字段
        for result in results:
            assert hasattr(result, 'doc_id')
            assert hasattr(result, 'snippet')
            assert hasattr(result, 'relevance')

    @pytest.mark.asyncio
    async def test_rag_search_by_growth_stage(self):
        """测试按生育期搜索"""
        from app.services.rag_service import RAGService

        service = RAGService()
        results = await service.search_by_growth_stage("flowering", top_k=3)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_rag_search_by_anomaly(self):
        """测试按异常类型搜索"""
        from app.services.rag_service import RAGService

        service = RAGService()
        results = await service.search_by_anomaly("wilting", "mild")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_rag_build_augmented_answer(self):
        """测试构建增强回答"""
        from app.services.rag_service import RAGService

        service = RAGService()
        result = await service.build_augmented_answer(
            question="黄瓜需要多少水?",
            context=None,
            llm_service=None
        )

        assert "answer" in result
        assert "references" in result
        assert isinstance(result["references"], list)


class TestMemoryService:
    """测试 Memory 服务"""

    def test_memory_service_import(self):
        """测试 MemoryService 可正确导入"""
        from app.services.memory_service import MemoryService, memory_service
        assert MemoryService is not None
        assert memory_service is not None

    @pytest.mark.asyncio
    async def test_get_recent_episodes(self):
        """测试获取最近 Episodes"""
        from app.services.memory_service import MemoryService

        service = MemoryService()
        episodes = await service.get_recent_episodes(days=7)

        assert isinstance(episodes, list)

    @pytest.mark.asyncio
    async def test_build_working_context(self):
        """测试构建工作上下文"""
        from app.services.memory_service import MemoryService

        service = MemoryService()
        context = service.build_working_context(
            system_prompt="你是灌溉专家",
            today_input={"date": "2024-05-30"},
            weekly_context="本周状态良好",
            rag_results=["参考资料1"]
        )

        assert isinstance(context, dict)
        assert "system_prompt" in context
        assert "today_input" in context


class TestWeeklySummaryService:
    """测试 Weekly Summary 服务"""

    def test_weekly_service_import(self):
        """测试 WeeklySummaryService 可正确导入"""
        from app.services.weekly_summary_service import WeeklySummaryService, weekly_summary_service
        assert WeeklySummaryService is not None
        assert weekly_summary_service is not None

    @pytest.mark.asyncio
    async def test_generate_weekly_summary(self):
        """测试生成周报"""
        from app.services.weekly_summary_service import WeeklySummaryService

        service = WeeklySummaryService()
        result = await service.generate_weekly_summary(
            week_start="2024-05-27",
            week_end="2024-06-02"
        )

        assert result is not None
        assert hasattr(result, 'week_start')
        assert hasattr(result, 'week_end')
        assert hasattr(result, 'statistics')
        assert hasattr(result, 'prompt_block')


class TestWorkingContextInjection:
    """测试 Working Context 注入"""

    def test_context_structure(self):
        """测试上下文结构"""
        from app.services.memory_service import MemoryService

        service = MemoryService()
        context = service.build_working_context(
            system_prompt="系统提示",
            today_input={"env": {"temp": 25}},
            weekly_context="周摘要",
            rag_results=["RAG结果"]
        )

        # 验证结构
        assert "system_prompt" in context
        assert "today_input" in context
        assert "weekly_context" in context
        assert "rag_results" in context

    def test_context_with_empty_weekly(self):
        """测试无周摘要的上下文"""
        from app.services.memory_service import MemoryService

        service = MemoryService()
        context = service.build_working_context(
            system_prompt="系统提示",
            today_input={},
            weekly_context=None,
            rag_results=[]
        )

        assert context["weekly_context"] is None
        assert context["rag_results"] == []


class TestRAGIntegration:
    """测试 RAG 与预测流程集成"""

    @pytest.mark.asyncio
    async def test_rag_in_prediction_context(self):
        """测试 RAG 在预测上下文中的使用"""
        from app.services.rag_service import RAGService

        service = RAGService()

        # 模拟预测流程中的 RAG 调用
        growth_stage = "flowering"
        results = await service.search_by_growth_stage(growth_stage, top_k=3)

        # 构建 RAG 建议
        advice_parts = []
        for result in results:
            advice_parts.append(result.snippet)

        rag_advice = "\n".join(advice_parts)
        assert isinstance(rag_advice, str)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
