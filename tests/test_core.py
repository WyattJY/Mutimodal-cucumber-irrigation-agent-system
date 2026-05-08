"""Unit tests for core components

P6-01: Tests for ColdStartFiller, WindowBuilder, AnomalyDetector, GrowthStageDetector
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime


class TestColdStartFiller:
    """Tests for ColdStartFiller (P2-02)"""

    def test_cold_start_filler_init(self, sample_reference_data):
        """Test ColdStartFiller initialization"""
        from cucumber_irrigation.core import ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        assert filler.reference_data is not None
        assert len(filler.reference_data) > 0

    def test_fill_empty_user_data(self, sample_reference_data):
        """Test filling when user has no data"""
        from cucumber_irrigation.core import ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        user_data = pd.DataFrame()
        target_date = "2025-03-14"

        result = filler.fill(
            user_data=user_data,
            target_date=target_date,
            required_length=96
        )

        assert len(result) == 96, "Should return 96 rows"

    def test_fill_partial_user_data(self, sample_reference_data, sample_user_data):
        """Test filling when user has partial data"""
        from cucumber_irrigation.core import ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        target_date = "2025-03-14"

        result = filler.fill(
            user_data=sample_user_data,
            target_date=target_date,
            required_length=96
        )

        assert len(result) == 96, "Should return 96 rows"

    def test_date_mapping(self, sample_reference_data):
        """Test date mapping to reference year (Q1.3)"""
        from cucumber_irrigation.core import ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)

        # 2025-03-14 should map to 2023-03-14
        mapped = filler._map_date_to_reference_year("2025-03-14")
        assert "2023" in mapped or mapped.endswith("-03-14"), "Should map to reference year"


class TestWindowBuilder:
    """Tests for WindowBuilder (P2-03)"""

    def test_window_builder_init(self, sample_reference_data):
        """Test WindowBuilder initialization"""
        from cucumber_irrigation.core import ColdStartFiller, WindowBuilder

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        builder = WindowBuilder(cold_start_filler=filler)

        assert builder.cold_start_filler is not None
        assert len(builder.feature_columns) == 11

    def test_build_window_shape(self, sample_reference_data, sample_user_data):
        """Test window building produces correct shape"""
        from cucumber_irrigation.core import ColdStartFiller, WindowBuilder

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        builder = WindowBuilder(cold_start_filler=filler)

        window = builder.build(
            data=sample_user_data,
            target_date="2025-03-14"
        )

        assert window.shape == (96, 11), f"Expected (96, 11), got {window.shape}"

    def test_build_with_today_data(self, sample_reference_data, sample_user_data):
        """Test window building with today's data"""
        from cucumber_irrigation.core import ColdStartFiller, WindowBuilder

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        builder = WindowBuilder(cold_start_filler=filler)

        today_data = {
            "temperature": 26.0,
            "humidity": 72.0,
            "light": 9000.0,
            "leaf Instance Count": 15.0,
            "leaf average mask": 300.0,
            "flower Instance Count": 5.0,
            "flower Mask Pixel Count": 100.0,
            "terminal average Mask Pixel Count": 120.0,
            "fruit Mask average": 200.0,
            "all leaf mask": 1500.0,
            "Target": 0.0
        }

        window = builder.build(
            data=sample_user_data,
            target_date="2025-03-14",
            today_data=today_data
        )

        assert window.shape == (96, 11)

    def test_feature_columns_order(self, sample_reference_data):
        """Test feature columns match expected order"""
        from cucumber_irrigation.core import WindowBuilder, ColdStartFiller

        filler = ColdStartFiller(reference_data_path=sample_reference_data)
        builder = WindowBuilder(cold_start_filler=filler)

        expected_columns = [
            'temperature', 'humidity', 'light',
            'leaf Instance Count', 'leaf average mask',
            'flower Instance Count', 'flower Mask Pixel Count',
            'terminal average Mask Pixel Count', 'fruit Mask average',
            'all leaf mask', 'Target'
        ]

        assert builder.feature_columns == expected_columns


