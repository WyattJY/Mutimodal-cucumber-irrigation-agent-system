# 温室黄瓜灌水智能体系统 - 功能补充设计文档

> 版本：v1.0
> 创建日期：2024-12-27
> 基于：requirements_27bu.md
> 文档状态：设计完成，待实现

---

## 1. 核心目标

### 1.1 总体目标

补齐系统的 **记忆功能** 和 **智能分析链路**，使系统从"工具集合"升级为"具备记忆的智能体"。

### 1.2 具体目标

| 编号 | 目标 | 验收标准 |
|------|------|----------|
| G1 | 上传图片后自动生成 PlantResponse | GPT-5.2 分析结果保存到 `output/responses/` |
| G2 | 支持单张图片冷启动 | 首次上传不报错，生成单日分析 |
| G3 | 每日决策自动入库 Episode | MongoDB/JSON 中可查询 Episode |
| G4 | SanityCheck 验证 TSMixer 预测 | 不一致时给出调整建议 |
| G5 | Weekly Summary 自动/手动生成 | 周报可注入后续决策 Prompt |
| G6 | RAG 知识检索集成 | 问答时显示引用来源 |

### 1.3 非目标（本次不做）

- 不修改 YOLO/TSMixer 模型
- 不新增数据库（使用现有 MongoDB/JSON）
- 不修改 LLM API 配置方式

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   前端 (React + Vite)                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Dashboard  │ │ DailyDecision│ │   History   │ │   Weekly    │ │  Knowledge │ │
│  │  (概览)     │ │ (今日决策)   │ │  (历史)     │ │  (周报)     │ │  (RAG问答) │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬─────┘ │
│         │               │               │               │               │        │
│         └───────────────┴───────────────┴───────────────┴───────────────┘        │
│                                         │                                         │
│                              HTTP / SSE │                                         │
└─────────────────────────────────────────┼─────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              后端 API 层 (FastAPI)                               │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         API Routes (backend/app/api/v1/)                 │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │
│  │  │ predict  │ │ episodes │ │  weekly  │ │knowledge │ │  upload  │ ...   │    │
│  │  │ (NEW)    │ │          │ │ (增强)   │ │ (增强)   │ │          │       │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │    │
│  └───────┼────────────┼────────────┼────────────┼────────────┼─────────────┘    │
│          │            │            │            │            │                   │
│          ▼            ▼            ▼            ▼            ▼                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                     Services (backend/app/services/)                     │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │    │
│  │  │ prediction │ │    llm     │ │    yolo    │ │  tsmixer   │            │    │
│  │  │  (NEW)     │ │  (增强)    │ │            │ │            │            │    │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘            │    │
│  └────────┼──────────────┼──────────────┼──────────────┼───────────────────┘    │
│           │              │              │              │                         │
└───────────┼──────────────┼──────────────┼──────────────┼─────────────────────────┘
            │              │              │              │
            ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           核心模块层 (src/cucumber_irrigation/)                  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                           Pipelines (管道编排)                          │     │
│  │      ┌─────────────────────┐         ┌─────────────────────┐           │     │
│  │      │   DailyPipeline     │         │   WeeklyPipeline    │           │     │
│  │      │   (每日决策流程)     │         │   (周度总结流程)     │           │     │
│  │      └──────────┬──────────┘         └──────────┬──────────┘           │     │
│  └─────────────────┼────────────────────────────────┼─────────────────────┘     │
│                    │                                │                            │
│  ┌─────────────────┼────────────────────────────────┼─────────────────────┐     │
│  │                 ▼            Memory (4层记忆)     ▼                     │     │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐        │     │
│  │  │  L1 Working      │ │  L2 Episode      │ │  L3 Weekly       │        │     │
│  │  │  Context         │ │  Store           │ │  Summary Store   │        │     │
│  │  │  (工作上下文)     │ │  (日记录存储)    │ │  (周摘要存储)    │        │     │
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘        │     │
│  │                                                                         │     │
│  │  ┌──────────────────────────────────────────────────────────────┐      │     │
│  │  │                    L4 Knowledge Retrieval                     │      │     │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │      │     │
│  │  │  │  Embedder   │ │  Retriever  │ │ Local RAG   │              │      │     │
│  │  │  │  (向量化)    │ │  (检索器)   │ │ Service     │              │      │     │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘              │      │     │
│  │  └──────────────────────────────────────────────────────────────┘      │     │
│  └─────────────────────────────────────────────────────────────────────────┘     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐     │
│  │                             Services (服务层)                            │     │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │     │
│  │  │ LLMService │ │ RAGService │ │ DBService  │ │TSMixerSvc  │            │     │
│  │  │ (长势评估)  │ │ (知识检索)  │ │ (数据存储)  │ │(时序预测)   │            │     │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │     │
│  └─────────────────────────────────────────────────────────────────────────┘     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐     │
│  │                              Core (核心组件)                             │     │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │     │
│  │  │ EnvHandler │ │WindowBuilder│ │ Anomaly   │ │GrowthStage │            │     │
│  │  │ (环境处理)  │ │ (窗口构建)  │ │ Detector  │ │ Detector   │            │     │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │     │
│  └─────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   存储层                                         │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐    │
│  │   data/images  │ │ output/responses│ │data/storage/   │ │ output/yolo_   │    │
│  │   (原始图像)    │ │ (PlantResponse) │ │episodes.json   │ │ metrics/       │    │
│  └────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构

