from __future__ import annotations
# Pydantic Models for API
"""
数据模型定义

包含:
1. 枚举类型 (TrendType, SeverityType, GrowthStageType, PredictionSource)
2. 请求模型 (DailyPredictRequest, KnowledgeQueryRequest, WeeklyGenerateRequest)
3. 响应模型 (PlantResponseResult, SanityCheckResult, DailyPredictResult 等)
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# 枚举类型
# ============================================================================

class TrendType(str, Enum):
    """长势趋势"""
    BETTER = "better"
    SAME = "same"
    WORSE = "worse"


class SeverityType(str, Enum):
    """异常严重程度"""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class GrowthStageType(str, Enum):
    """生育期类型"""
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MIXED = "mixed"


class PredictionSource(str, Enum):
    """预测来源"""
    TSMIXER = "tsmixer"
    OVERRIDE = "override"
    SANITY_ADJUSTED = "sanity_adjusted"
    FALLBACK = "fallback"


# ============================================================================
# YOLO 相关模型
# ============================================================================

class YoloMetrics(BaseModel):
    """YOLO 检测指标"""
    leaf_instance_count: float
    leaf_average_mask: float
    flower_instance_count: float
    flower_mask_pixel_count: float
    terminal_average_mask_pixel_count: float
    fruit_mask_average: float
    all_leaf_mask: float

    @classmethod
    def from_raw(cls, data: dict) -> "YoloMetrics":
        """从原始 JSON 数据转换"""
        return cls(
            leaf_instance_count=data.get("leaf Instance Count", 0),
            leaf_average_mask=data.get("leaf average mask", 0),
            flower_instance_count=data.get("flower Instance Count", 0),
            flower_mask_pixel_count=data.get("flower Mask Pixel Count", 0),
            terminal_average_mask_pixel_count=data.get("terminal average Mask Pixel Count", 0),
            fruit_mask_average=data.get("fruit Mask average", 0),
            all_leaf_mask=data.get("all leaf mask", 0),
        )


class EnvData(BaseModel):
    """环境数据"""
    temperature: float
    humidity: float
    light: float


class Evidence(BaseModel):
    """长势证据"""
    leaf_observation: str
    flower_observation: str
    fruit_observation: str
    terminal_bud_observation: str


class Abnormalities(BaseModel):
    """异常情况"""
    wilting: Literal["none", "mild", "moderate", "severe"]
    yellowing: Literal["none", "mild", "moderate", "severe"]
    pest_damage: Literal["none", "mild", "moderate", "severe"]
    other: str


class Comparison(BaseModel):
    """变化对比"""
    leaf_area_change: str
    leaf_count_change: str
    flower_count_change: str
    fruit_count_change: str
    overall_vigor_change: str


class PlantResponse(BaseModel):
    """LLM 长势响应"""
    trend: Literal["better", "same", "worse"]
    confidence: float
    evidence: Evidence
    abnormalities: Abnormalities
    growth_stage: str
    comparison: Comparison


class Episode(BaseModel):
    """单日决策记录"""
    date: str
    created_at: str
    prompt_version: str
    image_today: str
    image_yesterday: str
    yolo_today: YoloMetrics
    yolo_yesterday: YoloMetrics
    env_today: EnvData
    response: PlantResponse

    # 扩展字段
    irrigation_amount: Optional[float] = None
    decision_source: Optional[Literal["TSMixer", "FAO56", "Override"]] = None
    risk_level: Optional[Literal["low", "medium", "high", "critical"]] = None
    override_reason: Optional[str] = None


class EpisodeFilters(BaseModel):
    """Episode 查询参数"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    trend: Optional[str] = None
    source: Optional[str] = None
    risk_level: Optional[str] = None
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class OverrideData(BaseModel):
    """Override 提交数据"""
    date: str
    original_value: float
    replaced_value: float
    reason: str
    confirmation_answers: Optional[dict] = None


class ApiResponse(BaseModel):
    """统一 API 响应"""
    success: bool
    data: Optional[Any] = None
    error: Optional[dict] = None
    timestamp: str


class GrowthStats(BaseModel):
    """生长统计"""
    created_at: str
    all_leaf_mask: dict
    date_range: dict
    thresholds: dict


# ============================================================================
# 每日预测请求/响应模型
# ============================================================================

class PredictOptions(BaseModel):
    """预测选项"""
    run_sanity_check: bool = True
    use_rag: bool = True
    save_episode: bool = True
    save_response: bool = True