class TestAnomalyDetector:
    """Tests for AnomalyDetector (P2-04 to P2-07)"""

    def test_anomaly_detector_init(self):
        """Test AnomalyDetector initialization"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()
        assert detector is not None

    def test_a1_range_detection_normal(self):
        """Test A1: Normal prediction within range (Q2.1)"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()
        out_of_range, details = detector.check_range_only(5.0)

        assert out_of_range is False, "5.0 L/m² should be in range [0.1, 15.0]"

    def test_a1_range_detection_too_high(self):
        """Test A1: Prediction too high (Q2.1)"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()
        out_of_range, details = detector.check_range_only(16.0)

        assert out_of_range is True, "16.0 L/m² should be out of range"

    def test_a1_range_detection_too_low(self):
        """Test A1: Prediction too low (Q2.1)"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()
        out_of_range, details = detector.check_range_only(0.05)

        assert out_of_range is True, "0.05 L/m² should be out of range"

    def test_a2_trend_conflict_worse_decrease(self, sample_plant_response):
        """Test A2: Trend conflict when worse + decrease (Q2.2)"""
        from cucumber_irrigation.core import AnomalyDetector
        from cucumber_irrigation.models import (
            PlantResponse, Comparison, Abnormalities, Evidence, Trend, GrowthStage
        )

        detector = AnomalyDetector()

        # Create worse trend response
        worse_response = PlantResponse(
            trend=Trend.WORSE,
            confidence=0.85,
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
            prediction=4.0,  # Lower than yesterday
            yesterday_irrigation=5.0,
            plant_response=worse_response,
            env_history=[]
        )

        assert result.trend_conflict is True, "Should detect conflict: worse trend with decreased irrigation"
        assert result.trend_conflict_severity.value == "severe"

    def test_a2_no_conflict_better_stable(self, sample_plant_response):
        """Test A2: No conflict when better + stable"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()

        result = detector.detect(
            prediction=5.5,
            yesterday_irrigation=5.0,
            plant_response=sample_plant_response,  # trend=BETTER
            env_history=[]
        )

        # Better trend with slight increase should not conflict
        assert result.trend_conflict is False or result.trend_conflict_severity.value in ["mild", "none"]

    def test_a3_env_anomaly_high_humidity(self, sample_plant_response):
        """Test A3: Consecutive high humidity detection (Q2.3)"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()

        env_history = [
            {"temperature": 25.0, "humidity": 88.0, "light": 8000.0},
            {"temperature": 26.0, "humidity": 90.0, "light": 8500.0},
            {"temperature": 24.0, "humidity": 87.0, "light": 7500.0},
        ]

        result = detector.detect(
            prediction=5.0,
            yesterday_irrigation=5.0,
            plant_response=sample_plant_response,
            env_history=env_history
        )

        assert result.env_anomaly is True, "Should detect high humidity anomaly"
        assert result.env_anomaly_type.value == "high_humidity"

    def test_a3_env_anomaly_high_temperature(self, sample_plant_response):
        """Test A3: Consecutive high temperature detection"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()

        env_history = [
            {"temperature": 36.0, "humidity": 70.0, "light": 8000.0},
            {"temperature": 37.0, "humidity": 68.0, "light": 8500.0},
            {"temperature": 38.0, "humidity": 65.0, "light": 9000.0},
        ]

        result = detector.detect(
            prediction=5.0,
            yesterday_irrigation=5.0,
            plant_response=sample_plant_response,
            env_history=env_history
        )

        assert result.env_anomaly is True
        assert result.env_anomaly_type.value == "high_temperature"

    def test_a3_env_anomaly_low_light(self, sample_plant_response):
        """Test A3: Consecutive low light detection"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()

        env_history = [
            {"temperature": 25.0, "humidity": 70.0, "light": 1500.0},
            {"temperature": 24.0, "humidity": 72.0, "light": 1800.0},
            {"temperature": 25.0, "humidity": 71.0, "light": 1600.0},
        ]

        result = detector.detect(
            prediction=5.0,
            yesterday_irrigation=5.0,
            plant_response=sample_plant_response,
            env_history=env_history
        )

        assert result.env_anomaly is True
        assert result.env_anomaly_type.value == "low_light"

    def test_a3_no_env_anomaly(self, sample_plant_response):
        """Test A3: No anomaly with normal environment"""
        from cucumber_irrigation.core import AnomalyDetector

        detector = AnomalyDetector()

        env_history = [
            {"temperature": 25.0, "humidity": 70.0, "light": 8000.0},
            {"temperature": 26.0, "humidity": 72.0, "light": 8500.0},
            {"temperature": 24.0, "humidity": 68.0, "light": 7500.0},
        ]

        result = detector.detect(
            prediction=5.0,
            yesterday_irrigation=5.0,
            plant_response=sample_plant_response,
            env_history=env_history
        )

        assert result.env_anomaly is False

    def test_anomaly_result_has_anomaly(self):
        """Test AnomalyResult.has_anomaly() method"""
        from cucumber_irrigation.models import AnomalyResult

        # No anomalies
        result = AnomalyResult(
            out_of_range=False,
            trend_conflict=False,
            env_anomaly=False
        )
        assert result.has_anomaly() is False

        # One anomaly
        result = AnomalyResult(
            out_of_range=True,
            trend_conflict=False,
            env_anomaly=False
        )
        assert result.has_anomaly() is True


