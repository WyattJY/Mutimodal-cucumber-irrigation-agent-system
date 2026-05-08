from __future__ import annotations
"""PlantResponse 数据模型"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import json
import re


class Trend(str, Enum):
    """长势趋势"""
    BETTER = "better"
    SAME = "same"
    WORSE = "worse"


class GrowthStage(str, Enum):
    """生长阶段"""
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MATURE = "mature"


class SeverityLevel(str, Enum):
    """严重程度"""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class Evidence:
    """观察证据"""
    leaf_observation: str = ""
    flower_observation: str = ""
    fruit_observation: str = ""
    terminal_bud_observation: str = ""

    def to_dict(self) -> dict:
        return {
            "leaf_observation": self.leaf_observation,
            "flower_observation": self.flower_observation,
            "fruit_observation": self.fruit_observation,
            "terminal_bud_observation": self.terminal_bud_observation
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        return cls(
            leaf_observation=data.get("leaf_observation", ""),
            flower_observation=data.get("flower_observation", ""),
            fruit_observation=data.get("fruit_observation", ""),
            terminal_bud_observation=data.get("terminal_bud_observation", "")
        )


@dataclass
class Abnormalities:
    """异常情况"""
    wilting: str = "none"
    yellowing: str = "none"
    pest_damage: str = "none"
    other: str = ""

    def to_dict(self) -> dict:
        return {
            "wilting": self.wilting,
            "yellowing": self.yellowing,
            "pest_damage": self.pest_damage,
            "other": self.other
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Abnormalities":
        return cls(
            wilting=data.get("wilting", "none"),
            yellowing=data.get("yellowing", "none"),
            pest_damage=data.get("pest_damage", "none"),
            other=data.get("other", "")
        )

    def has_abnormality(self) -> bool:
        """是否有异常"""
        return any([
            self.wilting != "none",
            self.yellowing != "none",
            self.pest_damage != "none",
            bool(self.other)
        ])

    def has_severe_abnormality(self) -> bool:
        """是否有严重异常"""
        return any([
            self.wilting in ("moderate", "severe"),
            self.yellowing in ("moderate", "severe"),
            self.pest_damage in ("moderate", "severe")
        ])


@dataclass
class Comparison:
    """对比结果"""
    leaf_area_change: str = "持平"
    leaf_count_change: str = "持平"
    flower_count_change: str = "不适用"
    fruit_count_change: str = "不适用"
    overall_vigor_change: str = "持平"

    def to_dict(self) -> dict:
        return {
            "leaf_area_change": self.leaf_area_change,
            "leaf_count_change": self.leaf_count_change,
            "flower_count_change": self.flower_count_change,
            "fruit_count_change": self.fruit_count_change,
            "overall_vigor_change": self.overall_vigor_change
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Comparison":
        return cls(
            leaf_area_change=data.get("leaf_area_change", "持平"),
            leaf_count_change=data.get("leaf_count_change", "持平"),
            flower_count_change=data.get("flower_count_change", "不适用"),
            fruit_count_change=data.get("fruit_count_change", "不适用"),
            overall_vigor_change=data.get("overall_vigor_change", "持平")
        )


@dataclass
class PlantResponse:
    """植物长势评估响应 - 匹配 LLM 输出格式"""
    trend: Trend
    confidence: float
    evidence: Evidence
    abnormalities: Abnormalities
    growth_stage: GrowthStage
    comparison: Comparison

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "trend": self.trend.value,
            "confidence": self.confidence,
            "evidence": self.evidence.to_dict(),
            "abnormalities": self.abnormalities.to_dict(),
            "growth_stage": self.growth_stage.value,
            "comparison": self.comparison.to_dict()
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "PlantResponse":
        """从字典创建"""
        # 处理 trend
        trend_value = data.get("trend", "same")
        if isinstance(trend_value, str):
            trend = Trend(trend_value.lower())
        else:
            trend = Trend.SAME

        # 处理 growth_stage
        stage_value = data.get("growth_stage", "vegetative")
        if isinstance(stage_value, str):
            try:
                growth_stage = GrowthStage(stage_value.lower())
            except ValueError:
                growth_stage = GrowthStage.VEGETATIVE
        else:
            growth_stage = GrowthStage.VEGETATIVE

        return cls(
            trend=trend,
            confidence=float(data.get("confidence", 0.5)),
            evidence=Evidence.from_dict(data.get("evidence", {})),
            abnormalities=Abnormalities.from_dict(data.get("abnormalities", {})),
            growth_stage=growth_stage,
            comparison=Comparison.from_dict(data.get("comparison", {}))
        )

    @classmethod
    def from_json(cls, json_str: str) -> "PlantResponse":
        """从 JSON 字符串创建"""
        # 清理可能的 markdown 代码块
        cleaned = json_str.strip()
        if cleaned.startswith("```"):
            # 移除 ```json 和 ```
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

        data = json.loads(cleaned)
        return cls.from_dict(data)

    @classmethod
    def from_llm_response(cls, response: str) -> "PlantResponse":
        """从 LLM 响应解析（兼容可能的格式问题）"""
        try:
            return cls.from_json(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return cls.from_json(json_match.group())
            raise ValueError(f"无法从 LLM 响应中解析 JSON: {response[:200]}...")
