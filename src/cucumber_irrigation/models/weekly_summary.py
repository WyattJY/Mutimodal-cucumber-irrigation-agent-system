from __future__ import annotations
"""WeeklySummary 数据模型

L3 周摘要数据结构
参考: requirements1.md 4.5节
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class TrendStats:
    """趋势统计"""
    better_days: int = 0
    same_days: int = 0
    worse_days: int = 0
    dominant_trend: str = "same"  # better | same | worse

    def to_dict(self) -> dict:
        return {
            "better_days": self.better_days,
            "same_days": self.same_days,
            "worse_days": self.worse_days,
            "dominant_trend": self.dominant_trend
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrendStats":
        return cls(
            better_days=data.get("better_days", 0),
            same_days=data.get("same_days", 0),
            worse_days=data.get("worse_days", 0),
            dominant_trend=data.get("dominant_trend", "same")
        )


@dataclass
class IrrigationStats:
    """灌溉统计"""
    total: float = 0.0
    daily_avg: float = 0.0
    max_value: float = 0.0
    min_value: float = 0.0
    trend: str = "stable"  # increasing | stable | decreasing

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "daily_avg": self.daily_avg,
            "max": self.max_value,
            "min": self.min_value,
            "trend": self.trend
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IrrigationStats":
        return cls(
            total=float(data.get("total", 0.0)),
            daily_avg=float(data.get("daily_avg", 0.0)),
            max_value=float(data.get("max", 0.0)),
            min_value=float(data.get("min", 0.0)),
            trend=data.get("trend", "stable")
        )


@dataclass
class AnomalyEvent:
    """异常事件记录"""
    date: str
    anomaly_type: str
    severity: str = "minor"  # minor | moderate | severe
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnomalyEvent":
        return cls(
            date=data.get("date", ""),
            anomaly_type=data.get("anomaly_type", ""),
            severity=data.get("severity", "minor"),
            description=data.get("description")
        )


@dataclass
class OverrideSummary:
    """人工覆盖总结"""
    count: int = 0
    total_delta: float = 0.0
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "total_delta": self.total_delta,
            "reasons": self.reasons
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OverrideSummary":
        return cls(
            count=data.get("count", 0),
            total_delta=float(data.get("total_delta", 0.0)),
            reasons=data.get("reasons", [])
        )


@dataclass
class WeeklySummary:
    """L3 周摘要

    用于动态 Prompt 注入的经验总结
    参考: requirements1.md 4.5节
    """
    week_start: str  # YYYY-MM-DD
    week_end: str
    season: str = ""

    # 统计数据 (落库但不注入)
    trend_stats: TrendStats = field(default_factory=TrendStats)
    irrigation_stats: IrrigationStats = field(default_factory=IrrigationStats)
    anomaly_events: List[AnomalyEvent] = field(default_factory=list)
    override_summary: OverrideSummary = field(default_factory=OverrideSummary)

    # 关键洞察 (用于生成 prompt_block)
    key_insights: List[str] = field(default_factory=list)

    # 知识引用 (Q7)
    knowledge_references: List[dict] = field(default_factory=list)

    # 核心: 用于注入的 Prompt 块
    prompt_block: str = ""
    prompt_block_tokens: int = 0

    # 元数据
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "week_start": self.week_start,
            "week_end": self.week_end,
            "season": self.season,
            "trend_stats": self.trend_stats.to_dict(),
            "irrigation_stats": self.irrigation_stats.to_dict(),
            "anomaly_events": [e.to_dict() for e in self.anomaly_events],
            "override_summary": self.override_summary.to_dict(),
            "key_insights": self.key_insights,
            "knowledge_references": self.knowledge_references,
            "prompt_block": self.prompt_block,
            "prompt_block_tokens": self.prompt_block_tokens,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WeeklySummary":
        return cls(
            week_start=data["week_start"],
            week_end=data["week_end"],
            season=data.get("season", ""),
            trend_stats=TrendStats.from_dict(data.get("trend_stats", {})),
            irrigation_stats=IrrigationStats.from_dict(data.get("irrigation_stats", {})),
            anomaly_events=[
                AnomalyEvent.from_dict(e)
                for e in data.get("anomaly_events", [])
            ],
            override_summary=OverrideSummary.from_dict(data.get("override_summary", {})),
            key_insights=data.get("key_insights", []),
            knowledge_references=data.get("knowledge_references", []),
            prompt_block=data.get("prompt_block", ""),
            prompt_block_tokens=data.get("prompt_block_tokens", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