```
                                    用户上传图片
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                              每日预测流程 (DailyPredictFlow)                     │
│                                                                                 │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│   │ 1.保存  │───▶│ 2.YOLO  │───▶│ 3.查找  │───▶│ 4.构建  │───▶│ 5.TSMixer│     │
│   │  图片   │    │  推理   │    │ 昨日图片 │    │ 时序窗口 │    │   预测   │     │
│   └─────────┘    └─────────┘    └────┬────┘    └─────────┘    └─────────┘     │
│                                      │                              │          │
│                              ┌───────┴───────┐                      │          │
│                              ▼               ▼                      │          │
│                         [有昨日]         [无昨日]                    │          │
│                              │               │                      │          │
│                              ▼               ▼                      ▼          │
│   ┌─────────┐    ┌─────────────────┐  ┌─────────────┐    ┌─────────────────┐  │
│   │ 6.生育期 │◀──│ 7.PlantResponse │  │ 7.单日分析  │    │  8.RAG 检索     │  │
│   │  检测   │    │  (今日vs昨日)   │  │ (冷启动)    │    │  (可选)         │  │
│   └─────────┘    └─────────────────┘  └─────────────┘    └─────────────────┘  │
│        │                   │                 │                    │            │
│        └───────────────────┼─────────────────┼────────────────────┘            │
│                            ▼                 ▼                                 │
│                  ┌─────────────────────────────────────┐                       │
│                  │      9. 构建 Working Context (L1)    │                       │
│                  │  ┌─────────┬─────────┬─────────────┐ │                       │
│                  │  │ System  │ Weekly  │ RAG Results │ │                       │
│                  │  │ Prompt  │ Summary │             │ │                       │
│                  │  └─────────┴─────────┴─────────────┘ │                       │
│                  └──────────────────┬──────────────────┘                       │
│                                     ▼                                          │
│                  ┌─────────────────────────────────────┐                       │
│                  │        10. SanityCheck (复核)        │                       │
│                  │  PlantResponse + TSMixer → 一致性判断 │                       │
│                  └──────────────────┬──────────────────┘                       │
│                                     ▼                                          │
│                  ┌─────────────────────────────────────┐                       │
│                  │         11. 创建 Episode (L2)        │                       │
│                  │  inputs + predictions + llm_outputs  │                       │
│                  └──────────────────┬──────────────────┘                       │
│                                     ▼                                          │
│                  ┌─────────────────────────────────────┐                       │
│                  │        12. 保存 & 返回结果           │                       │
│                  │  PlantResponse → output/responses/   │                       │
│                  │  Episode → data/storage/episodes.json│                       │
│                  └─────────────────────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块划分

### 3.1 新增模块

```
backend/app/
├── api/v1/
│   ├── predict.py          # [增强] 每日预测 API
│   ├── knowledge.py        # [增强] RAG 增强问答 API
│   └── weekly.py           # [增强] 周报生成 API
│
├── services/
│   ├── prediction_service.py   # [新增] 预测编排服务
│   ├── llm_service.py          # [增强] 添加 generate_plant_response
│   ├── memory_service.py       # [新增] 记忆层封装
│   └── rag_service.py          # [新增] RAG 服务封装
│
└── core/
    └── pipeline_adapter.py     # [新增] 核心模块适配器
