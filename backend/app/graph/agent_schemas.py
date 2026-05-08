"""JSON schemas for prompt-driven irrigation subagents."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


AgentStatus = Literal["ok", "degraded", "error"]


class Reference(BaseModel):
    model_config = ConfigDict(extra="allow")

    doc_id: str = "unknown"
    title: Optional[str] = None
    snippet: str = ""
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class YoloAgentReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    agent_name: str = "YOLOAgent"
    status: AgentStatus = "degraded"
    confidence: float = 0.0
    date: Optional[str] = None
    segmentation_metrics: Dict[str, Any] = Field(default_factory=dict)
    image_quality: Dict[str, Any] = Field(default_factory=dict)
    crop_state: Dict[str, Any] = Field(default_factory=dict)
    anomalies: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    llm_status: str = "fallback"
    prompt_version: str = "subagents/yolo_agent_system_v1"


class TSMixerAgentReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    agent_name: str = "TSMixerAgent"
    status: AgentStatus = "degraded"
    confidence: float = 0.0
    prediction_l_per_m2: float = 0.0
    input_contract: Dict[str, Any] = Field(default_factory=dict)
    yolo_context: Dict[str, Any] = Field(default_factory=dict)
    feature_health: Dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    risk_flags: List[str] = Field(default_factory=list)
    llm_status: str = "fallback"
    prompt_version: str = "subagents/tsmixer_agent_system_v1"


class RAGAgentReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    agent_name: str = "RAGAgent"
    phase: str = "rag"
    status: AgentStatus = "degraded"
    confidence: float = 0.0
    query: str = ""
    references: List[Reference] = Field(default_factory=list)
    evidence_summary: str = ""
    adjustment_advice: Dict[str, Any] = Field(default_factory=dict)
    missing_evidence: List[str] = Field(default_factory=list)
    llm_status: str = "fallback"
    prompt_version: str = "subagents/rag_agent_system_v1"


class MainAgentDecision(BaseModel):
    model_config = ConfigDict(extra="allow")

    agent_name: str = "MainAgent"
    status: AgentStatus = "degraded"
    final_irrigation_l_per_m2: float = 0.0
    confidence: float = 0.0
    explanation: str = ""
    references: List[Reference] = Field(default_factory=list)
    subagent_summary: Dict[str, Any] = Field(default_factory=dict)
    risk_flags: List[str] = Field(default_factory=list)
    llm_status: str = "fallback"
    prompt_version: str = "subagents/main_agent_system_v1"


def validate_report(
    model_cls: Type[BaseModel],
    data: Dict[str, Any],
    fallback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate a report while preserving extra LLM-provided fields."""
    try:
        return model_cls.model_validate(data).model_dump()
    except Exception as exc:
        safe = dict(fallback or {})
        safe.setdefault("status", "degraded")
        safe["schema_validation_error"] = str(exc)
        return model_cls.model_validate(safe).model_dump()
