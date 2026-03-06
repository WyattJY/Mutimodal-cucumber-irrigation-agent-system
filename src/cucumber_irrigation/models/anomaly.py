from __future__ import annotations
"""异常检测和RAG结果数据模型

参考: task1.md P1-04, P1-05
参考: requirements1.md 3.1-3.6节
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, List
from enum import Enum
import json


class ConflictSeverity(str, Enum):
    """矛盾严重程度"""
    NONE = "none"
    MILD = "mild"           # 长势好但灌水增加>30%
    MODERATE = "moderate"   # 长势差但灌水增加<10%
    SEVERE = "severe"       # 长势差但灌水减少>10%


class EnvAnomalyType(str, Enum):
    """环境异常类型"""
    HIGH_HUMIDITY = "high_humidity"       # 连续≥3天 humidity > 85%
    HIGH_TEMPERATURE = "high_temperature"  # 连续≥3天 temperature > 35°C
    LOW_LIGHT = "low_light"                # 连续≥3天 light < 2000 lux


@dataclass
class AnomalyResult:
    """异常检测结果

    三类异常:
    - A1: 超出历史范围 (out_of_range)
    - A2: 长势-灌水矛盾 (trend_conflict)
    - A3: 环境异常 (env_anomaly)
    """
    # A1: 预测值超出历史范围 [0.1, 15.0]
    out_of_range: bool = False
    out_of_range_value: Optional[float] = None  # 超出的预测值

    # A2: 长势-灌水矛盾
    trend_conflict: bool = False
    trend_conflict_severity: ConflictSeverity = ConflictSeverity.NONE
    change_ratio: Optional[float] = None  # 灌水变化率

    # A3: 连续环境异常
    env_anomaly: bool = False
    env_anomaly_type: Optional[EnvAnomalyType] = None
    env_anomaly_days: int = 0  # 连续异常天数

    def has_anomaly(self) -> bool:
        """是否存在任何异常"""
        return self.out_of_range or self.trend_conflict or self.env_anomaly

    def get_anomaly_types(self) -> List[str]:
        """获取所有异常类型列表"""
        types = []
        if self.out_of_range:
            types.append("out_of_range")
        if self.trend_conflict:
            types.append(f"trend_conflict_{self.trend_conflict_severity.value}")
        if self.env_anomaly and self.env_anomaly_type:
            types.append(self.env_anomaly_type.value)
        return types

    def get_severity_level(self) -> str:
        """获取最高严重级别"""
        if self.trend_conflict_severity == ConflictSeverity.SEVERE:
            return "severe"
        if self.out_of_range:
            return "moderate"
        if self.trend_conflict_severity == ConflictSeverity.MODERATE:
            return "moderate"
        if self.env_anomaly:
            return "moderate"
        if self.trend_conflict_severity == ConflictSeverity.MILD:
            return "mild"
        return "none"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "out_of_range": self.out_of_range,
            "out_of_range_value": self.out_of_range_value,
            "trend_conflict": self.trend_conflict,
            "trend_conflict_severity": self.trend_conflict_severity.value,
            "change_ratio": self.change_ratio,
            "env_anomaly": self.env_anomaly,
            "env_anomaly_type": self.env_anomaly_type.value if self.env_anomaly_type else None,
            "env_anomaly_days": self.env_anomaly_days,
            "has_anomaly": self.has_anomaly(),
            "severity_level": self.get_severity_level()
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "AnomalyResult":
        """从字典创建"""
        env_type = data.get("env_anomaly_type")
        return cls(
            out_of_range=data.get("out_of_range", False),
            out_of_range_value=data.get("out_of_range_value"),
            trend_conflict=data.get("trend_conflict", False),
            trend_conflict_severity=ConflictSeverity(
                data.get("trend_conflict_severity", "none")
            ),
            change_ratio=data.get("change_ratio"),
            env_anomaly=data.get("env_anomaly", False),
            env_anomaly_type=EnvAnomalyType(env_type) if env_type else None,
            env_anomaly_days=data.get("env_anomaly_days", 0)
        )


@dataclass
class RAGResult:
    """RAG 检索结果

    用于存储从 Milvus/MongoDB 检索到的知识片段
    """
    doc_id: str                           # 文档 ID
    snippet: str                          # 检索到的文本片段
    relevance_score: float                # 相关性分数
    source: str                           # 来源标识
    is_fao56: bool = False                # 是否为 FAO56 文献
    source_type: Literal["system", "user"] = "system"  # 数据隔离: 系统/用户文献

    # 可选: 扩展元数据
    page: Optional[int] = None            # 页码
    chapter: Optional[str] = None         # 章节
    content_type: Optional[str] = None    # 内容类型: formula/table/text

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "doc_id": self.doc_id,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "is_fao56": self.is_fao56,
            "source_type": self.source_type
        }
        if self.page is not None:
            result["page"] = self.page
        if self.chapter is not None:
            result["chapter"] = self.chapter
        if self.content_type is not None:
            result["content_type"] = self.content_type
        return result

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "RAGResult":
        """从字典创建"""
        return cls(
            doc_id=data["doc_id"],
            snippet=data["snippet"],
            relevance_score=float(data.get("relevance_score", 0.0)),
            source=data.get("source", "unknown"),
            is_fao56=data.get("is_fao56", False),
            source_type=data.get("source_type", "system"),
            page=data.get("page"),
            chapter=data.get("chapter"),
            content_type=data.get("content_type")
        )

    def get_citation(self) -> str:
        """生成引用格式"""
        if self.is_fao56:
            return f"[FAO56] {self.source}"
        elif self.source_type == "user":
            return f"[用户文献] {self.source}"
        else:
            return f"[文献] {self.source}"


@dataclass
class KnowledgeReference:
    """知识引用记录

    用于 PlantResponse 和 WeeklySummary 中记录引用的知识
    """
    doc_id: str
    snippet: str
    usage: str              # 引用用途说明
    relevance: Literal["high", "medium", "low"] = "medium"

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "snippet": self.snippet,
            "usage": self.usage,
            "relevance": self.relevance
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeReference":
        return cls(
            doc_id=data["doc_id"],
            snippet=data["snippet"],
            usage=data.get("usage", ""),
            relevance=data.get("relevance", "medium")
        )