```

### 3.2 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| **predict.py** | 暴露 `/api/predict/daily` 端点 | prediction_service |
| **prediction_service.py** | 编排完整预测流程 | llm, yolo, tsmixer, memory |
| **memory_service.py** | 封装 Episode/WeeklySummary 存储 | src/.../memory/* |
| **rag_service.py** | 封装 RAG 检索 | src/.../rag/* |
| **pipeline_adapter.py** | 适配 src/ 核心模块到 backend | src/.../pipelines/* |

### 3.3 模块交互图

```
┌──────────────────────────────────────────────────────────────────┐
│                         API Layer                                 │
│                                                                   │
│    predict.py ──────────────────────────────────────────────┐    │
│         │                                                    │    │
│         ▼                                                    │    │
│    ┌─────────────────────────────────────────────────────┐  │    │
│    │              prediction_service.py                   │  │    │
│    │                                                      │  │    │
│    │   ┌─────────────┬─────────────┬─────────────┐       │  │    │
│    │   │  YOLO       │  TSMixer    │  LLM        │       │  │    │
│    │   │  Service    │  Service    │  Service    │       │  │    │
│    │   └──────┬──────┴──────┬──────┴──────┬──────┘       │  │    │
│    │          │             │             │               │  │    │
│    │   ┌──────▼─────────────▼─────────────▼──────┐       │  │    │
│    │   │           memory_service.py             │       │  │    │
│    │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │       │  │    │
│    │   │  │ Episode │ │ Weekly  │ │ Working │   │       │  │    │
│    │   │  │ Store   │ │ Summary │ │ Context │   │       │  │    │
│    │   │  └─────────┘ └─────────┘ └─────────┘   │       │  │    │
│    │   └─────────────────────────────────────────┘       │  │    │
│    │                       │                              │  │    │
│    │   ┌───────────────────▼───────────────────┐         │  │    │
│    │   │             rag_service.py            │         │  │    │
│    │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │         │  │    │
│    │   │  │Embedder │ │Retriever│ │LocalRAG │ │         │  │    │
│    │   │  └─────────┘ └─────────┘ └─────────┘ │         │  │    │
│    │   └───────────────────────────────────────┘         │  │    │
│    └─────────────────────────────────────────────────────┘  │    │
│                                                              │    │
│    knowledge.py ─────────────────────────────────────────────┘    │
│    weekly.py ────────────────────────────────────────────────────►│
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. 核心组件设计

### 4.1 PredictionService (预测编排服务)

```python
# backend/app/services/prediction_service.py

class PredictionService:
    """
    每日预测编排服务

    职责:
    1. 协调 YOLO, TSMixer, LLM 服务
    2. 处理冷启动情况
    3. 构建 Working Context
    4. 生成并保存 PlantResponse
    5. 执行 SanityCheck
    6. 创建 Episode
    """

    def __init__(
        self,
        yolo_service: YOLOService,
        tsmixer_service: TSMixerService,
        llm_service: LLMService,
        memory_service: MemoryService,
        rag_service: Optional[RAGService] = None
    ):
        self.yolo = yolo_service
        self.tsmixer = tsmixer_service
        self.llm = llm_service
        self.memory = memory_service
        self.rag = rag_service

    async def predict_daily(
        self,
        date: str,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        env_data: Optional[dict] = None,
        options: Optional[PredictOptions] = None
    ) -> DailyPredictResult:
        """
        执行完整的每日预测流程

        Returns:
            DailyPredictResult: 包含预测值、PlantResponse、SanityCheck 等
        """
        pass

    async def _find_yesterday_image(self, date: str) -> Optional[str]:
        """查找昨日图片，支持跳过缺失日期"""
        pass

    async def _generate_plant_response(
        self,
        image_today: str,
        image_yesterday: Optional[str],
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        is_cold_start: bool
    ) -> PlantResponseResult:
        """生成 PlantResponse (对比分析或单日分析)"""
        pass

    async def _run_sanity_check(
        self,
        tsmixer_prediction: float,
        plant_response: dict,
        env_data: dict,
        weekly_context: Optional[str]
    ) -> SanityCheckResult:
        """执行合理性复核"""
        pass
```

### 4.2 MemoryService (记忆层封装)

