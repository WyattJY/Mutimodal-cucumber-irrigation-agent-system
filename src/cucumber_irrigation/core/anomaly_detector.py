"""异常检测器

检测三类异常: A1(范围), A2(矛盾), A3(环境)
参考: task1.md P2-04~07, requirements1.md 3.1-3.4节
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..models import (
    PlantResponse,
    AnomalyResult,
    ConflictSeverity,
    EnvAnomalyType
)


@dataclass
class ThresholdsConfig:
    """阈值配置"""
    # A1: 历史范围阈值
    irrigation_min: float = 0.1
    irrigation_max: float = 15.0

    # A2: 长势-灌水矛盾阈值
    severe_decrease_threshold: float = -0.10
    moderate_increase_threshold: float = 0.10
    severe_abnormality_threshold: float = 0.20
    mild_increase_threshold: float = 0.30

    # A3: 环境异常阈值
    consecutive_days: int = 3
    high_humidity: float = 85.0
    high_temperature: float = 35.0
    low_light: float = 2000.0

    @classmethod
    def from_yaml(cls, config: dict) -> "ThresholdsConfig":
        """从 YAML 配置创建"""
        ir = config.get("irrigation_range", {})
        tc = config.get("trend_conflict", {})
        ea = config.get("env_anomaly", {})

        return cls(
            irrigation_min=ir.get("min", 0.1),
            irrigation_max=ir.get("max", 15.0),
            severe_decrease_threshold=tc.get("severe_decrease_threshold", -0.10),
            moderate_increase_threshold=tc.get("moderate_increase_threshold", 0.10),
            severe_abnormality_threshold=tc.get("severe_abnormality_threshold", 0.20),
            mild_increase_threshold=tc.get("mild_increase_threshold", 0.30),
            consecutive_days=ea.get("consecutive_days", 3),
            high_humidity=ea.get("high_humidity", 85.0),
            high_temperature=ea.get("high_temperature", 35.0),
            low_light=ea.get("low_light", 2000.0)
        )


class AnomalyDetector:
    """异常检测器

    检测三类异常:
    - A1: 预测值超出历史范围 [0.1, 15.0]
    - A2: 长势-灌水矛盾
    - A3: 连续环境异常
    """

    def __init__(self, config: Optional[ThresholdsConfig] = None):
        """
        初始化检测器

        Args:
            config: 阈值配置 (可选，使用默认值)
        """
        self.config = config or ThresholdsConfig()

    def detect(
        self,
        prediction: float,
        yesterday_irrigation: float,
        plant_response: PlantResponse,
        env_history: List[dict]
    ) -> AnomalyResult:
        """
        执行异常检测

        Args:
            prediction: TSMixer 预测值
            yesterday_irrigation: 昨日灌水量
            plant_response: 长势评估结果
            env_history: 近N天环境数据 [{temperature, humidity, light}, ...]

        Returns:
            AnomalyResult 异常检测结果
        """
        result = AnomalyResult()

        # A1: 范围检测
        result.out_of_range = self._check_range(prediction)
        if result.out_of_range:
            result.out_of_range_value = prediction

        # A2: 矛盾检测
        conflict, severity, change_ratio = self._check_conflict(
            prediction, yesterday_irrigation, plant_response
        )
        result.trend_conflict = conflict
        result.trend_conflict_severity = severity
        result.change_ratio = change_ratio

        # A3: 环境异常检测
        env_anomaly, env_type, env_days = self._check_env_anomaly(env_history)
        result.env_anomaly = env_anomaly
        result.env_anomaly_type = env_type
        result.env_anomaly_days = env_days

        return result

    def _check_range(self, prediction: float) -> bool:
        """
        A1: 检测预测值是否超出历史范围

        阈值:
            - min: 0.1 L/m²
            - max: 15.0 L/m²

        Returns:
            True if 超出范围
        """
        return prediction < self.config.irrigation_min or \
               prediction > self.config.irrigation_max

    def _check_conflict(
        self,
        prediction: float,
        yesterday: float,
        plant_response: PlantResponse
    ) -> Tuple[bool, ConflictSeverity, float]:
        """
        A2: 检测长势-灌水矛盾

        矛盾严重程度:
        - severe: trend=worse 且 灌水减少>10%
        - moderate: trend=worse 且 灌水增加<10%
        - moderate: trend=worse 且 有严重异常 且 灌水增加<20%
        - mild: trend=better 且 灌水增加>30%
        - none: 无矛盾

        Returns:
            (是否矛盾, 严重程度, 变化率)
        """
        # 计算灌水变化率
        base = max(yesterday, 0.1)  # 避免除零
        change_ratio = (prediction - yesterday) / base

        # 获取趋势和异常信息
        trend = plant_response.trend.value
        has_severe_abnormality = plant_response.abnormalities.has_severe_abnormality()

        # 判断矛盾
        if trend == "worse":
            if change_ratio < self.config.severe_decrease_threshold:
                # 长势差但灌水减少 > 10%
                return True, ConflictSeverity.SEVERE, change_ratio
            elif change_ratio < self.config.moderate_increase_threshold:
                # 长势差但灌水增加 < 10%
                return True, ConflictSeverity.MODERATE, change_ratio
            elif has_severe_abnormality and change_ratio < self.config.severe_abnormality_threshold:
                # 有严重异常但灌水增加 < 20%
                return True, ConflictSeverity.MODERATE, change_ratio

        elif trend == "better":
            if change_ratio > self.config.mild_increase_threshold:
                # 长势好但灌水增加 > 30%
                return True, ConflictSeverity.MILD, change_ratio

        return False, ConflictSeverity.NONE, change_ratio

    def _check_env_anomaly(
        self,
        env_history: List[dict]
    ) -> Tuple[bool, Optional[EnvAnomalyType], int]:
        """
        A3: 检测连续环境异常

        异常类型:
        - high_humidity: 连续≥3天, humidity > 85%
        - high_temperature: 连续≥3天, temperature > 35°C
        - low_light: 连续≥3天, light < 2000 lux

        Returns:
            (是否异常, 异常类型, 连续天数)
        """
        if len(env_history) < self.config.consecutive_days:
            return False, None, 0

        recent = env_history[-self.config.consecutive_days:]

        # 高湿检测
        if all(e.get('humidity', 0) > self.config.high_humidity for e in recent):
            return True, EnvAnomalyType.HIGH_HUMIDITY, self.config.consecutive_days

        # 高温检测
        if all(e.get('temperature', 0) > self.config.high_temperature for e in recent):
            return True, EnvAnomalyType.HIGH_TEMPERATURE, self.config.consecutive_days

        # 弱光检测
        if all(e.get('light', float('inf')) < self.config.low_light for e in recent):
            return True, EnvAnomalyType.LOW_LIGHT, self.config.consecutive_days

        return False, None, 0

    def check_range_only(self, prediction: float) -> Tuple[bool, Optional[float]]:
        """
        仅检测范围异常 (快速检测)

        Returns:
            (是否超出范围, 超出的值)
        """
        out_of_range = self._check_range(prediction)
        return out_of_range, prediction if out_of_range else None

    def get_config(self) -> dict:
        """获取当前配置"""
        return {
            "irrigation_range": {
                "min": self.config.irrigation_min,
                "max": self.config.irrigation_max
            },
            "trend_conflict": {
                "severe_decrease_threshold": self.config.severe_decrease_threshold,
                "moderate_increase_threshold": self.config.moderate_increase_threshold,
                "severe_abnormality_threshold": self.config.severe_abnormality_threshold,
                "mild_increase_threshold": self.config.mild_increase_threshold
            },
            "env_anomaly": {
                "consecutive_days": self.config.consecutive_days,
                "high_humidity": self.config.high_humidity,
                "high_temperature": self.config.high_temperature,
                "low_light": self.config.low_light
            }
        }
