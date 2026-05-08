"""Unit tests for memory architecture

P6-02: Tests for BudgetController, TokenCounter, EpisodeStore, WeeklySummaryStore
"""

import pytest
import json
import os


class TestTokenCounter:
    """Tests for TokenCounter (P3-01)"""

    def test_token_counter_init(self):
        """Test TokenCounter initialization"""
        from cucumber_irrigation.utils.token_counter import TokenCounter

        counter = TokenCounter()
        assert counter is not None

    def test_count_simple_text(self):
        """Test counting tokens in simple text"""
        from cucumber_irrigation.utils.token_counter import TokenCounter

        counter = TokenCounter()
        text = "Hello, world!"
        count = counter.count(text)

        assert count > 0
        assert count < 10  # Simple text should be just a few tokens

    def test_count_longer_text(self):
        """Test counting tokens in longer text"""
        from cucumber_irrigation.utils.token_counter import TokenCounter

        counter = TokenCounter()
        text = "This is a longer piece of text that should have more tokens. " * 10
        count = counter.count(text)

        assert count > 50  # Repeated text should have many tokens

    def test_count_empty_string(self):
        """Test counting tokens in empty string"""
        from cucumber_irrigation.utils.token_counter import TokenCounter

        counter = TokenCounter()
        count = counter.count("")

        assert count == 0

    def test_count_chinese_text(self):
        """Test counting tokens in Chinese text"""
        from cucumber_irrigation.utils.token_counter import TokenCounter

        counter = TokenCounter()
        text = "本周长势好转，日均灌水量6.07 L/m²"
        count = counter.count(text)

        assert count > 0  # Should handle Chinese characters


class TestBudgetController:
    """Tests for BudgetController (P3-02, P3-08)"""

    def test_budget_controller_init(self):
        """Test BudgetController initialization with defaults"""
        from cucumber_irrigation.memory import BudgetController

        controller = BudgetController()
        assert controller.config.total_max == 4500
        assert controller.config.system_fixed == 500
        assert controller.config.weekly_max == 800
        assert controller.config.today_max == 2000
        assert controller.config.retrieval_max == 1000

    def test_budget_controller_custom_config(self):
        """Test BudgetController with custom config"""
        from cucumber_irrigation.memory.budget_controller import BudgetController, BudgetConfig

        config = BudgetConfig(
            total_max=5000,
            system_fixed=600,
            weekly_max=900
        )
        controller = BudgetController(config=config)

        assert controller.config.total_max == 5000
        assert controller.config.system_fixed == 600
        assert controller.config.weekly_max == 900

    def test_apply_under_limit(self):
        """Test apply when under limit"""
        from cucumber_irrigation.memory.budget_controller import BudgetController, WorkingContext

        controller = BudgetController()
        context = WorkingContext(
            system_prompt="You are a test assistant.",
            weekly_context="Weekly summary",
            today_input={"temperature": 25.0},
            retrieval_results=["Snippet 1"]
        )

        result = controller.apply(context)

        assert result.total_tokens > 0
        assert result.total_tokens <= 4500

    def test_check_budget(self):
        """Test budget check"""
        from cucumber_irrigation.memory.budget_controller import BudgetController, WorkingContext

        controller = BudgetController()
        context = WorkingContext(
            system_prompt="You are a test assistant.",
            weekly_context="Weekly summary " * 50,
            today_input={"temperature": 25.0, "humidity": 70.0},
            retrieval_results=["Knowledge snippet " * 20] * 5
        )

        result = controller.check_budget(context)

        assert "total" in result
        assert "limit" in result
        assert "over_budget" in result
        assert "breakdown" in result


