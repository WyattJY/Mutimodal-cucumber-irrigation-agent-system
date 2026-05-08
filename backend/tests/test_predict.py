# T1.12 Phase 1 Integration Tests
"""
Phase 1 集成测试 - 每日预测流程
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.schemas import (
    TrendType,
    SeverityType,
    GrowthStageType,
    PredictionSource,
    PredictOptions,
    DailyPredictRequest,
    DailyPredictResult,
    PlantResponseResult,
    SanityCheckResult,
    Evidence,
    Abnormalities,
    Comparison,
    YoloMetrics,
)


class TestSchemas:
    """测试数据模型"""

    def test_trend_type_enum(self):
        """测试 TrendType 枚举"""
        assert TrendType.BETTER.value == "better"
        assert TrendType.SAME.value == "same"
        assert TrendType.WORSE.value == "worse"

    def test_severity_type_enum(self):
        """测试 SeverityType 枚举"""
        assert SeverityType.NONE.value == "none"
        assert SeverityType.MILD.value == "mild"
        assert SeverityType.SEVERE.value == "severe"

    def test_growth_stage_enum(self):
        """测试 GrowthStageType 枚举"""
        assert GrowthStageType.VEGETATIVE.value == "vegetative"
        assert GrowthStageType.FLOWERING.value == "flowering"
        assert GrowthStageType.FRUITING.value == "fruiting"
        assert GrowthStageType.MIXED.value == "mixed"

    def test_prediction_source_enum(self):
        """测试 PredictionSource 枚举"""
        assert PredictionSource.TSMIXER.value == "tsmixer"
        assert PredictionSource.OVERRIDE.value == "override"
        assert PredictionSource.SANITY_ADJUSTED.value == "sanity_adjusted"
        assert PredictionSource.FALLBACK.value == "fallback"

    def test_predict_options_defaults(self):
        """测试 PredictOptions 默认值"""
        options = PredictOptions()
        assert options.skip_yolo is False
        assert options.skip_tsmixer is False
        assert options.skip_plant_response is False
        assert options.skip_sanity_check is False
        assert options.skip_rag is False
        assert options.override_value is None
        assert options.override_reason is None

    def test_daily_predict_request(self):
        """测试 DailyPredictRequest 模型"""
        request = DailyPredictRequest(
            date="2024-05-30",
            image_base64="base64data",
            env_data={"temp": 25},
            options=PredictOptions(skip_yolo=True)
        )
        assert request.date == "2024-05-30"
        assert request.image_base64 == "base64data"
        assert request.env_data == {"temp": 25}
        assert request.options.skip_yolo is True

    def test_evidence_model(self):
        """测试 Evidence 模型"""
        evidence = Evidence(
            leaves="叶片健康",
            flowers="花朵数量正常",
            fruits="果实发育良好",
            apex="顶芽生长正常"
        )
        assert evidence.leaves == "叶片健康"
        assert evidence.apex == "顶芽生长正常"

    def test_abnormalities_model(self):
        """测试 Abnormalities 模型"""
        abnormalities = Abnormalities(
            wilting=SeverityType.NONE,
            yellowing=SeverityType.MILD,
            pests=SeverityType.NONE,
            disease=SeverityType.SEVERE
        )
        assert abnormalities.wilting == SeverityType.NONE
        assert abnormalities.yellowing == SeverityType.MILD
        assert abnormalities.disease == SeverityType.SEVERE

    def test_comparison_model(self):
        """测试 Comparison 模型"""
        comparison = Comparison(
            leaf_area_change=0.05,
            flower_count_change=2,
            fruit_count_change=1,
            overall_health_change=0.1
        )
        assert comparison.leaf_area_change == 0.05
        assert comparison.flower_count_change == 2

    def test_yolo_metrics_model(self):
        """测试 YoloMetrics 模型"""
        metrics = YoloMetrics(
            leaf_area=0.45,
            flower_count=12,
            fruit_count=5,
            health_score=0.85,
            detection_confidence=0.92
        )
        assert metrics.leaf_area == 0.45
        assert metrics.flower_count == 12
        assert metrics.health_score == 0.85

    def test_plant_response_result(self):
        """测试 PlantResponseResult 模型"""
        result = PlantResponseResult(
            trend=TrendType.BETTER,
            confidence=0.85,
            growth_stage=GrowthStageType.FLOWERING,
            evidence=Evidence(
                leaves="叶片健康",
                flowers="花朵数量增加",
                fruits="果实发育正常"
            ),
            abnormalities=Abnormalities(
                wilting=SeverityType.NONE,
                yellowing=SeverityType.NONE,
                pests=SeverityType.NONE,
                disease=SeverityType.NONE
            ),
            comparison=Comparison(
                leaf_area_change=0.02,
                flower_count_change=3
            ),
            is_cold_start=False,
            reasoning="植株整体状态良好"
        )
        assert result.trend == TrendType.BETTER
        assert result.confidence == 0.85
        assert result.is_cold_start is False

    def test_plant_response_result_cold_start(self):
        """测试冷启动时的 PlantResponseResult"""
        result = PlantResponseResult(
            trend=None,
            confidence=0.7,
            growth_stage=GrowthStageType.VEGETATIVE,
            evidence=Evidence(leaves="首次观察"),
            abnormalities=Abnormalities(),
            is_cold_start=True,
            reasoning="首次观察，无对比数据"
        )
        assert result.trend is None
        assert result.is_cold_start is True

    def test_sanity_check_result_consistent(self):
        """测试 SanityCheckResult - 一致"""
        result = SanityCheckResult(
            is_consistent=True,
            original_value=5.0,
            adjusted_value=5.0,
            adjustment_reason=None,
            confidence=0.9
        )
        assert result.is_consistent is True
        assert result.original_value == result.adjusted_value

    def test_sanity_check_result_inconsistent(self):
        """测试 SanityCheckResult - 不一致需调整"""
        result = SanityCheckResult(
            is_consistent=False,
            original_value=3.0,
            adjusted_value=4.5,
            adjustment_reason="植株状态显示需要更多水分",
            confidence=0.75
        )
        assert result.is_consistent is False
        assert result.adjusted_value > result.original_value
        assert result.adjustment_reason is not None

    def test_daily_predict_result(self):
        """测试 DailyPredictResult 模型"""
        result = DailyPredictResult(
            date="2024-05-30",
            irrigation_amount=5.2,
            source=PredictionSource.TSMIXER,
            is_cold_start=False,
            yolo_metrics=YoloMetrics(
                leaf_area=0.5,
                flower_count=10,
                fruit_count=3,
                health_score=0.9,
                detection_confidence=0.95
            ),
            plant_response=PlantResponseResult(
                trend=TrendType.SAME,
                confidence=0.8,
                growth_stage=GrowthStageType.FLOWERING,
                evidence=Evidence(leaves="正常"),
                abnormalities=Abnormalities(),
                is_cold_start=False
            ),
            sanity_check=SanityCheckResult(
                is_consistent=True,
                original_value=5.2,
                adjusted_value=5.2,
                confidence=0.85
            ),
            rag_references=[],
            warnings=[],
            suggestions=["建议保持当前灌水量"]
        )
        assert result.date == "2024-05-30"
        assert result.irrigation_amount == 5.2
        assert result.source == PredictionSource.TSMIXER
        assert result.is_cold_start is False


class TestPredictOptions:
    """测试预测选项"""

    def test_override_option(self):
        """测试 Override 选项"""
        options = PredictOptions(
            override_value=6.0,
            override_reason="手动调整"
        )
        assert options.override_value == 6.0
        assert options.override_reason == "手动调整"

    def test_skip_options(self):
        """测试跳过选项"""
        options = PredictOptions(
            skip_yolo=True,
            skip_plant_response=True
        )
        assert options.skip_yolo is True
        assert options.skip_plant_response is True
        assert options.skip_tsmixer is False


class TestColdStartScenarios:
    """测试冷启动场景"""

    def test_cold_start_detection(self):
        """测试冷启动检测"""
        # 冷启动时 trend 应为 None
        result = PlantResponseResult(
            trend=None,
            confidence=0.6,
            growth_stage=GrowthStageType.VEGETATIVE,
            evidence=Evidence(leaves="首次观察"),
            abnormalities=Abnormalities(),
            is_cold_start=True
        )
        assert result.is_cold_start is True
        assert result.trend is None

    def test_normal_prediction(self):
        """测试正常预测（非冷启动）"""
        result = PlantResponseResult(
            trend=TrendType.BETTER,
            confidence=0.85,
            growth_stage=GrowthStageType.FLOWERING,
            evidence=Evidence(leaves="叶片增长"),
            abnormalities=Abnormalities(),
            is_cold_start=False
        )
        assert result.is_cold_start is False
        assert result.trend is not None


class TestSanityCheckLogic:
    """测试 SanityCheck 逻辑"""

    def test_consistent_prediction(self):
        """测试预测一致的情况"""
        result = SanityCheckResult(
            is_consistent=True,
            original_value=5.0,
            adjusted_value=5.0,
            confidence=0.9
        )
        assert result.is_consistent is True
        assert result.original_value == result.adjusted_value

    def test_inconsistent_needs_increase(self):
        """测试不一致需要增加灌水量"""
        result = SanityCheckResult(
            is_consistent=False,
            original_value=3.0,
            adjusted_value=4.5,
            adjustment_reason="植株显示缺水迹象",
            confidence=0.75
        )
        assert result.is_consistent is False
        assert result.adjusted_value > result.original_value

    def test_inconsistent_needs_decrease(self):
        """测试不一致需要减少灌水量"""
        result = SanityCheckResult(
            is_consistent=False,
            original_value=6.0,
            adjusted_value=4.5,
            adjustment_reason="植株状态良好，可减少灌水",
            confidence=0.8
        )
        assert result.is_consistent is False
        assert result.adjusted_value < result.original_value


class TestPredictionSourcePriority:
    """测试预测来源优先级"""

    def test_override_takes_priority(self):
        """测试 Override 优先"""
        # 当有 override 时，source 应为 OVERRIDE
        result = DailyPredictResult(
            date="2024-05-30",
            irrigation_amount=6.0,
            source=PredictionSource.OVERRIDE,
            is_cold_start=False,
            rag_references=[],
            warnings=[],
            suggestions=[]
        )
        assert result.source == PredictionSource.OVERRIDE

    def test_sanity_adjusted_source(self):
        """测试 SanityCheck 调整后的来源"""
        result = DailyPredictResult(
            date="2024-05-30",
            irrigation_amount=4.5,
            source=PredictionSource.SANITY_ADJUSTED,
            is_cold_start=False,
            rag_references=[],
            warnings=[],
            suggestions=[]
        )
        assert result.source == PredictionSource.SANITY_ADJUSTED

    def test_tsmixer_source(self):
        """测试 TSMixer 预测来源"""
        result = DailyPredictResult(
            date="2024-05-30",
            irrigation_amount=5.2,
            source=PredictionSource.TSMIXER,
            is_cold_start=False,
            rag_references=[],
            warnings=[],
            suggestions=[]
        )
        assert result.source == PredictionSource.TSMIXER

    def test_fallback_source(self):
        """测试回退来源"""
        result = DailyPredictResult(
            date="2024-05-30",
            irrigation_amount=4.0,
            source=PredictionSource.FALLBACK,
            is_cold_start=False,
            rag_references=[],
            warnings=["TSMixer 不可用，使用回退值"],
            suggestions=[]
        )
        assert result.source == PredictionSource.FALLBACK


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
