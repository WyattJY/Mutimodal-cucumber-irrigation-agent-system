from __future__ import annotations
"""数据模型"""

from .plant_response import (
    PlantResponse,
    Comparison,
    Abnormalities,
    Evidence,
    Trend,
    GrowthStage,
    SeverityLevel
)

from .env_input import EnvInput

from .anomaly import (
    AnomalyResult,
    ConflictSeverity,
    EnvAnomalyType,
    RAGResult,
    KnowledgeReference
)

from .episode import (
    Episode,
    EpisodeInputs,
    EpisodePredictions,
    EpisodeAnomalies,
    FinalDecision,
    UserFeedback
)

from .weekly_summary import (
    WeeklySummary,
    TrendStats,
    IrrigationStats,
    AnomalyEvent,
    OverrideSummary
)

__all__ = [
    # PlantResponse 相关
    "PlantResponse",
    "Comparison",
    "Abnormalities",
    "Evidence",
    "Trend",
    "GrowthStage",
    "SeverityLevel",
    # EnvInput
    "EnvInput",
    # Anomaly 相关
    "AnomalyResult",
    "ConflictSeverity",
    "EnvAnomalyType",
    "RAGResult",
    "KnowledgeReference",
    # Episode 相关
    "Episode",
    "EpisodeInputs",
    "EpisodePredictions",
    "EpisodeAnomalies",
    "FinalDecision",
    "UserFeedback",
    # WeeklySummary 相关
    "WeeklySummary",
    "TrendStats",
    "IrrigationStats",
    "AnomalyEvent",
    "OverrideSummary"
]