```python
# backend/app/services/memory_service.py

class MemoryService:
    """
    记忆层统一封装

    职责:
    1. 管理 Episode 存储 (L2)
    2. 管理 Weekly Summary 存储 (L3)
    3. 构建 Working Context (L1)
    4. 提供记忆查询接口
    """

    def __init__(
        self,
        storage_path: str = "data/storage",
        use_mongodb: bool = False
    ):
        self.episode_store = EpisodeStore(...)
        self.weekly_store = WeeklySummaryStore(...)
        self.context_builder = WorkingContextBuilder(...)

    # === L2: Episode ===

    async def save_episode(self, episode: Episode) -> str:
        """保存 Episode"""
        pass

    async def get_episode(self, date: str) -> Optional[Episode]:
        """获取指定日期的 Episode"""
        pass

    async def get_recent_episodes(self, days: int = 7) -> List[Episode]:
        """获取最近 N 天的 Episodes"""
        pass

    # === L3: Weekly Summary ===

    async def save_weekly_summary(self, summary: WeeklySummary) -> str:
        """保存周摘要"""
        pass

    async def get_latest_weekly_summary(self) -> Optional[WeeklySummary]:
        """获取最新的周摘要"""
        pass

    async def get_weekly_prompt_block(self) -> Optional[str]:
        """获取用于注入 Prompt 的周摘要块"""
        pass

    # === L1: Working Context ===

    def build_working_context(
        self,
        system_prompt: str,
        today_input: dict,
        weekly_context: Optional[str] = None,
        rag_results: Optional[List[str]] = None
    ) -> WorkingContext:
        """构建工作上下文"""
        pass
```

### 4.3 RAGService (知识检索服务)

```python
# backend/app/services/rag_service.py

class RAGService:
    """
    RAG 知识检索服务

    职责:
    1. 文档向量化和检索
    2. 按生育期/异常类型检索
    3. 构建 RAG 增强的回答
    """

    def __init__(self, index_path: str = "data/rag_index"):
        self.embedder = Embedder()
        self.retriever = Retriever(index_path)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> List[RetrievalResult]:
        """通用检索"""
        pass

    async def search_by_growth_stage(
        self,
        growth_stage: str,
        top_k: int = 3
    ) -> List[RetrievalResult]:
        """按生育期检索相关知识"""
        pass

    async def search_by_anomaly(
        self,
        anomaly_type: str,
        severity: str = "mild"
    ) -> List[RetrievalResult]:
        """按异常类型检索处理建议"""
        pass

    async def build_augmented_answer(
        self,
        question: str,
        context: dict,
        llm_service: LLMService
    ) -> RAGAnswer:
        """构建 RAG 增强的回答"""
        pass
```

### 4.4 PlantResponseGenerator (长势评估生成器)

```python
# backend/app/services/llm_service.py (增强)

class LLMService:
    # ... 现有方法 ...

    async def generate_plant_response(
        self,
        image_today_b64: str,
        image_yesterday_b64: Optional[str],
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        env_data: Optional[dict] = None,
        is_cold_start: bool = False
    ) -> PlantResponseResult:
        """
        生成 PlantResponse

        Args:
            image_today_b64: 今日图片 Base64
            image_yesterday_b64: 昨日图片 Base64 (冷启动时为 None)
            yolo_today: 今日 YOLO 指标
            yolo_yesterday: 昨日 YOLO 指标 (冷启动时为 None)
            env_data: 环境数据
            is_cold_start: 是否为冷启动

        Returns:
            PlantResponseResult: 结构化的长势评估结果
        """
        if is_cold_start:
            return await self._generate_cold_start_response(
                image_today_b64, yolo_today, env_data
            )
        else:
            return await self._generate_comparison_response(
                image_today_b64, image_yesterday_b64,
                yolo_today, yolo_yesterday, env_data
            )

    async def _generate_comparison_response(self, ...) -> PlantResponseResult:
        """生成对比分析 (今日 vs 昨日)"""
        system_prompt = self._build_comparison_system_prompt()
        user_prompt = self._build_comparison_user_prompt(
            yolo_today, yolo_yesterday, env_data
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "## 昨日图像"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_yesterday_b64}"}},
                    {"type": "text", "text": "## 今日图像"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_today_b64}"}},
                    {"type": "text", "text": user_prompt}
                ]
            }
        ]

        response = await self._call_api(messages, model=MODEL_VISION)
        return self._parse_plant_response(response)

    async def _generate_cold_start_response(self, ...) -> PlantResponseResult:
        """生成单日分析 (冷启动)"""
        system_prompt = self._build_cold_start_system_prompt()
        # ... 类似实现，但只分析单张图片
        pass
```

---

## 5. 数据结构设计

### 5.1 请求/响应模型

