"""Integration tests for pipelines

P6-03: Daily pipeline integration test
P6-04: Weekly pipeline integration test
"""

import pytest
import pandas as pd
import numpy as np
import os


class TestDailyPipelineIntegration:
    """Integration tests for DailyPipeline (P6-03)"""

    def test_daily_pipeline_init(self, temp_json_storage):
        """Test DailyPipeline initialization"""
        from cucumber_irrigation.pipelines import DailyPipeline, DailyPipelineConfig

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage
        )

        pipeline = DailyPipeline(config=config)

        assert pipeline is not None
        assert pipeline.tsmixer_service is not None
        assert pipeline.anomaly_detector is not None
        assert pipeline.episode_store is not None

    def test_daily_pipeline_run_basic(self, temp_json_storage, sample_user_data):
        """Test basic daily pipeline run"""
        from cucumber_irrigation.pipelines import DailyPipeline, DailyPipelineConfig

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage,
            enable_rag=False,  # Disable for basic test
            enable_growth_stage_detection=False
        )

        pipeline = DailyPipeline(config=config)

        result = pipeline.run(
            target_date="2025-03-14",
            env_data={"temperature": 25.0, "humidity": 70.0, "light": 8000.0},
            user_data=sample_user_data
        )

        assert result is not None
        assert result.date == "2025-03-14"
        assert result.irrigation_amount > 0
        assert result.source in ["tsmixer", "override", "sanity_adjusted", "fallback"]

    def test_daily_pipeline_with_override(self, temp_json_storage, sample_user_data):
        """Test daily pipeline with override"""
        from cucumber_irrigation.pipelines import DailyPipeline, DailyPipelineConfig

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage,
            enable_rag=False
        )

        pipeline = DailyPipeline(config=config)

        result = pipeline.run(
            target_date="2025-03-14",
            env_data={"temperature": 25.0, "humidity": 70.0, "light": 8000.0},
            user_data=sample_user_data,
            override_value=7.5,
            override_reason="Manual adjustment for test"
        )

        assert result.irrigation_amount == 7.5
        assert result.source == "override"

    def test_daily_pipeline_stores_episode(self, temp_json_storage, sample_user_data):
        """Test that daily pipeline stores Episode correctly"""
        from cucumber_irrigation.pipelines import DailyPipeline, DailyPipelineConfig

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage,
            enable_rag=False
        )

        pipeline = DailyPipeline(config=config)

        result = pipeline.run(
            target_date="2025-03-14",
            env_data={"temperature": 25.0, "humidity": 70.0, "light": 8000.0},
            user_data=sample_user_data
        )

        # Verify episode was stored
        episode = pipeline.episode_store.get_by_date("2025-03-14")

        assert episode is not None
        assert episode.date == "2025-03-14"
        assert episode.final_decision.value == result.irrigation_amount

    def test_daily_pipeline_anomaly_detection(self, temp_json_storage, sample_user_data):
        """Test daily pipeline with anomaly detection"""
        from cucumber_irrigation.pipelines import DailyPipeline, DailyPipelineConfig

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage,
            enable_rag=False
        )

        pipeline = DailyPipeline(config=config)

        # High humidity environment
        result = pipeline.run(
            target_date="2025-03-14",
            env_data={"temperature": 25.0, "humidity": 90.0, "light": 8000.0},
            user_data=sample_user_data
        )

        assert result is not None
        # Result should contain anomaly info if detected
        if result.anomaly_result:
            assert hasattr(result.anomaly_result, 'env_anomaly')