class DailyPredictRequest(BaseModel):
    """每日预测请求"""
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    image_base64: Optional[str] = Field(None, description="图片 Base64 (可选，不传则从 data/images/ 读取)")
    env_data: Optional[dict] = Field(None, description="环境数据 (可选，不传则从 CSV 读取)")
    options: Optional[PredictOptions] = Field(default_factory=PredictOptions)


class RAGReference(BaseModel):
    """RAG 检索引用"""
    doc_id: str = Field(..., description="文档ID")
    title: Optional[str] = Field(None, description="文档标题")
    snippet: str = Field(..., description="相关片段")
    relevance: float = Field(..., description="相关度分数 0-1")


class PlantResponseResult(BaseModel):
    """长势评估结果"""
    trend: Optional[TrendType] = Field(None, description="长势趋势 (冷启动时为 None)")
    confidence: float = Field(..., description="置信度 0-1")
    evidence: Evidence = Field(..., description="观察证据")
    abnormalities: Abnormalities = Field(..., description="异常情况")
    growth_stage: str = Field(..., description="生育期")
    comparison: Optional[Comparison] = Field(None, description="对比变化 (冷启动时为 None)")
    is_cold_start: bool = Field(False, description="是否为冷启动")
    current_state_summary: Optional[str] = Field(None, description="当前状态摘要 (冷启动时使用)")


class SanityCheckResult(BaseModel):
    """合理性复核结果"""
    is_consistent: bool = Field(..., description="预测值与长势是否一致")
    confidence: float = Field(..., description="判断置信度 0-1")
    adjusted_value: float = Field(..., description="调整后的灌水量")
    reason: str = Field(..., description="判断理由")
    rag_used: bool = Field(False, description="是否参考了知识库")


class DailyPredictResult(BaseModel):
    """每日预测结果"""
    date: str = Field(..., description="日期")
    irrigation_amount: float = Field(..., description="预测灌水量 L/m²")
    source: PredictionSource = Field(..., description="预测来源")
    is_cold_start: bool = Field(False, description="是否为冷启动")

    yolo_metrics: Optional[YoloMetrics] = Field(None, description="YOLO 指标")
    plant_response: Optional[PlantResponseResult] = Field(None, description="长势评估结果")
    sanity_check: Optional[SanityCheckResult] = Field(None, description="合理性复核结果")
    rag_references: List[RAGReference] = Field(default_factory=list, description="RAG 检索引用")

    warnings: List[str] = Field(default_factory=list, description="警告信息")
    suggestions: List[str] = Field(default_factory=list, description="建议信息")

    episode_id: Optional[str] = Field(None, description="Episode ID (日期)")
    response_saved_path: Optional[str] = Field(None, description="PlantResponse 保存路径")


# ============================================================================
# 知识库查询请求/响应模型
# ============================================================================

class KnowledgeQueryRequest(BaseModel):
    """知识库查询请求"""
    question: str = Field(..., description="问题")
    context: Optional[dict] = Field(None, description="上下文信息")
    top_k: int = Field(5, description="返回结果数量")


class RAGAnswer(BaseModel):
    """RAG 增强回答"""
    answer: str = Field(..., description="回答内容")
    references: List[RAGReference] = Field(default_factory=list, description="引用来源")
    model: str = Field(..., description="使用的模型")


# ============================================================================
# 周报生成请求/响应模型
# ============================================================================

class WeeklyGenerateRequest(BaseModel):
    """周报生成请求"""
    week_start: str = Field(..., description="周开始日期 (YYYY-MM-DD)")
    week_end: str = Field(..., description="周结束日期 (YYYY-MM-DD)")


class WeeklyStatistics(BaseModel):
    """周统计数据"""
    avg_irrigation: float = Field(..., description="平均灌水量")
    max_irrigation: float = Field(..., description="最大灌水量")
    min_irrigation: float = Field(..., description="最小灌水量")
    override_rate: float = Field(0.0, description="Override 比例")
    better_days: int = Field(0, description="好转天数")
    same_days: int = Field(0, description="平稳天数")
    worse_days: int = Field(0, description="下降天数")


class WeeklySummaryResult(BaseModel):
    """周报生成结果"""
    week_start: str = Field(..., description="周开始日期")
    week_end: str = Field(..., description="周结束日期")
    patterns: List[str] = Field(default_factory=list, description="发现的规律")
    risk_triggers: List[str] = Field(default_factory=list, description="风险触发条件")
    overrides: List[dict] = Field(default_factory=list, description="Override 记录")
    statistics: WeeklyStatistics = Field(..., description="统计数据")
    prompt_block: str = Field("", description="用于注入 Prompt 的摘要")
    insights: List[str] = Field(default_factory=list, description="关键洞察")