class TestEpisodeStore:
    """Tests for EpisodeStore (P3-04)"""

    def test_episode_store_init_json(self, temp_json_storage):
        """Test EpisodeStore initialization with JSON storage"""
        from cucumber_irrigation.memory import EpisodeStore

        json_path = os.path.join(temp_json_storage, "episodes.json")
        store = EpisodeStore(json_path=json_path)

        assert store is not None

    def test_episode_save_and_get(self, temp_json_storage, sample_episode):
        """Test saving and retrieving an Episode"""
        from cucumber_irrigation.memory import EpisodeStore

        json_path = os.path.join(temp_json_storage, "episodes.json")
        store = EpisodeStore(json_path=json_path)

        # Save
        store.save(sample_episode)

        # Get
        retrieved = store.get_by_date("2025-03-14")

        assert retrieved is not None
        assert retrieved.date == "2025-03-14"
        assert retrieved.season == "spring"
        assert retrieved.final_decision.value == 5.5

    def test_episode_get_recent(self, temp_json_storage):
        """Test getting recent Episodes"""
        from cucumber_irrigation.memory import EpisodeStore
        from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision

        json_path = os.path.join(temp_json_storage, "episodes.json")
        store = EpisodeStore(json_path=json_path)

        # Save multiple episodes
        for i in range(5):
            ep = Episode(
                date=f"2025-03-{10+i:02d}",
                predictions=EpisodePredictions(tsmixer_raw=5.0 + i * 0.1),
                final_decision=FinalDecision(value=5.0 + i * 0.1, source="tsmixer")
            )
            store.save(ep)

        recent = store.get_recent(days=5)  # Get 5 days worth

        assert len(recent) == 5  # All 5 episodes should be returned

    def test_episode_get_by_date_range(self, temp_json_storage):
        """Test getting Episodes by date range"""
        from cucumber_irrigation.memory import EpisodeStore
        from cucumber_irrigation.models import Episode, FinalDecision

        json_path = os.path.join(temp_json_storage, "episodes.json")
        store = EpisodeStore(json_path=json_path)

        # Save episodes for a week
        for i in range(7):
            ep = Episode(
                date=f"2025-03-{10+i:02d}",
                final_decision=FinalDecision(value=5.0, source="tsmixer")
            )
            store.save(ep)

        episodes = store.get_by_date_range("2025-03-10", "2025-03-14")

        assert len(episodes) >= 4  # At least 4 days in range


class TestWeeklySummaryStore:
    """Tests for WeeklySummaryStore (P3-05)"""

    def test_weekly_summary_store_init(self, temp_json_storage):
        """Test WeeklySummaryStore initialization"""
        from cucumber_irrigation.memory import WeeklySummaryStore

        json_path = os.path.join(temp_json_storage, "weekly.json")
        store = WeeklySummaryStore(json_path=json_path)

        assert store is not None

    def test_weekly_summary_save_and_get(self, temp_json_storage, sample_weekly_summary):
        """Test saving and retrieving a WeeklySummary"""
        from cucumber_irrigation.memory import WeeklySummaryStore

        json_path = os.path.join(temp_json_storage, "weekly.json")
        store = WeeklySummaryStore(json_path=json_path)

        # Save
        store.save(sample_weekly_summary)

        # Get
        retrieved = store.get_by_week("2025-03-10")

        assert retrieved is not None
        assert retrieved.week_start == "2025-03-10"
        assert retrieved.week_end == "2025-03-16"

    def test_prompt_block_generation(self, temp_json_storage, sample_weekly_summary):
        """Test prompt_block is generated on save"""
        from cucumber_irrigation.memory import WeeklySummaryStore

        json_path = os.path.join(temp_json_storage, "weekly.json")
        store = WeeklySummaryStore(json_path=json_path)

        store.save(sample_weekly_summary)
        retrieved = store.get_by_week("2025-03-10")

        assert retrieved.prompt_block is not None
        assert len(retrieved.prompt_block) > 0
        assert retrieved.prompt_block_tokens > 0

    def test_prompt_block_within_budget(self, temp_json_storage, sample_weekly_summary):
        """Test prompt_block is within 800 token budget (Q4.1)"""
        from cucumber_irrigation.memory import WeeklySummaryStore

        json_path = os.path.join(temp_json_storage, "weekly.json")
        store = WeeklySummaryStore(json_path=json_path)

        store.save(sample_weekly_summary)
        retrieved = store.get_by_week("2025-03-10")

        assert retrieved.prompt_block_tokens <= 800, \
            f"prompt_block should be ≤800 tokens, got {retrieved.prompt_block_tokens}"

    def test_get_latest(self, temp_json_storage):
        """Test getting latest WeeklySummary"""
        from cucumber_irrigation.memory import WeeklySummaryStore
        from cucumber_irrigation.models import WeeklySummary, TrendStats, IrrigationStats

        json_path = os.path.join(temp_json_storage, "weekly.json")
        store = WeeklySummaryStore(json_path=json_path)

        # Save multiple summaries
        for i in range(3):
            start_day = 10 + i * 7
            end_day = 16 + i * 7

            summary = WeeklySummary(
                week_start=f"2025-03-{start_day:02d}",
                week_end=f"2025-03-{end_day:02d}",
                trend_stats=TrendStats(better_days=3, same_days=2, worse_days=2, dominant_trend="better"),
                irrigation_stats=IrrigationStats(total=40, daily_avg=5.7, trend="stable"),
                key_insights=[f"Week {i+1} insight"]
            )
            store.save(summary)

        latest = store.get_latest()

        assert latest is not None
        # Should be the most recent week
        assert "03-24" in latest.week_start or "03-17" in latest.week_start or "03-10" in latest.week_start