class TestWeeklyPipelineIntegration:
    """Integration tests for WeeklyPipeline (P6-04)"""

    def test_weekly_pipeline_init(self, temp_json_storage):
        """Test WeeklyPipeline initialization"""
        from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore

        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig()
        )

        assert pipeline is not None

    def test_weekly_pipeline_run(self, temp_json_storage):
        """Test weekly pipeline run with sample episodes"""
        from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore
        from cucumber_irrigation.models import (
            Episode, EpisodePredictions, EpisodeAnomalies, FinalDecision
        )

        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        # Create sample episodes for a week
        for i in range(7):
            ep = Episode(
                date=f"2025-03-{10+i:02d}",
                predictions=EpisodePredictions(
                    tsmixer_raw=5.0 + i * 0.2,
                    growth_stage="vegetative",
                    plant_response={"trend": ["better", "same", "worse"][i % 3]}
                ),
                anomalies=EpisodeAnomalies(
                    out_of_range=False,
                    trend_conflict=i == 3  # One conflict day
                ),
                final_decision=FinalDecision(
                    value=5.0 + i * 0.2,
                    source="tsmixer"
                )
            )
            episode_store.save(ep)

        pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig(
                enable_rag=False,
                enable_llm_insights=False
            )
        )

        result = pipeline.run(week_end_date="2025-03-16")

        assert result is not None
        assert result.week_start == "2025-03-10"
        assert result.week_end == "2025-03-16"
        assert result.summary is not None

    def test_weekly_pipeline_generates_prompt_block(self, temp_json_storage):
        """Test weekly pipeline generates valid prompt_block"""
        from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore
        from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision

        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        # Create sample episodes
        for i in range(7):
            ep = Episode(
                date=f"2025-03-{10+i:02d}",
                predictions=EpisodePredictions(
                    tsmixer_raw=5.5,
                    plant_response={"trend": "better"}
                ),
                final_decision=FinalDecision(value=5.5, source="tsmixer")
            )
            episode_store.save(ep)

        pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig(
                enable_rag=False,
                enable_llm_insights=False
            )
        )

        result = pipeline.run(week_end_date="2025-03-16")

        assert result.prompt_block_tokens > 0
        assert result.prompt_block_tokens <= 800, \
            f"prompt_block should be ≤800 tokens, got {result.prompt_block_tokens}"

    def test_weekly_pipeline_aggregates_statistics(self, temp_json_storage):
        """Test weekly pipeline aggregates statistics correctly"""
        from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore
        from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision

        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        # Create episodes with varied values
        irrigation_values = [4.0, 5.0, 6.0, 5.5, 6.5, 5.0, 5.5]
        for i, value in enumerate(irrigation_values):
            ep = Episode(
                date=f"2025-03-{10+i:02d}",
                predictions=EpisodePredictions(
                    tsmixer_raw=value,
                    plant_response={"trend": "better"}
                ),
                final_decision=FinalDecision(value=value, source="tsmixer")
            )
            episode_store.save(ep)

        pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig(
                enable_rag=False,
                enable_llm_insights=False
            )
        )

        result = pipeline.run(week_end_date="2025-03-16")

        # Check aggregation
        total = sum(irrigation_values)
        daily_avg = total / len(irrigation_values)

        assert abs(result.summary.irrigation_stats.total - total) < 0.1
        assert abs(result.summary.irrigation_stats.daily_avg - daily_avg) < 0.1

    def test_weekly_pipeline_stores_summary(self, temp_json_storage):
        """Test weekly pipeline stores summary in WeeklySummaryStore"""
        from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore
        from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision

        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        # Create sample episodes
        for i in range(7):
            ep = Episode(
                date=f"2025-03-{10+i:02d}",
                predictions=EpisodePredictions(tsmixer_raw=5.0),
                final_decision=FinalDecision(value=5.0, source="tsmixer")
            )
            episode_store.save(ep)

        pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig(
                enable_rag=False,
                enable_llm_insights=False
            )
        )

        pipeline.run(week_end_date="2025-03-16")

        # Verify summary was stored
        stored = weekly_store.get_by_week("2025-03-10")

        assert stored is not None
        assert stored.week_start == "2025-03-10"


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_daily_then_weekly_pipeline(self, temp_json_storage, sample_user_data):
        """Test running daily pipeline for a week, then weekly summary"""
        from cucumber_irrigation.pipelines import (
            DailyPipeline, DailyPipelineConfig,
            WeeklyPipeline, WeeklyPipelineConfig
        )
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage,
            enable_rag=False,
            enable_growth_stage_detection=False
        )

        daily_pipeline = DailyPipeline(config=config)

        # Run daily pipeline for 7 days
        for i in range(7):
            env_data = {
                "temperature": 24.0 + i * 0.5,
                "humidity": 68.0 + i,
                "light": 7500.0 + i * 200
            }

            daily_pipeline.run(
                target_date=f"2025-03-{10+i:02d}",
                env_data=env_data,
                user_data=sample_user_data
            )

        # Run weekly pipeline
        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        weekly_pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig(
                enable_rag=False,
                enable_llm_insights=False
            )
        )

        weekly_result = weekly_pipeline.run(week_end_date="2025-03-16")

        assert weekly_result is not None
        assert weekly_result.summary.irrigation_stats.total > 0
        assert len(weekly_result.summary.key_insights) > 0

    def test_weekly_context_injection(self, temp_json_storage, sample_user_data):
        """Test weekly context is available for next week's daily pipeline (Q6.1)"""
        from cucumber_irrigation.pipelines import (
            DailyPipeline, DailyPipelineConfig,
            WeeklyPipeline, WeeklyPipelineConfig
        )
        from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore

        config = DailyPipelineConfig(
            use_mongodb=False,
            json_storage_path=temp_json_storage,
            enable_rag=False,
            enable_growth_stage_detection=False
        )

        daily_pipeline = DailyPipeline(config=config)

        # Run daily for week 1
        for i in range(7):
            daily_pipeline.run(
                target_date=f"2025-03-{10+i:02d}",
                env_data={"temperature": 25.0, "humidity": 70.0, "light": 8000.0},
                user_data=sample_user_data
            )

        # Generate weekly summary
        episode_store = EpisodeStore(
            json_path=os.path.join(temp_json_storage, "episodes.json")
        )
        weekly_store = WeeklySummaryStore(
            json_path=os.path.join(temp_json_storage, "weekly.json")
        )

        weekly_pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            config=WeeklyPipelineConfig(
                enable_rag=False,
                enable_llm_insights=False
            )
        )

        weekly_pipeline.run(week_end_date="2025-03-16")

        # Verify weekly context is available
        latest_weekly = weekly_store.get_latest()

        assert latest_weekly is not None
        assert latest_weekly.prompt_block is not None
        assert len(latest_weekly.prompt_block) > 0
