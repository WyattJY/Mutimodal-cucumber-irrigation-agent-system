"""Pytest fixtures for cucumber-irrigation tests"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json


@pytest.fixture
def sample_env_data():
    """Sample environment data"""
    return {
        "temperature": 25.0,
        "humidity": 70.0,
        "light": 8000.0
    }


@pytest.fixture
def sample_plant_response():
    """Sample PlantResponse data"""
    from cucumber_irrigation.models import (
        PlantResponse, Comparison, Abnormalities, Evidence,
        Trend, GrowthStage
    )
    return PlantResponse(
        trend=Trend.BETTER,
        confidence=0.85,
        evidence=Evidence(
            leaf_observation="Leaves appear green and healthy",
            flower_observation="No flowers visible",
            fruit_observation="No fruits visible",
            terminal_bud_observation="Healthy terminal bud"
        ),
        abnormalities=Abnormalities(
            wilting="none",
            yellowing="none",
            pest_damage="none",
            other=""
        ),
        growth_stage=GrowthStage.VEGETATIVE,
        comparison=Comparison(
            leaf_area_change="增加",
            leaf_count_change="增加",
            flower_count_change="不适用",
            fruit_count_change="不适用",
            overall_vigor_change="增强"
        )
    )


@pytest.fixture
def sample_episode():
    """Sample Episode data"""
    from cucumber_irrigation.models import (
        Episode, EpisodeInputs, EpisodePredictions,
        EpisodeAnomalies, FinalDecision
    )
    return Episode(
        date="2025-03-14",
        season="spring",
        day_in_season=14,
        inputs=EpisodeInputs(
            environment={"temperature": 25.0, "humidity": 70.0, "light": 8000.0}
        ),
        predictions=EpisodePredictions(
            tsmixer_raw=5.5,
            growth_stage="vegetative",
            growth_stage_confidence=0.85
        ),
        anomalies=EpisodeAnomalies(
            out_of_range=False,
            trend_conflict=False
        ),
        final_decision=FinalDecision(
            value=5.5,
            source="tsmixer"
        )
    )


@pytest.fixture
def sample_weekly_summary():
    """Sample WeeklySummary data"""
    from cucumber_irrigation.models import (
        WeeklySummary, TrendStats, IrrigationStats, AnomalyEvent, OverrideSummary
    )
    return WeeklySummary(
        week_start="2025-03-10",
        week_end="2025-03-16",
        season="spring",
        trend_stats=TrendStats(
            better_days=3,
            same_days=2,
            worse_days=2,
            dominant_trend="better"
        ),
        irrigation_stats=IrrigationStats(
            total=42.5,
            daily_avg=6.07,
            max_value=8.2,
            min_value=4.5,
            trend="stable"
        ),
        anomaly_events=[
            AnomalyEvent(date="2025-03-12", anomaly_type="high_humidity", severity="moderate")
        ],
        override_summary=OverrideSummary(count=1, total_delta=0.5, reasons=["Test override"]),
        key_insights=["Stable irrigation pattern", "Good growth trend"]
    )


@pytest.fixture
def temp_json_storage(tmp_path):
    """Temporary JSON storage directory"""
    storage_path = tmp_path / "storage"
    storage_path.mkdir(parents=True, exist_ok=True)
    return str(storage_path)


@pytest.fixture
def sample_reference_data(tmp_path):
    """Create sample reference data CSV for ColdStartFiller"""
    dates = pd.date_range("2023-03-01", periods=120, freq="D")
    np.random.seed(42)

    data = {
        "date": [d.strftime('%Y-%m-%d') for d in dates],
        "temperature": np.random.uniform(18, 30, 120),
        "humidity": np.random.uniform(60, 85, 120),
        "light": np.random.uniform(5000, 15000, 120),
        "leaf Instance Count": np.random.uniform(5, 20, 120),
        "leaf average mask": np.random.uniform(100, 500, 120),
        "flower Instance Count": np.random.uniform(0, 10, 120),
        "flower Mask Pixel Count": np.random.uniform(0, 200, 120),
        "terminal average Mask Pixel Count": np.random.uniform(50, 150, 120),
        "fruit Mask average": np.random.uniform(0, 300, 120),
        "all leaf mask": np.random.uniform(500, 2000, 120),
        "Target": np.random.uniform(2, 10, 120)
    }

    df = pd.DataFrame(data)
    csv_path = tmp_path / "reference_data.csv"
    # Use tab separator as expected by ColdStartFiller
    df.to_csv(csv_path, index=False, sep='\t')
    return str(csv_path)


@pytest.fixture
def sample_user_data():
    """Create sample user data DataFrame"""
    dates = pd.date_range("2025-03-01", periods=30, freq="D")
    np.random.seed(42)

    data = {
        "date": dates,
        "temperature": np.random.uniform(20, 28, 30),
        "humidity": np.random.uniform(65, 80, 30),
        "light": np.random.uniform(6000, 12000, 30),
        "leaf Instance Count": np.random.uniform(8, 25, 30),
        "leaf average mask": np.random.uniform(150, 600, 30),
        "flower Instance Count": np.random.uniform(2, 15, 30),
        "flower Mask Pixel Count": np.random.uniform(50, 300, 30),
        "terminal average Mask Pixel Count": np.random.uniform(80, 200, 30),
        "fruit Mask average": np.random.uniform(100, 400, 30),
        "all leaf mask": np.random.uniform(800, 2500, 30),
        "Target": np.random.uniform(3, 9, 30)
    }

    return pd.DataFrame(data)
