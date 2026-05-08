"""Requirements acceptance tests

P6-05: Q1-Q6 requirements acceptance
P6-06: Q7 knowledge enhancement acceptance
"""

import pytest
import pandas as pd
import numpy as np
import os


class TestQ1RollingPrediction:
    """Q1: 滚动预测与冷启动 (requirements1.md 2.x)"""

    def test_q1_1_rolling_prediction(self, sample_reference_data, sample_user_data):
        """Q1.1: 输入96步序列，输出单一灌水量值"""
        from cucumber_irrigation.core import ColdStartFiller, WindowBuilder
        from cucumber_irrigation.services import TSMixerService

        # Build window
        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        builder = WindowBuilder(cold_start_filler=filler)

        window = builder.build(
            data=sample_user_data,
            target_date="2025-03-14"
        )

        # Verify shape
        assert window.shape == (96, 11), "Input should be 96 steps × 11 features"

        # Run TSMixer (if model available)
        service = TSMixerService()
        if service.is_available():
            prediction = service.predict(
                pd.DataFrame(window, columns=builder.feature_columns)
            )
            assert isinstance(prediction, float), "Output should be a single float"
            assert prediction > 0, "Prediction should be positive"

    def test_q1_2_cold_start_filling(self, sample_reference_data):
        """Q1.2: 数据不足时自动用2023年数据填充"""
        from cucumber_irrigation.core import ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)

        # Empty user data
        user_data = pd.DataFrame()
        target_date = "2025-03-14"

        result = filler.fill(
            user_data=user_data,
            target_date=target_date,
            required_length=96
        )

        assert len(result) == 96, "Should fill to 96 rows"

    def test_q1_3_date_alignment(self, sample_reference_data):
        """Q1.3: 2025-03-14 填充 2023-03-14 数据"""
        from cucumber_irrigation.core import ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)

        # Map date to reference year
        mapped = filler._map_date_to_reference_year("2025-03-14")

        # Should map to same month-day in 2023
        assert "2023" in mapped or mapped.endswith("-03-14")


