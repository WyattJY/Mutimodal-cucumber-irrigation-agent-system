from __future__ import annotations
"""Episode 数据模型

每日完整决策记录
参考: requirements1.md 4.4节
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json


@dataclass
class EpisodeInputs:
    """输入快照"""
    environment: dict = field(default_factory=dict)
    yolo_metrics: dict = field(default_factory=dict)
    image_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "environment": self.environment,
            "yolo_metrics": self.yolo_metrics,
            "image_path": self.image_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpisodeInputs":
        return cls(
            environment=data.get("environment", {}),
            yolo_metrics=data.get("yolo_metrics", {}),
            image_path=data.get("image_path")
        )


@dataclass
class EpisodePredictions:
    """模型输出"""
    tsmixer_raw: Optional[float] = None
    plant_response: dict = field(default_factory=dict)
    sanity_check: dict = field(default_factory=dict)
    growth_stage: Optional[str] = None
    growth_stage_confidence: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "tsmixer_raw": self.tsmixer_raw,
            "plant_response": self.plant_response,
            "sanity_check": self.sanity_check,
            "growth_stage": self.growth_stage,
            "growth_stage_confidence": self.growth_stage_confidence
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpisodePredictions":
        return cls(
            tsmixer_raw=data.get("tsmixer_raw"),
            plant_response=data.get("plant_response", {}),
            sanity_check=data.get("sanity_check", {}),
            growth_stage=data.get("growth_stage"),
            growth_stage_confidence=data.get("growth_stage_confidence")
        )


@dataclass
class EpisodeAnomalies:
    """异常检测结果"""
    out_of_range: bool = False
    trend_conflict: bool = False
    trend_conflict_severity: str = "none"
    env_anomaly: bool = False
    env_anomaly_type: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "out_of_range": self.out_of_range,
            "trend_conflict": self.trend_conflict,
            "trend_conflict_severity": self.trend_conflict_severity,
            "env_anomaly": self.env_anomaly,
            "env_anomaly_type": self.env_anomaly_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpisodeAnomalies":
        return cls(
            out_of_range=data.get("out_of_range", False),
            trend_conflict=data.get("trend_conflict", False),
            trend_conflict_severity=data.get("trend_conflict_severity", "none"),
            env_anomaly=data.get("env_anomaly", False),
            env_anomaly_type=data.get("env_anomaly_type")
        )


@dataclass
class FinalDecision:
    """最终决策"""
    value: float = 0.0
    source: str = "tsmixer"  # tsmixer | override
    override_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "source": self.source,
            "override_reason": self.override_reason
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FinalDecision":
        return cls(
            value=float(data.get("value", 0.0)),
            source=data.get("source", "tsmixer"),
            override_reason=data.get("override_reason")
        )


@dataclass
class UserFeedback:
    """用户反馈"""
    actual_irrigation: Optional[float] = None
    notes: Optional[str] = None
    rating: Optional[int] = None  # 1-5

    def to_dict(self) -> dict:
        return {
            "actual_irrigation": self.actual_irrigation,
            "notes": self.notes,
            "rating": self.rating
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserFeedback":
        return cls(
            actual_irrigation=data.get("actual_irrigation"),
            notes=data.get("notes"),
            rating=data.get("rating")
        )


@dataclass
class Episode:
    """每日决策记录 (L2 Episodic Log)"""
    date: str
    season: str = ""
    day_in_season: int = 0

    inputs: EpisodeInputs = field(default_factory=EpisodeInputs)
    predictions: EpisodePredictions = field(default_factory=EpisodePredictions)
    anomalies: EpisodeAnomalies = field(default_factory=EpisodeAnomalies)
    final_decision: FinalDecision = field(default_factory=FinalDecision)
    user_feedback: UserFeedback = field(default_factory=UserFeedback)

    # RAG 检索记录 (只记录 doc_id，不存内容)
    rag_doc_ids: List[str] = field(default_factory=list)

    # 知识引用 (Q7)
    knowledge_references: List[dict] = field(default_factory=list)

    # 元数据
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "season": self.season,
            "day_in_season": self.day_in_season,
            "inputs": self.inputs.to_dict(),
            "predictions": self.predictions.to_dict(),
            "anomalies": self.anomalies.to_dict(),
            "final_decision": self.final_decision.to_dict(),
            "user_feedback": self.user_feedback.to_dict(),
            "rag_doc_ids": self.rag_doc_ids,
            "knowledge_references": self.knowledge_references,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        return cls(
            date=data["date"],
            season=data.get("season", ""),
            day_in_season=data.get("day_in_season", 0),
            inputs=EpisodeInputs.from_dict(data.get("inputs", {})),
            predictions=EpisodePredictions.from_dict(data.get("predictions", {})),
            anomalies=EpisodeAnomalies.from_dict(data.get("anomalies", {})),
            final_decision=FinalDecision.from_dict(data.get("final_decision", {})),
            user_feedback=UserFeedback.from_dict(data.get("user_feedback", {})),
            rag_doc_ids=data.get("rag_doc_ids", []),
            knowledge_references=data.get("knowledge_references", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