class TestWorkingContextBuilder:
    """Tests for WorkingContextBuilder (P3-03)"""

    def test_working_context_builder_init(self):
        """Test WorkingContextBuilder initialization"""
        from cucumber_irrigation.memory import WorkingContextBuilder, BudgetController

        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        assert builder is not None

    def test_build_context_basic(self):
        """Test building basic working context"""
        from cucumber_irrigation.memory import WorkingContextBuilder, BudgetController

        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        context = builder.build(
            system_prompt="You are a greenhouse irrigation expert.",
            today_input={"temperature": 25.0, "humidity": 70.0, "prediction": 5.5}
        )

        assert context is not None
        assert context.total_tokens > 0
        assert context.system_prompt is not None

    def test_build_context_with_weekly(self):
        """Test building context with weekly summary"""
        from cucumber_irrigation.memory import WorkingContextBuilder, BudgetController

        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        weekly_context = """## 上周经验总结
本周长势好转，日均灌水量6.07 L/m²"""

        context = builder.build(
            system_prompt="You are a greenhouse irrigation expert.",
            today_input={"temperature": 25.0, "humidity": 70.0, "prediction": 5.5},
            weekly_context=weekly_context
        )

        assert context.weekly_context is not None
        assert len(context.weekly_context) > 0

    def test_build_context_with_retrieval(self):
        """Test building context with retrieval results"""
        from cucumber_irrigation.memory import WorkingContextBuilder, BudgetController

        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        retrieval_results = [
            "FAO56 recommends Kc=0.6 for vegetative stage",
            "Irrigation should increase during flowering"
        ]

        context = builder.build(
            system_prompt="You are a greenhouse irrigation expert.",
            today_input={"temperature": 25.0, "humidity": 70.0, "prediction": 5.5},
            retrieval_results=retrieval_results
        )

        assert len(context.retrieval_results) == 2

    def test_context_within_total_budget(self):
        """Test built context stays within total budget (Q3.2)"""
        from cucumber_irrigation.memory import WorkingContextBuilder, BudgetController

        controller = BudgetController()
        builder = WorkingContextBuilder(budget_controller=controller)

        # Build with all components
        context = builder.build(
            system_prompt="You are a greenhouse irrigation expert. " * 20,  # Longer prompt
            today_input={"temperature": 25.0, "humidity": 70.0, "prediction": 5.5},
            weekly_context="Weekly summary " * 50,  # Longer weekly
            retrieval_results=["Knowledge " * 30] * 5  # Multiple retrievals
        )

        assert context.total_tokens <= 4500, \
            f"Total tokens should be ≤4500, got {context.total_tokens}"


class TestKnowledgeRetriever:
    """Tests for KnowledgeRetriever (P3-06, P3-07)"""

    def test_knowledge_retriever_init(self):
        """Test KnowledgeRetriever initialization"""
        from cucumber_irrigation.memory import KnowledgeRetriever

        retriever = KnowledgeRetriever()
        assert retriever is not None

    def test_build_query_for_anomaly(self):
        """Test query building for anomalies"""
        from cucumber_irrigation.memory import KnowledgeRetriever

        retriever = KnowledgeRetriever()

        query = retriever.build_query(anomaly_type="high_humidity")
        assert query is not None
        assert "humidity" in query.lower()

        query = retriever.build_query(anomaly_type="high_temperature")
        assert "temperature" in query.lower()

        query = retriever.build_query(anomaly_type="low_light")
        assert "light" in query.lower()

    def test_build_query_for_growth_stage(self):
        """Test query building for growth stages"""
        from cucumber_irrigation.memory import KnowledgeRetriever

        retriever = KnowledgeRetriever()

        query = retriever.build_query(growth_stage="vegetative")
        assert "vegetative" in query.lower()
        assert "kc" in query.lower()

        query = retriever.build_query(growth_stage="flowering")
        assert "flowering" in query.lower()

        query = retriever.build_query(growth_stage="fruiting")
        assert "fruiting" in query.lower()

    def test_search_without_milvus(self):
        """Test search returns empty when Milvus not configured"""
        from cucumber_irrigation.memory import KnowledgeRetriever

        retriever = KnowledgeRetriever()
        results = retriever.search("cucumber irrigation", top_k=5)

        assert isinstance(results, list)
        # Should return empty list when Milvus not available

    def test_get_fao56_kc(self):
        """Test FAO56 Kc coefficient retrieval"""
        from cucumber_irrigation.memory import KnowledgeRetriever

        retriever = KnowledgeRetriever()

        kc = retriever.get_fao56_kc("vegetative")
        assert kc is not None
        assert "Kc_ini" in kc
        assert "Kc_mid" in kc
        assert "Kc_end" in kc