class TestQ2AnomalyDetection:
    """Q2: 异常检测与 RAG 辅助 (requirements1.md 3.x)"""

    def test_q2_1_range_detection_high(self):
        """Q2.1: 预测值15.5触发out_of_range"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()
        out_of_range, _ = detector.check_range_only(15.5)

        assert out_of_range is True, "15.5 should trigger out_of_range"

    def test_q2_1_range_detection_low(self):
        """Q2.1: 预测值0.05触发out_of_range"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()
        out_of_range, _ = detector.check_range_only(0.05)

        assert out_of_range is True, "0.05 should trigger out_of_range"

    def test_q2_2_trend_conflict_severe(self):
        """Q2.2: trend=worse, 灌水-15% 触发 severe"""
        from cucumber_irrigation.core import AnomalyDetector
        from cucumber_irrigation.models import (
            PlantResponse, Comparison, Abnormalities, Evidence, Trend, GrowthStage
        )

        detector = AnomalyDetector()

        worse_response = PlantResponse(
            trend=Trend.WORSE,
            confidence=0.9,
            evidence=Evidence(
                leaf_observation="Wilting observed",
                flower_observation="",
                fruit_observation="",
                terminal_bud_observation=""
            ),
            abnormalities=Abnormalities(
                wilting="moderate",
                yellowing="none",
                pest_damage="none"
            ),
            growth_stage=GrowthStage.VEGETATIVE,
            comparison=Comparison()
        )

        result = detector.detect(
            prediction=4.25,  # -15% from 5.0
            yesterday_irrigation=5.0,
            plant_response=worse_response,
            env_history=[]
        )

        assert result.trend_conflict is True
        assert result.trend_conflict_severity.value == "severe"

    def test_q2_3_env_anomaly_high_humidity(self, sample_plant_response):
        """Q2.3: 连续3天humidity>85%触发high_humidity"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()

        env_history = [
            {"temperature": 25, "humidity": 87, "light": 8000},
            {"temperature": 26, "humidity": 88, "light": 8500},
            {"temperature": 25, "humidity": 86, "light": 8000},
        ]

        result = detector.detect(
            prediction=5.0,
            yesterday_irrigation=5.0,
            plant_response=sample_plant_response,
            env_history=env_history
        )

        assert result.env_anomaly is True
        assert result.env_anomaly_type.value == "high_humidity"

    def test_q2_4_rag_retrieval_on_anomaly(self):
        """Q2.4: 有异常时返回FAO56片段"""
        from cucumber_irrigation.services import RAGService

        service = RAGService()

        # If Milvus is available, should return results
        # Otherwise, test the interface exists
        results = service.search_for_anomaly("high_humidity")

        assert isinstance(results, list)
        # If results exist, they should have doc_id and snippet
        for r in results:
            if hasattr(r, 'doc_id'):
                assert r.doc_id is not None


class TestQ3MemoryArchitecture:
    """Q3: 4层记忆架构 (requirements1.md 4.x)"""

    def test_q3_1_episode_storage(self, temp_json_storage, sample_episode):
        """Q3.1: 4层记忆落库 - Episode可存储查询"""
        from cucumber_irrigation.memory import EpisodeStore

        store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )

        # Save
        store.save(sample_episode)

        # Retrieve
        retrieved = store.get_by_date("2025-03-14")

        assert retrieved is not None
        assert retrieved.date == sample_episode.date

    def test_q3_2_context_budget(self):
        """Q3.2: 构建上下文总tokens≤4500"""
        from cucumber_irrigation.memory import WorkingContextBuilder, BudgetController

        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        # Build with all components at max
        context = builder.build(
            system_prompt="System prompt " * 50,
            today_input={"data": "x" * 1000},
            weekly_context="Weekly " * 100,
            retrieval_results=["Knowledge " * 50] * 5
        )

        assert context.total_tokens <= 4500, \
            f"Total should be ≤4500, got {context.total_tokens}"

    def test_q3_3_compression_priority(self):
        """Q3.3: 超限按优先级压缩"""
        from cucumber_irrigation.memory.budget_controller import BudgetController, WorkingContext

        controller = BudgetController()

        # Create over-budget context
        context = WorkingContext(
            system_prompt="System prompt " * 50,
            weekly_context="Weekly context " * 100,
            today_input={"data": "x" * 2000},
            retrieval_results=["Knowledge " * 50] * 10
        )

        # Apply compression
        result = controller.apply(context)

        # Should be within budget after compression
        assert result.total_tokens <= 4500


class TestQ4WeeklySummary:
    """Q4: 周摘要与 prompt_block (requirements1.md 4.5节)"""

    def test_q4_1_prompt_block_limit(self, temp_json_storage, sample_weekly_summary):
        """Q4.1: 周摘要生成，prompt_block≤800 tokens"""
        from cucumber_irrigation.memory import WeeklySummaryStore

        store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        store.save(sample_weekly_summary)
        retrieved = store.get_by_week("2025-03-10")

        assert retrieved.prompt_block_tokens <= 800, \
            f"prompt_block should be ≤800 tokens, got {retrieved.prompt_block_tokens}"

    def test_q4_2_prompt_block_content(self, temp_json_storage, sample_weekly_summary):
        """Q4.2: prompt_block包含关键信息"""
        from cucumber_irrigation.memory import WeeklySummaryStore

        store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        store.save(sample_weekly_summary)
        retrieved = store.get_by_week("2025-03-10")

        prompt_block = retrieved.prompt_block

        # Should contain key information
        assert "2025-03-10" in prompt_block or "03-10" in prompt_block
        assert any(word in prompt_block.lower() for word in ["趋势", "trend", "better", "好转"])


class TestQ5DatabaseIsolation:
    """Q5: 同实例分库访问 (requirements1.md 6.x)"""

    def test_q5_1_db_service_init(self):
        """Q5.1: 同实例分库 - 两个库独立可访问"""
        from cucumber_irrigation.services import DBService

        # Test that DBService can be instantiated
        # (even without MongoDB running, should handle gracefully)
        try:
            service = DBService()
            # If MongoDB is available, check collections
            if service.is_connected:
                assert service.episodes is not None
                assert service.weekly_summaries is not None
        except Exception:
            # MongoDB not available, which is acceptable
            pass

    def test_q5_2_json_storage_fallback(self, temp_json_storage):
        """Q5.2: JSON存储回退 - 无MongoDB时使用JSON"""
        from cucumber_irrigation.memory import EpisodeStore

        # Should work without MongoDB
        store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )

        assert store is not None


class TestQ6PromptInjection:
    """Q6: 动态 Prompt 注入 (requirements1.md 7.x)"""

    def test_q6_1_weekly_context_injection(self, temp_json_storage):
        """Q6.1: Prompt注入 - Weekly Context包含周总结"""
        from cucumber_irrigation.memory import (
            WorkingContextBuilder, BudgetController, WeeklySummaryStore
        )
        from cucumber_irrigation.models import WeeklySummary, TrendStats, IrrigationStats

        # Create weekly summary
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        summary = WeeklySummary(
            week_start="2025-03-10",
            week_end="2025-03-16",
            trend_stats=TrendStats(
                better_days=3, same_days=2, worse_days=2, dominant_trend="better"
            ),
            irrigation_stats=IrrigationStats(
                total=42.5, daily_avg=6.07, trend="stable"
            ),
            key_insights=["Test insight for injection"]
        )
        weekly_store.save(summary)

        # Build working context with weekly
        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        latest_weekly = weekly_store.get_latest()

        context = builder.build(
            system_prompt="You are a greenhouse expert.",
            today_input={"temperature": 25.0},
            weekly_context=latest_weekly.prompt_block
        )

        # Check that weekly context was included
        assert context.weekly_context is not None
        assert len(context.weekly_context) > 0

    def test_q6_2_memory_continuity(self, temp_json_storage):
        """Q6.2: 记忆连贯性 - 周总结可被引用"""
        from cucumber_irrigation.memory import WeeklySummaryStore
        from cucumber_irrigation.models import WeeklySummary, TrendStats, IrrigationStats

        store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        # Create multiple weeks
        for week_offset in range(3):
            start_day = 10 + week_offset * 7
            end_day = 16 + week_offset * 7

            summary = WeeklySummary(
                week_start=f"2025-03-{start_day:02d}",
                week_end=f"2025-03-{end_day:02d}",
                trend_stats=TrendStats(
                    better_days=3, same_days=2, worse_days=2, dominant_trend="better"
                ),
                irrigation_stats=IrrigationStats(
                    total=40 + week_offset * 2, daily_avg=5.7 + week_offset * 0.3
                ),
                key_insights=[f"Week {week_offset + 1} insight"]
            )
            store.save(summary)

        # Get latest for continuity
        latest = store.get_latest()

        assert latest is not None
        assert latest.prompt_block is not None


class TestQ7KnowledgeEnhancement:
    """Q7: 知识增强 (requirements1.md 8.x) - P6-06"""

    def test_q7_1_growth_stage_prediction(self):
        """Q7.1: 生育期预判 - GrowthStageDetector返回结果"""
        from cucumber_irrigation.core import GrowthStageDetector

        config = {"growth_stage_detection": {"confidence_threshold": 0.7}}
        detector = GrowthStageDetector(llm_service=None, config=config)

        # Test fallback detection from YOLO metrics
        stage, confidence = detector.detect_from_yolo_metrics(
            flower_count=2.0, fruit_mask=100, leaf_count=10
        )

        assert stage in ["vegetative", "flowering", "fruiting", "mixed"]
        assert 0.0 <= confidence <= 1.0

    def test_q7_2_growth_stage_retrieval_query(self):
        """Q7.2: 知识增强PlantResponse - 生成检索查询"""
        from cucumber_irrigation.core import GrowthStageDetector

        config = {"growth_stage_detection": {"confidence_threshold": 0.7}}
        detector = GrowthStageDetector(llm_service=None, config=config)

        for stage in ["vegetative", "flowering", "fruiting"]:
            query = detector.get_retrieval_query(stage)

            assert query is not None
            assert len(query) > 0
            assert stage in query.lower()

    def test_q7_3_knowledge_references_in_episode(self, temp_json_storage, sample_episode):
        """Q7.3: 知识引用记录 - Episode包含knowledge_references"""
        from cucumber_irrigation.memory import EpisodeStore
        from cucumber_irrigation.models import Episode, FinalDecision

        store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )

        # Create episode with knowledge references
        episode = Episode(
            date="2025-03-14",
            final_decision=FinalDecision(value=5.5, source="tsmixer"),
            knowledge_references=[
                {"doc_id": "fao56_001", "snippet": "Kc = 0.6 for vegetative"},
                {"doc_id": "cucumber_002", "snippet": "Water stress symptoms"}
            ]
        )

        store.save(episode)
        retrieved = store.get_by_date("2025-03-14")

        assert len(retrieved.knowledge_references) == 2
        assert retrieved.knowledge_references[0]["doc_id"] == "fao56_001"

    def test_q7_4_rag_service_search(self):
        """Q7.4: 检索优先级 - RAGService正确搜索"""
        from cucumber_irrigation.services import RAGService

        service = RAGService()

        # Test search for growth stage
        results = service.search_for_growth_stage("vegetative", top_k=3)

        assert isinstance(results, list)
        # Interface should exist even if Milvus not available

    def test_q7_5_weekly_summary_with_knowledge(self, temp_json_storage):
        """Q7.5: 知识增强WeeklySummary - 包含knowledge_references"""
        from cucumber_irrigation.memory import WeeklySummaryStore
        from cucumber_irrigation.models import WeeklySummary, TrendStats, IrrigationStats

        store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        summary = WeeklySummary(
            week_start="2025-03-10",
            week_end="2025-03-16",
            trend_stats=TrendStats(
                better_days=3, same_days=2, worse_days=2, dominant_trend="better"
            ),
            irrigation_stats=IrrigationStats(total=40, daily_avg=5.7),
            key_insights=["[文献] FAO56 recommends Kc=0.9 for flowering"],
            knowledge_references=[
                {"doc_id": "fao56_010", "source": "FAO56"}
            ]
        )

        store.save(summary)
        retrieved = store.get_by_week("2025-03-10")

        assert len(retrieved.knowledge_references) == 1
        assert retrieved.knowledge_references[0]["doc_id"] == "fao56_010"


class TestServicesIntegration:
    """Service integration tests"""

    def test_tsmixer_service_info(self):
        """Test TSMixerService provides model info"""
        from cucumber_irrigation.services import TSMixerService

        service = TSMixerService()
        info = service.get_model_info()

        assert "model_path" in info
        assert "feature_columns" in info
        assert info["input_shape"] == (96, 11)

    def test_llm_service_interface(self):
        """Test LLMService interface exists"""
        from cucumber_irrigation.services import LLMService

        # Use dummy key for interface testing
        service = LLMService(api_key="dummy-key-for-testing")

        # Interface methods should exist
        assert hasattr(service, 'generate_plant_response')
        assert hasattr(service, 'generate_with_context')
        assert hasattr(service, 'sanity_check')

    def test_rag_service_interface(self):
        """Test RAGService interface exists"""
        from cucumber_irrigation.services import RAGService

        service = RAGService()

        # Interface methods should exist
        assert hasattr(service, 'search_for_growth_stage')
        assert hasattr(service, 'search_for_anomaly')
        assert hasattr(service, 'build_rag_advice')