```python
# backend/app/models/schemas.py (新增)

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# === 枚举 ===

class TrendType(str, Enum):
    BETTER = "better"
    SAME = "same"
    WORSE = "worse"

class SeverityType(str, Enum):
    NONE = "none"
    MILD = "mild"
    SEVERE = "severe"

class GrowthStageType(str, Enum):
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MIXED = "mixed"

class PredictionSource(str, Enum):
    TSMIXER = "tsmixer"
    OVERRIDE = "override"
    SANITY_ADJUSTED = "sanity_adjusted"
    FALLBACK = "fallback"

# === 请求模型 ===

class PredictOptions(BaseModel):
    run_sanity_check: bool = True
    use_rag: bool = True
    save_episode: bool = True
    save_response: bool = True

class DailyPredictRequest(BaseModel):
    date: str  # YYYY-MM-DD
    image_base64: Optional[str] = None  # 如果不传，从 data/images/ 读取
    env_data: Optional[dict] = None
    options: Optional[PredictOptions] = None

class KnowledgeQueryRequest(BaseModel):
    question: str
    context: Optional[dict] = None
    top_k: int = 5

class WeeklyGenerateRequest(BaseModel):
    week_start: str  # YYYY-MM-DD
    week_end: str

# === 响应模型 ===

class Evidence(BaseModel):
    leaf_observation: str
    flower_observation: str
    fruit_observation: str
    terminal_bud_observation: Optional[str] = None

class Abnormalities(BaseModel):
    wilting: SeverityType = SeverityType.NONE
    yellowing: SeverityType = SeverityType.NONE
    pest_damage: SeverityType = SeverityType.NONE
    other: Optional[str] = None

class Comparison(BaseModel):
    leaf_area_change: str
    leaf_count_change: str
    flower_count_change: str
    fruit_count_change: str
    overall_vigor_change: str

class PlantResponseResult(BaseModel):
    trend: Optional[TrendType] = None  # 冷启动时为 None
    confidence: float
    evidence: Evidence
    abnormalities: Abnormalities
    growth_stage: GrowthStageType
    comparison: Optional[Comparison] = None  # 冷启动时为 None
    is_cold_start: bool = False

class SanityCheckResult(BaseModel):
    is_consistent: bool
    confidence: float
    adjusted_value: float
    reason: str
    rag_used: bool = False

class RAGReference(BaseModel):
    doc_id: str
    title: Optional[str] = None
    snippet: str
    relevance: float

class YOLOMetrics(BaseModel):
    leaf_instance_count: float
    leaf_average_mask: float
    flower_instance_count: float
    flower_mask_pixel_count: float
    terminal_average_mask: float
    fruit_mask_average: float
    all_leaf_mask: float

class DailyPredictResult(BaseModel):
    date: str
    irrigation_amount: float
    source: PredictionSource
    is_cold_start: bool = False

    yolo_metrics: Optional[YOLOMetrics] = None
    plant_response: Optional[PlantResponseResult] = None
    sanity_check: Optional[SanityCheckResult] = None
    rag_references: List[RAGReference] = []

    warnings: List[str] = []
    suggestions: List[str] = []

    episode_id: Optional[str] = None
    response_saved_path: Optional[str] = None

class RAGAnswer(BaseModel):
    answer: str
    references: List[RAGReference]
    model: str
```

### 5.2 Episode 数据结构

```python
# 基于现有 src/cucumber_irrigation/models/episode.py

@dataclass
class Episode:
    date: str  # YYYY-MM-DD

    # 输入
    inputs: EpisodeInputs = field(default_factory=EpisodeInputs)

    # 预测
    predictions: EpisodePredictions = field(default_factory=EpisodePredictions)

    # LLM 输出
    llm_outputs: EpisodeLLMOutputs = field(default_factory=EpisodeLLMOutputs)

    # 异常
    anomalies: EpisodeAnomalies = field(default_factory=EpisodeAnomalies)

    # 最终决策
    final_decision: FinalDecision = field(default_factory=FinalDecision)

    # 知识引用
    knowledge_references: List[dict] = field(default_factory=list)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None

@dataclass
class EpisodeLLMOutputs:
    """LLM 输出 (新增)"""
    plant_response: Optional[dict] = None
    sanity_check: Optional[dict] = None
    is_cold_start: bool = False
```

---

## 6. API 接口设计

### 6.1 POST /api/predict/daily

**完整的每日预测接口**

```python
# backend/app/api/v1/predict.py

from fastapi import APIRouter, HTTPException
from app.models.schemas import DailyPredictRequest, DailyPredictResult
from app.services.prediction_service import prediction_service

router = APIRouter()

@router.post("/daily", response_model=DailyPredictResult)
async def predict_daily(request: DailyPredictRequest):
    """
    执行完整的每日预测流程

    流程:
    1. 保存/获取图片
    2. YOLO 推理
    3. 查找昨日图片 (冷启动检测)
    4. TSMixer 预测
    5. 生育期检测
    6. RAG 检索 (可选)
    7. 构建 Working Context
    8. 生成 PlantResponse
    9. SanityCheck (可选)
    10. 创建 Episode
    11. 保存结果
    """
    try:
        result = await prediction_service.predict_daily(
            date=request.date,
            image_base64=request.image_base64,
            env_data=request.env_data,
            options=request.options
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/response/{date}")
async def get_plant_response(date: str):
    """获取指定日期的 PlantResponse"""
    pass


@router.get("/episode/{date}")
async def get_episode(date: str):
    """获取指定日期的 Episode"""
    pass
```