class TestEnvInputHandler:
    """Tests for EnvInputHandler (P2-01)"""

    def test_from_frontend(self):
        """Test creating EnvInput from frontend data"""
        from cucumber_irrigation.core import EnvInputHandler

        handler = EnvInputHandler()
        env_input = handler.from_frontend(
            date="2025-03-14",
            temperature=25.0,
            humidity=70.0,
            light=8000.0
        )

        assert env_input.temperature == 25.0
        assert env_input.humidity == 70.0
        assert env_input.light == 8000.0
        assert env_input.source == "frontend"

    def test_validation_valid(self):
        """Test validation with valid data"""
        from cucumber_irrigation.core import EnvInputHandler
        from cucumber_irrigation.models import EnvInput

        handler = EnvInputHandler()
        env_input = EnvInput(
            date="2025-03-14",
            temperature=25.0,
            humidity=70.0,
            light=8000.0
        )

        is_valid, errors = handler.validate(env_input)
        assert is_valid is True
        assert len(errors) == 0

    def test_validation_invalid_temperature(self):
        """Test validation with invalid temperature"""
        from cucumber_irrigation.core import EnvInputHandler
        from cucumber_irrigation.models import EnvInput
        import pytest

        handler = EnvInputHandler()

        # EnvInput raises ValueError on invalid data
        with pytest.raises(ValueError):
            env_input = EnvInput(
                date="2025-03-14",
                temperature=55.0,  # Too high
                humidity=70.0,
                light=8000.0
            )


class TestGrowthStageDetector:
    """Tests for GrowthStageDetector (P2-08)"""

    def test_growth_stage_detector_init(self):
        """Test GrowthStageDetector initialization"""
        from cucumber_irrigation.core import GrowthStageDetector

        config = {"growth_stage_detection": {"confidence_threshold": 0.7}}
        detector = GrowthStageDetector(llm_service=None, config=config)
        assert detector is not None

    def test_get_retrieval_query(self):
        """Test retrieval query generation for different stages"""
        from cucumber_irrigation.core import GrowthStageDetector

        config = {"growth_stage_detection": {"confidence_threshold": 0.7}}
        detector = GrowthStageDetector(llm_service=None, config=config)

        vegetative_query = detector.get_retrieval_query("vegetative")
        assert "vegetative" in vegetative_query.lower()
        assert "kc" in vegetative_query.lower()

        flowering_query = detector.get_retrieval_query("flowering")
        assert "flowering" in flowering_query.lower()

        fruiting_query = detector.get_retrieval_query("fruiting")
        assert "fruiting" in fruiting_query.lower()

    def test_detect_from_yolo_metrics(self):
        """Test detect from YOLO metrics (fallback method)"""
        from cucumber_irrigation.core import GrowthStageDetector

        config = {"growth_stage_detection": {"confidence_threshold": 0.7}}
        detector = GrowthStageDetector(llm_service=None, config=config)

        # Test fruiting detection
        stage, confidence = detector.detect_from_yolo_metrics(
            flower_count=0.1, fruit_mask=1500, leaf_count=10
        )
        assert stage == "fruiting"
        assert confidence >= 0.7

        # Test flowering detection
        stage, confidence = detector.detect_from_yolo_metrics(
            flower_count=2.0, fruit_mask=100, leaf_count=10
        )
        assert stage == "flowering"

        # Test vegetative detection
        stage, confidence = detector.detect_from_yolo_metrics(
            flower_count=0.1, fruit_mask=100, leaf_count=10
        )
        assert stage == "vegetative"