### 6.2 POST /api/knowledge/query

**RAG 增强问答接口**

```python
# backend/app/api/v1/knowledge.py (增强)

@router.post("/query")
async def query_knowledge(request: KnowledgeQueryRequest):
    """
    RAG 增强问答

    流程:
    1. 向量检索相关文档
    2. 构建增强 Prompt
    3. 调用 LLM 生成回答
    4. 返回答案 + 引用
    """
    try:
        answer = await rag_service.build_augmented_answer(
            question=request.question,
            context=request.context,
            llm_service=llm_service
        )
        return create_response(answer.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 6.3 POST /api/weekly/generate

**周报生成接口**

```python
# backend/app/api/v1/weekly.py (增强)

@router.post("/generate")
async def generate_weekly_summary(request: WeeklyGenerateRequest):
    """
    生成周度总结

    流程:
    1. 获取本周 Episodes
    2. 统计趋势、灌水量、异常
    3. 调用 LLM 生成洞察
    4. 保存 Weekly Summary
    5. 生成 prompt_block
    """
    try:
        summary = await weekly_service.generate(
            week_start=request.week_start,
            week_end=request.week_end
        )
        return create_response(summary.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 7. 前端组件设计

### 7.1 PlantResponse 展示组件

```
frontend/src/components/
├── PlantResponseCard/
│   ├── PlantResponseCard.tsx      # 主组件
│   ├── PlantResponseCard.css
│   ├── TrendBadge.tsx             # 趋势标签 (better/same/worse)
│   ├── ConfidenceBar.tsx          # 置信度进度条
│   ├── EvidenceList.tsx           # 证据列表
│   ├── AbnormalityAlert.tsx       # 异常警告
│   └── index.ts
```

**PlantResponseCard 结构**:

```tsx
interface PlantResponseCardProps {
  response: PlantResponseResult;
  isLoading?: boolean;
  isColdStart?: boolean;
}

function PlantResponseCard({ response, isLoading, isColdStart }: PlantResponseCardProps) {
  return (
    <Card className="plant-response-card">
      <Card.Header>
        <h3>长势评估</h3>
        {isColdStart && <Badge variant="warning">首日分析</Badge>}
      </Card.Header>

      <Card.Body>
        {/* 趋势 + 置信度 */}
        <div className="trend-section">
          <TrendBadge trend={response.trend} />
          <ConfidenceBar value={response.confidence} />
        </div>

        {/* 生育期 */}
        <div className="growth-stage">
          <span>生育期: {response.growth_stage}</span>
        </div>

        {/* 证据观察 */}
        <EvidenceList evidence={response.evidence} />

        {/* 异常警告 */}
        {hasAbnormalities(response.abnormalities) && (
          <AbnormalityAlert abnormalities={response.abnormalities} />
        )}

        {/* 对比变化 (非冷启动) */}
        {!isColdStart && response.comparison && (
          <ComparisonTable comparison={response.comparison} />
        )}
      </Card.Body>
    </Card>
  );
}
```

### 7.2 图像对比组件

```
frontend/src/components/
├── ImageCompare/
│   ├── ImageCompare.tsx           # 主组件
│   ├── ImageCompare.css
│   ├── SideBySideView.tsx         # 左右对比
│   ├── SliderView.tsx             # 滑动对比
│   ├── MetricsDiff.tsx            # YOLO 指标差异
│   └── index.ts
```

### 7.3 RAG 引用组件

```
frontend/src/components/
├── RAGReferences/
│   ├── RAGReferences.tsx          # 引用列表
│   ├── RAGReferences.css
│   ├── ReferenceCard.tsx          # 单个引用卡片
│   ├── RelevanceScore.tsx         # 相关度显示
│   └── index.ts
```

---

## 8. 依赖管理

### 8.1 后端依赖 (backend/pyproject.toml)

```toml
[project]
name = "agriagent-backend"
version = "0.2.0"
requires-python = ">=3.10"

dependencies = [
    # === 现有依赖 ===
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.6",
    "openai>=1.12.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "openpyxl>=3.1.0",

    # === 新增依赖 ===
    # 无需新增，现有依赖已满足
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]
```

### 8.2 核心模块依赖 (src/cucumber_irrigation/)

```toml
# 已有依赖，无需修改
[project]
dependencies = [
    "openai>=1.12.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "torch>=2.0.0",
    "ultralytics>=8.0.0",
    "loguru>=0.7.0",
    "pyyaml>=6.0.0",
    "tiktoken>=0.5.0",  # Token 计数
    "sentence-transformers>=2.2.0",  # RAG Embedding
]
```

### 8.3 前端依赖 (frontend/package.json)

```json
{
  "dependencies": {
    // === 现有依赖 ===
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "@tanstack/react-query": "^5.17.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "clsx": "^2.1.0",
    "dayjs": "^1.11.10",
    "react-hot-toast": "^2.4.1",

    // === 新增依赖 ===
    "react-compare-image": "^3.4.0"  // 图像对比滑块
  }
}
```

### 8.4 依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  react-compare-image ← ImageCompare 组件                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                                                                  │
│  openai ←─────── LLMService                                     │
│  pandas ←─────── DataProcessing                                 │
│  pydantic ←───── Schemas                                        │
│                                                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ import
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Core Modules (cucumber_irrigation)              │
│                                                                  │
│  torch ←─────────── TSMixerService                              │
│  ultralytics ←───── YOLOService                                 │
│  tiktoken ←──────── TokenCounter (BudgetController)             │
│  sentence-transformers ←── Embedder (RAG)                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. 文件结构变更

### 9.1 新增文件

```
backend/app/
├── api/v1/
│   └── predict.py                    # [新增] 每日预测 API
│
├── services/
│   ├── prediction_service.py         # [新增] 预测编排服务
│   ├── memory_service.py             # [新增] 记忆层封装
│   └── rag_service.py                # [新增] RAG 服务封装
│
└── models/
    └── schemas.py                    # [增强] 新增请求/响应模型

frontend/src/
├── components/
│   ├── PlantResponseCard/            # [新增] 长势评估展示
│   ├── ImageCompare/                 # [新增] 图像对比
│   └── RAGReferences/                # [新增] RAG 引用展示
│
├── hooks/
│   ├── useDailyPredict.ts            # [新增] 每日预测 Hook
│   └── useRAGQuery.ts                # [新增] RAG 查询 Hook
│
└── services/
    └── predictService.ts             # [新增] 预测服务 API
```

### 9.2 修改文件

```
backend/app/
├── api/v1/
│   ├── knowledge.py                  # [修改] 添加 /query 端点
│   └── weekly.py                     # [修改] 添加 /generate 端点
│
├── services/
│   └── llm_service.py                # [修改] 添加 generate_plant_response
│
└── main.py                           # [修改] 注册新路由

frontend/src/
├── pages/
│   ├── DailyDecision.tsx             # [修改] 集成 PlantResponseCard
│   └── Knowledge.tsx                 # [修改] 添加 RAG 引用显示
│
└── services/
    └── api.ts                        # [修改] 添加新接口
```

---

## 10. 实现计划

### Phase 1: 核心功能 (P0) - 预计 2-3 天

| 任务 | 文件 | 复杂度 | 依赖 |
|------|------|--------|------|
| 1.1 创建 prediction_service.py | backend/app/services/ | 高 | - |
| 1.2 实现 generate_plant_response | backend/app/services/llm_service.py | 中 | - |
| 1.3 实现冷启动处理 | prediction_service.py | 中 | 1.2 |
| 1.4 创建 memory_service.py | backend/app/services/ | 中 | - |
| 1.5 创建 predict.py API | backend/app/api/v1/ | 中 | 1.1, 1.2, 1.3, 1.4 |
| 1.6 集成 SanityCheck | prediction_service.py | 低 | 1.5 |

### Phase 2: 记忆系统 (P1) - 预计 1-2 天

| 任务 | 文件 | 复杂度 | 依赖 |
|------|------|--------|------|
| 2.1 创建 rag_service.py | backend/app/services/ | 中 | - |
| 2.2 增强 knowledge.py | backend/app/api/v1/ | 低 | 2.1 |
| 2.3 增强 weekly.py | backend/app/api/v1/ | 中 | 1.4 |
| 2.4 Working Context 注入 | prediction_service.py | 低 | 2.3 |

### Phase 3: 前端增强 (P2) - 预计 1-2 天

| 任务 | 文件 | 复杂度 | 依赖 |
|------|------|--------|------|
| 3.1 PlantResponseCard 组件 | frontend/src/components/ | 中 | Phase 1 |
| 3.2 ImageCompare 组件 | frontend/src/components/ | 中 | - |
| 3.3 RAGReferences 组件 | frontend/src/components/ | 低 | Phase 2 |
| 3.4 DailyDecision 页面集成 | frontend/src/pages/ | 中 | 3.1, 3.2 |
| 3.5 Knowledge 页面增强 | frontend/src/pages/ | 低 | 3.3 |

---

## 11. 测试策略

### 11.1 单元测试

```python
# tests/test_prediction_service.py

@pytest.mark.asyncio
async def test_predict_daily_with_yesterday():
    """测试正常预测流程 (有昨日图片)"""
    pass

@pytest.mark.asyncio
async def test_predict_daily_cold_start():
    """测试冷启动流程 (无昨日图片)"""
    pass

@pytest.mark.asyncio
async def test_sanity_check_consistent():
    """测试 SanityCheck 一致情况"""
    pass

@pytest.mark.asyncio
async def test_sanity_check_inconsistent():
    """测试 SanityCheck 不一致情况"""
    pass
```

### 11.2 集成测试

```python
# tests/test_api_predict.py

@pytest.mark.asyncio
async def test_predict_daily_api():
    """测试 /api/predict/daily 端点"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/predict/daily", json={
            "date": "2024-05-30"
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert "irrigation_amount" in data
        assert "plant_response" in data
```

### 11.3 验收测试

| 测试场景 | 预期结果 |
|----------|----------|
| 上传 0530.jpg | 返回 PlantResponse (对比 0529) |
| 上传 0314.jpg (首日) | 返回冷启动分析 |
| 调用 /weekly/generate | 生成周摘要 + prompt_block |
| Knowledge 页面提问 | 返回答案 + 引用来源 |

---

## 12. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| LLM API 调用失败 | 中 | 高 | 重试机制 + 回退到默认值 |
| 单次预测耗时过长 | 中 | 中 | 异步处理 + 进度反馈 |
| 冷启动分析质量差 | 低 | 中 | 提示用户连续上传 |
| RAG 检索相关性低 | 中 | 低 | 优化 Embedding + 过滤阈值 |

---

## 附录 A: Prompt 模板

### A.1 PlantResponse 对比分析 Prompt

```
你是一个温室黄瓜长势评估专家。

任务：对比分析昨日与今日的黄瓜植株图像，评估长势变化。

输入：
1. 昨日图像 + YOLO 指标
2. 今日图像 + YOLO 指标
3. 今日环境数据

输出格式 (JSON)：
{
  "trend": "better | same | worse",
  "confidence": 0.0-1.0,
  "evidence": {
    "leaf_observation": "叶片观察...",
    "flower_observation": "花朵观察...",
    "fruit_observation": "果实观察...",
    "terminal_bud_observation": "顶芽观察..."
  },
  "abnormalities": {
    "wilting": "none | mild | severe",
    "yellowing": "none | mild | severe",
    "pest_damage": "none | mild | severe",
    "other": null 或 "描述"
  },
  "growth_stage": "vegetative | flowering | fruiting | mixed",
  "comparison": {
    "leaf_area_change": "增加 | 减少 | 持平",
    "leaf_count_change": "增加 | 减少 | 持平",
    "flower_count_change": "增加 | 减少 | 持平",
    "fruit_count_change": "增加 | 减少 | 持平",
    "overall_vigor_change": "增加 | 减少 | 持平"
  }
}

判断规则：
- 有明显病害/萎蔫 → trend = "worse"
- 叶片 mask 增长率 > 平均 → trend = "better"
- 叶片 mask 增长率 ≈ 平均 → trend = "same"
- 叶片 mask 增长率 < 平均 → trend = "worse"
```

### A.2 冷启动单日分析 Prompt

```
你是一个温室黄瓜长势评估专家。

任务：分析单张黄瓜植株图像，描述当前状态。

注意：这是首次分析，没有历史对比数据。

输入：
1. 今日图像 + YOLO 指标
2. 今日环境数据

输出格式 (JSON)：
{
  "trend": null,  // 无法判断趋势
  "confidence": 0.0-1.0,
  "evidence": {
    "leaf_observation": "叶片观察...",
    "flower_observation": "花朵观察...",
    "fruit_observation": "果实观察...",
    "terminal_bud_observation": "顶芽观察..."
  },
  "abnormalities": {...},
  "growth_stage": "vegetative | flowering | fruiting | mixed",
  "comparison": null,  // 无法对比
  "is_cold_start": true,
  "current_state_summary": "当前植株整体状态良好..."
}
```

---

> 文档结束
