# 温室黄瓜灌水智能体系统 - 功能补充开发任务

> 版本：v1.0
> 创建日期：2024-12-27
> 基于：requirements_27bu.md, design_27bu.md
> 文档状态：任务分解完成，待开发

---

## 任务概览

| Phase | 名称 | 任务数 | 预估工时 | 优先级 |
|-------|------|--------|----------|--------|
| Phase 1 | 核心功能 | 12 | 16-20h | P0 |
| Phase 2 | 记忆系统 | 8 | 8-12h | P1 |
| Phase 3 | 前端增强 | 10 | 10-14h | P2 |
| **合计** | - | **30** | **34-46h** | - |

---

## Phase 1: 核心功能 (P0)

### 目标
实现完整的每日预测流程，包括 PlantResponse 自动生成、冷启动处理、SanityCheck 和 Episode 存储。

---

### T1.1 创建请求/响应数据模型

**描述**：定义 API 所需的 Pydantic 模型，包括枚举、请求体、响应体。

**文件位置**：`backend/app/models/schemas.py`

**输入**：design_27bu.md 5.1 节数据结构设计

**输出**：
```python
# 枚举
- TrendType (better/same/worse)
- SeverityType (none/mild/severe)
- GrowthStageType (vegetative/flowering/fruiting/mixed)
- PredictionSource (tsmixer/override/sanity_adjusted/fallback)

# 请求模型
- PredictOptions
- DailyPredictRequest
- KnowledgeQueryRequest
- WeeklyGenerateRequest

# 响应模型
- Evidence
- Abnormalities
- Comparison
- PlantResponseResult
- SanityCheckResult
- RAGReference
- YOLOMetrics
- DailyPredictResult
- RAGAnswer
```

**依赖**：无

**验收标准**：
- [ ] 所有模型定义完成
- [ ] 类型注解完整
- [ ] 默认值合理
- [ ] 可通过 `from app.models.schemas import *` 导入

**预估工时**：1.5h

---

### T1.2 创建 MemoryService 记忆层封装

**描述**：封装 Episode 和 WeeklySummary 的存储操作，提供统一接口。

**文件位置**：`backend/app/services/memory_service.py`

**输入**：
- `src/cucumber_irrigation/memory/episode_store.py`
- `src/cucumber_irrigation/memory/weekly_summary_store.py`
- `src/cucumber_irrigation/memory/working_context.py`

**输出**：
```python
class MemoryService:
    # 构造函数
    __init__(storage_path, use_mongodb)

    # L2: Episode 操作
    async save_episode(episode) -> str
    async get_episode(date) -> Optional[Episode]
    async get_recent_episodes(days) -> List[Episode]
    async update_episode(date, updates) -> bool

    # L3: Weekly Summary 操作
    async save_weekly_summary(summary) -> str
    async get_latest_weekly_summary() -> Optional[WeeklySummary]
    async get_weekly_prompt_block() -> Optional[str]

    # L1: Working Context
    build_working_context(system_prompt, today_input, weekly_context, rag_results) -> WorkingContext
```

**依赖**：T1.1

**验收标准**：
- [ ] 支持 JSON 文件存储
- [ ] 支持 MongoDB 存储（可选）
- [ ] Episode CRUD 操作正常
- [ ] Weekly Summary 操作正常
- [ ] Working Context 构建正确

**预估工时**：2h

---

### T1.3 增强 LLMService - 添加 generate_plant_response

**描述**：在现有 LLMService 中添加 PlantResponse 生成方法，支持对比分析和冷启动分析。

**文件位置**：`backend/app/services/llm_service.py`

**输入**：
- design_27bu.md 附录 A Prompt 模板
- 现有 `analyze_image` 方法参考

**输出**：
```python
class LLMService:
    # 现有方法保持不变...

    # 新增方法
    async generate_plant_response(
        image_today_b64: str,
        image_yesterday_b64: Optional[str],
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        env_data: Optional[dict],
        is_cold_start: bool
    ) -> PlantResponseResult

    # 内部方法
    async _generate_comparison_response(...) -> PlantResponseResult
    async _generate_cold_start_response(...) -> PlantResponseResult
    def _build_comparison_system_prompt() -> str
    def _build_comparison_user_prompt(yolo_today, yolo_yesterday, env_data) -> str
    def _build_cold_start_system_prompt() -> str
    def _parse_plant_response(response: str) -> PlantResponseResult
```

**依赖**：T1.1

**验收标准**：
- [ ] 对比分析输出正确的 JSON 结构
- [ ] 冷启动分析输出正确的 JSON 结构
- [ ] Prompt 模板符合设计文档
- [ ] 错误处理完善（JSON 解析失败时返回默认值）
- [ ] 支持流式和非流式两种模式

**预估工时**：2.5h

---

### T1.4 增强 LLMService - 添加 sanity_check

**描述**：在 LLMService 中添加 SanityCheck 方法，验证 TSMixer 预测与 PlantResponse 的一致性。

**文件位置**：`backend/app/services/llm_service.py`

**输入**：
- `src/cucumber_irrigation/services/llm_service.py` 中的 `sanity_check` 方法
- design_27bu.md SanityCheckResult 模型

**输出**：
```python
class LLMService:
    # 新增方法
    async sanity_check(
        tsmixer_prediction: float,
        plant_response: dict,
        env_data: dict,
        weekly_context: Optional[str],
        rag_advice: Optional[str]
    ) -> SanityCheckResult

    # 内部方法
    def _build_sanity_check_system_prompt(weekly_context) -> str
    def _build_sanity_check_user_prompt(prediction, response, env, rag) -> str
```

**依赖**：T1.1, T1.3

**验收标准**：
- [ ] 一致性判断逻辑正确
- [ ] 返回调整建议
- [ ] 支持周摘要上下文注入
- [ ] 支持 RAG 建议注入

**预估工时**：1.5h

---

### T1.5 创建 PredictionService 预测编排服务

**描述**：创建核心预测编排服务，协调 YOLO、TSMixer、LLM 等服务，实现完整预测流程。

**文件位置**：`backend/app/services/prediction_service.py`

**输入**：
- design_27bu.md 4.1 节 PredictionService 设计
- 现有 yolo_service, tsmixer_service, llm_service

**输出**：
```python
class PredictionService:
    __init__(yolo_service, tsmixer_service, llm_service, memory_service, rag_service)

    # 主方法
    async predict_daily(
        date: str,
        image_path: Optional[str],
        image_base64: Optional[str],
        env_data: Optional[dict],
        options: Optional[PredictOptions]
    ) -> DailyPredictResult

    # 步骤方法
    async _save_or_get_image(date, image_base64) -> str
    async _run_yolo(image_path) -> dict
    async _find_yesterday_image(date) -> Optional[str]
    async _get_yesterday_yolo(yesterday_path) -> Optional[dict]
    async _run_tsmixer(date, env_data) -> float
    async _detect_growth_stage(image_path) -> str
    async _retrieve_knowledge(growth_stage) -> List[RAGReference]
    async _generate_plant_response(...) -> PlantResponseResult
    async _run_sanity_check(...) -> SanityCheckResult
    async _create_episode(...) -> Episode
    async _save_plant_response(date, response) -> str

# 单例
prediction_service = PredictionService(...)
```

**依赖**：T1.2, T1.3, T1.4

**验收标准**：
- [ ] 完整流程可执行
- [ ] 各步骤错误隔离
- [ ] 支持跳过可选步骤
- [ ] 返回完整的 DailyPredictResult
- [ ] 日志记录完善

**预估工时**：3h

---

### T1.6 实现冷启动处理逻辑

**描述**：在 PredictionService 中实现冷启动检测和处理，支持单张图片分析。

**文件位置**：`backend/app/services/prediction_service.py`

**输入**：
- design_27bu.md 冷启动处理流程
- requirements_27bu.md 4.1.2 节

**输出**：
```python
class PredictionService:
    # 冷启动相关方法
    def _check_cold_start(self, yesterday_path: Optional[str]) -> bool

    async _find_yesterday_image(self, date: str) -> Optional[str]:
        """
        查找昨日图片
        - 优先查找 date-1
        - 如果不存在，尝试 date-2, date-3 (最多回溯 3 天)
        - 全部不存在则返回 None (冷启动)
        """
        pass

    async _handle_cold_start(self, date, image_path, yolo_today, env_data) -> PlantResponseResult:
        """冷启动时的处理逻辑"""
        pass
```

**依赖**：T1.5

**验收标准**：
- [ ] 正确识别冷启动情况
- [ ] 支持日期回溯查找
- [ ] 冷启动时 trend 为 None
- [ ] 冷启动时 is_cold_start = True
- [ ] 前端可识别冷启动状态

**预估工时**：1h

---

### T1.7 创建 predict.py API 路由

**描述**：创建 `/api/predict/` 路由，暴露每日预测端点。

**文件位置**：`backend/app/api/v1/predict.py`

**输入**：
- design_27bu.md 6.1 节 API 设计
- T1.5 PredictionService

**输出**：
```python
router = APIRouter()

@router.post("/daily", response_model=DailyPredictResult)
async def predict_daily(request: DailyPredictRequest):
    """完整的每日预测流程"""
    pass

@router.get("/response/{date}")
async def get_plant_response(date: str):
    """获取指定日期的 PlantResponse"""
    pass

@router.get("/episode/{date}")
async def get_episode(date: str):
    """获取指定日期的 Episode"""
    pass

@router.get("/responses")
async def list_plant_responses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """列出 PlantResponse 文件"""
    pass
```

**依赖**：T1.5, T1.6

**验收标准**：
- [ ] POST /api/predict/daily 可用
- [ ] GET /api/predict/response/{date} 可用
- [ ] GET /api/predict/episode/{date} 可用
- [ ] 错误响应格式统一
- [ ] Swagger 文档正确

**预估工时**：1.5h

---

### T1.8 注册路由到 main.py

**描述**：将新的 predict 路由注册到 FastAPI 应用。

**文件位置**：`backend/app/main.py`

**输入**：T1.7

**输出**：
```python
from app.api.v1 import predict

app.include_router(predict.router, prefix="/api/predict", tags=["Predict"])
```

**依赖**：T1.7

**验收标准**：
- [ ] /api/predict/daily 可访问
- [ ] /docs 中显示 Predict 标签
- [ ] 无导入错误

**预估工时**：0.5h

---

### T1.9 创建 PlantResponse 保存逻辑

**描述**：实现 PlantResponse 保存到 `output/responses/` 目录。

**文件位置**：`backend/app/services/prediction_service.py`

**输入**：
- 现有 `output/responses/*.json` 格式参考
- design_27bu.md PlantResponseResult 模型

**输出**：
```python
async def _save_plant_response(
    self,
    date: str,
    plant_response: PlantResponseResult,
    yolo_today: dict,
    yolo_yesterday: Optional[dict],
    env_data: dict,
    image_today_path: str,
    image_yesterday_path: Optional[str]
) -> str:
    """
    保存 PlantResponse 到 output/responses/{date}.json

    JSON 结构:
    {
        "date": "2024-05-30",
        "created_at": "2025-12-27T...",
        "prompt_version": "v2",
        "image_today": "path/to/0530.jpg",
        "image_yesterday": "path/to/0529.jpg",
        "yolo_today": {...},
        "yolo_yesterday": {...},
        "env_today": {...},
        "response": {...},
        "is_cold_start": false,
        "raw_response": "..."
    }
    """
    pass
```

**依赖**：T1.5

**验收标准**：
- [ ] JSON 文件格式与现有一致
- [ ] 包含完整元数据
- [ ] 文件名为 `{date}.json`
- [ ] 支持覆盖已存在文件

**预估工时**：1h

---

### T1.10 创建 Episode 自动生成逻辑

**描述**：在预测完成后自动创建 Episode 并保存。

**文件位置**：`backend/app/services/prediction_service.py`

**输入**：
- `src/cucumber_irrigation/models/episode.py`
- design_27bu.md 5.2 节 Episode 数据结构

**输出**：
```python
async def _create_episode(
    self,
    date: str,
    result: DailyPredictResult,
    env_data: dict,
    yolo_today: dict,
    override_value: Optional[float] = None,
    override_reason: Optional[str] = None
) -> Episode:
    """
    创建 Episode 对象

    包含:
    - inputs (environment, yolo_metrics)
    - predictions (tsmixer_raw, growth_stage)
    - llm_outputs (plant_response, sanity_check, is_cold_start)
    - anomalies (如有)
    - final_decision (value, source, override_reason)
    - knowledge_references
    """
    pass
```

**依赖**：T1.2, T1.5

**验收标准**：
- [ ] Episode 结构完整
- [ ] 自动保存到 MemoryService
- [ ] 支持 Override 更新
- [ ] 时间戳正确

**预估工时**：1h

---

### T1.11 服务初始化与依赖注入

**描述**：创建服务实例，配置依赖注入。

**文件位置**：
- `backend/app/services/__init__.py`
- `backend/app/core/dependencies.py` (新建)

**输入**：T1.2 ~ T1.5 所有服务

**输出**：
```python
# backend/app/services/__init__.py
from .yolo_service import yolo_service
from .tsmixer_service import tsmixer_service
from .llm_service import llm_service
from .memory_service import MemoryService, memory_service
from .prediction_service import PredictionService, prediction_service

# backend/app/core/dependencies.py
def get_prediction_service() -> PredictionService:
    return prediction_service

def get_memory_service() -> MemoryService:
    return memory_service
```

**依赖**：T1.2 ~ T1.5

**验收标准**：
- [ ] 所有服务可正确导入
- [ ] 服务单例正确创建
- [ ] FastAPI 依赖注入可用

**预估工时**：0.5h

---

### T1.12 Phase 1 集成测试

**描述**：编写集成测试，验证完整预测流程。

**文件位置**：`backend/tests/test_predict.py`

**输入**：Phase 1 所有任务

**输出**：
```python
# 测试用例
test_predict_daily_with_yesterday()      # 正常预测
test_predict_daily_cold_start()          # 冷启动
test_predict_daily_with_override()       # 带 Override
test_predict_daily_sanity_inconsistent() # SanityCheck 不一致
test_get_plant_response()                # 获取 PlantResponse
test_get_episode()                       # 获取 Episode
```

**依赖**：T1.1 ~ T1.11

**验收标准**：
- [ ] 所有测试用例通过
- [ ] 覆盖正常流程
- [ ] 覆盖边界情况
- [ ] 覆盖错误情况

**预估工时**：1.5h

---

## Phase 2: 记忆系统集成 (P1)

### 目标
集成 RAG 知识检索、Weekly Summary 生成、Working Context 注入。

---

### T2.1 创建 RAGService 知识检索服务

**描述**：封装 RAG 检索功能，提供统一接口。

**文件位置**：`backend/app/services/rag_service.py`

**输入**：
- `src/cucumber_irrigation/rag/`
- `src/cucumber_irrigation/services/local_rag_service.py`

**输出**：
```python
class RAGService:
    __init__(index_path)

    # 通用检索
    async search(query, top_k, filters) -> List[RetrievalResult]

    # 场景化检索
    async search_by_growth_stage(growth_stage, top_k) -> List[RetrievalResult]
    async search_by_anomaly(anomaly_type, severity) -> List[RetrievalResult]

    # RAG 增强回答
    async build_augmented_answer(question, context, llm_service) -> RAGAnswer

    # 内部方法
    def _build_rag_prompt(question, retrieved_docs) -> str
    def _format_references(docs) -> List[RAGReference]

# 单例
rag_service = RAGService(...)
```

**依赖**：无

**验收标准**：
- [ ] 支持通用文本检索
- [ ] 支持按生育期检索
- [ ] 支持按异常类型检索
- [ ] 返回相关度评分
- [ ] 支持构建 RAG 增强回答

**预估工时**：2h

---

### T2.2 增强 knowledge.py - 添加 RAG 查询端点

**描述**：在现有 knowledge API 中添加 RAG 增强查询端点。

**文件位置**：`backend/app/api/v1/knowledge.py`

**输入**：
- T2.1 RAGService
- design_27bu.md 6.2 节 API 设计

**输出**：
```python
@router.post("/query")
async def query_knowledge(request: KnowledgeQueryRequest):
    """
    RAG 增强问答

    1. 向量检索相关文档
    2. 构建增强 Prompt
    3. 调用 LLM 生成回答
    4. 返回答案 + 引用
    """
    pass

@router.get("/search")
async def search_knowledge(
    query: str,
    top_k: int = 5,
    growth_stage: Optional[str] = None
):
    """直接检索，不生成回答"""
    pass
```

**依赖**：T2.1

**验收标准**：
- [ ] POST /api/knowledge/query 可用
- [ ] GET /api/knowledge/search 可用
- [ ] 返回引用来源
- [ ] 支持按生育期过滤

**预估工时**：1h

---

### T2.3 创建 WeeklyService 周报服务

**描述**：封装周度总结生成逻辑。

**文件位置**：`backend/app/services/weekly_service.py`

**输入**：
- `src/cucumber_irrigation/pipelines/weekly_pipeline.py`
- `src/cucumber_irrigation/services/llm_service.py` 中的 `generate_weekly_insights`

**输出**：
```python
class WeeklyService:
    __init__(memory_service, llm_service, rag_service)

    async generate(week_start, week_end) -> WeeklySummary:
        """
        生成周度总结

        1. 获取本周 Episodes
        2. 统计趋势、灌水量、异常
        3. 调用 LLM 生成洞察
        4. 生成 prompt_block
        5. 保存 Weekly Summary
        """
        pass

    async _get_week_episodes(start, end) -> List[Episode]
    async _calculate_statistics(episodes) -> dict
    async _generate_insights(episodes, stats) -> List[str]
    async _generate_prompt_block(summary) -> str

# 单例
weekly_service = WeeklyService(...)
```

**依赖**：T1.2

**验收标准**：
- [ ] 正确统计本周数据
- [ ] 生成有意义的洞察
- [ ] prompt_block 格式正确
- [ ] 保存到 MemoryService

**预估工时**：2h

---

### T2.4 增强 weekly.py - 添加生成端点

**描述**：在现有 weekly API 中添加周报生成端点。

**文件位置**：`backend/app/api/v1/weekly.py`

**输入**：
- T2.3 WeeklyService
- design_27bu.md 6.3 节 API 设计

**输出**：
```python
@router.post("/generate")
async def generate_weekly_summary(request: WeeklyGenerateRequest):
    """
    生成周度总结

    请求:
    {
        "week_start": "2024-05-27",
        "week_end": "2024-06-02"
    }

    响应:
    {
        "patterns": [...],
        "risk_triggers": [...],
        "overrides": [...],
        "statistics": {...},
        "prompt_block": "..."
    }
    """
    pass

@router.get("/prompt-block")
async def get_latest_prompt_block():
    """获取最新的 prompt_block 用于注入"""
    pass
```

**依赖**：T2.3

**验收标准**：
- [ ] POST /api/weekly/generate 可用
- [ ] GET /api/weekly/prompt-block 可用
- [ ] 生成结果保存成功

**预估工时**：1h

---

### T2.5 集成 Working Context 注入

**描述**：在 PredictionService 中集成 Working Context 构建和周摘要注入。

**文件位置**：`backend/app/services/prediction_service.py`

**输入**：
- T1.2 MemoryService.build_working_context
- T2.3 WeeklyService

**输出**：
```python
class PredictionService:
    async def _build_working_context(
        self,
        date: str,
        today_input: dict,
        rag_results: List[str]
    ) -> WorkingContext:
        """
        构建工作上下文

        1. 获取最新 weekly_prompt_block
        2. 调用 memory_service.build_working_context
        3. 返回带 token 预算的上下文
        """
        pass

    async def _inject_context_to_llm(
        self,
        context: WorkingContext,
        ...
    ):
        """将上下文注入 LLM 调用"""
        pass
```

**依赖**：T1.2, T1.5, T2.3

**验收标准**：
- [ ] 正确获取周摘要
- [ ] Working Context 构建正确
- [ ] Token 预算控制生效
- [ ] LLM 调用时注入上下文

**预估工时**：1h

---

### T2.6 集成 RAG 到预测流程

**描述**：在 PredictionService 中集成 RAG 检索，根据生育期和异常类型检索相关知识。

**文件位置**：`backend/app/services/prediction_service.py`

**输入**：T2.1 RAGService

**输出**：
```python
class PredictionService:
    async def _retrieve_knowledge(
        self,
        growth_stage: str,
        anomaly_type: Optional[str] = None
    ) -> List[RAGReference]:
        """
        检索相关知识

        1. 根据生育期检索
        2. 如有异常，追加异常相关检索
        3. 去重合并
        4. 返回 top_k 个结果
        """
        pass

    async def _build_rag_advice(
        self,
        references: List[RAGReference]
    ) -> str:
        """将检索结果格式化为建议文本"""
        pass
```

**依赖**：T1.5, T2.1

**验收标准**：
- [ ] 预测流程中调用 RAG
- [ ] 结果注入 Working Context
- [ ] DailyPredictResult 包含 rag_references
- [ ] SanityCheck 可使用 RAG 建议

**预估工时**：1h

---

### T2.7 服务注册与配置

**描述**：注册新服务，更新配置。

**文件位置**：
- `backend/app/services/__init__.py`
- `backend/app/core/config.py`

**输入**：T2.1 ~ T2.4

**输出**：
```python
# services/__init__.py
from .rag_service import rag_service
from .weekly_service import weekly_service

# config.py
class Settings:
    # RAG 配置
    RAG_INDEX_PATH: str = "data/rag_index"
    RAG_TOP_K: int = 5
    RAG_ENABLED: bool = True

    # Weekly 配置
    WEEKLY_AUTO_GENERATE: bool = False
```

**依赖**：T2.1 ~ T2.4

**验收标准**：
- [ ] 新服务可正确导入
- [ ] 配置项生效
- [ ] 支持禁用 RAG

**预估工时**：0.5h

---

### T2.8 Phase 2 集成测试

**描述**：编写 Phase 2 集成测试。

**文件位置**：`backend/tests/test_memory.py`

**输入**：Phase 2 所有任务

**输出**：
```python
test_rag_search()                    # RAG 检索
test_rag_query()                     # RAG 问答
test_weekly_generate()               # 周报生成
test_working_context_injection()     # 上下文注入
test_predict_with_rag()              # 预测 + RAG
```

**依赖**：T2.1 ~ T2.7

**验收标准**：
- [ ] 所有测试通过
- [ ] RAG 检索正常
- [ ] 周报生成正常

**预估工时**：1h

---

## Phase 3: 前端增强 (P2)

### 目标
实现 PlantResponse 展示、图像对比、RAG 引用显示。

---

### T3.1 创建 useDailyPredict Hook

**描述**：创建调用每日预测 API 的 React Hook。

**文件位置**：`frontend/src/hooks/useDailyPredict.ts`

**输入**：T1.7 predict API

**输出**：
```typescript
interface UseDailyPredictOptions {
  onSuccess?: (result: DailyPredictResult) => void;
  onError?: (error: Error) => void;
}

function useDailyPredict(options?: UseDailyPredictOptions) {
  // 返回
  return {
    predict: (request: DailyPredictRequest) => Promise<DailyPredictResult>,
    isLoading: boolean,
    error: Error | null,
    data: DailyPredictResult | null
  };
}

function usePlantResponse(date: string) {
  // 获取指定日期的 PlantResponse
  return {
    data: PlantResponseResult | null,
    isLoading: boolean,
    error: Error | null
  };
}
```

**依赖**：T1.7

**验收标准**：
- [ ] 支持调用预测 API
- [ ] 支持获取历史 PlantResponse
- [ ] 错误处理完善
- [ ] Loading 状态正确

**预估工时**：1h

---

### T3.2 创建 TrendBadge 组件

**描述**：创建趋势标签组件，显示 better/same/worse。

**文件位置**：`frontend/src/components/PlantResponseCard/TrendBadge.tsx`

**输入**：design_27bu.md TrendType

**输出**：
```typescript
interface TrendBadgeProps {
  trend: 'better' | 'same' | 'worse' | null;
  size?: 'sm' | 'md' | 'lg';
}

function TrendBadge({ trend, size = 'md' }: TrendBadgeProps) {
  // better: 绿色 + 上箭头
  // same: 灰色 + 横线
  // worse: 红色 + 下箭头
  // null: 黄色 + 问号 (冷启动)
}
```

**依赖**：无

**验收标准**：
- [ ] 三种趋势样式正确
- [ ] 冷启动状态样式正确
- [ ] 支持多种尺寸
- [ ] 动画效果平滑

**预估工时**：0.5h

---

### T3.3 创建 ConfidenceBar 组件

**描述**：创建置信度进度条组件。

**文件位置**：`frontend/src/components/PlantResponseCard/ConfidenceBar.tsx`

**输入**：无

**输出**：
```typescript
interface ConfidenceBarProps {
  value: number;  // 0-1
  showLabel?: boolean;
}

function ConfidenceBar({ value, showLabel = true }: ConfidenceBarProps) {
  // 进度条 + 百分比标签
  // 颜色: <0.5 红, 0.5-0.7 黄, >0.7 绿
}
```

**依赖**：无

**验收标准**：
- [ ] 进度条显示正确
- [ ] 颜色随数值变化
- [ ] 支持隐藏标签

**预估工时**：0.5h

---

### T3.4 创建 EvidenceList 组件

**描述**：创建证据列表组件，显示叶片/花朵/果实观察。

**文件位置**：`frontend/src/components/PlantResponseCard/EvidenceList.tsx`

**输入**：design_27bu.md Evidence 模型

**输出**：
```typescript
interface EvidenceListProps {
  evidence: Evidence;
  expandable?: boolean;
}

function EvidenceList({ evidence, expandable = true }: EvidenceListProps) {
  // 折叠式列表
  // - 叶片观察
  // - 花朵观察
  // - 果实观察
  // - 顶芽观察 (可选)
}
```

**依赖**：无

**验收标准**：
- [ ] 列表项正确显示
- [ ] 支持展开/折叠
- [ ] 空值处理正确
- [ ] 样式与设计一致

**预估工时**：1h

---

### T3.5 创建 AbnormalityAlert 组件

**描述**：创建异常警告组件。

**文件位置**：`frontend/src/components/PlantResponseCard/AbnormalityAlert.tsx`

**输入**：design_27bu.md Abnormalities 模型

**输出**：
```typescript
interface AbnormalityAlertProps {
  abnormalities: Abnormalities;
}

function AbnormalityAlert({ abnormalities }: AbnormalityAlertProps) {
  // 只显示非 none 的异常
  // mild: 黄色警告
  // severe: 红色警告
}
```

**依赖**：无

**验收标准**：
- [ ] 正确过滤无异常项
- [ ] 严重程度颜色正确
- [ ] 支持多个异常同时显示

**预估工时**：0.5h

---

### T3.6 创建 PlantResponseCard 主组件

**描述**：组合上述子组件，创建完整的 PlantResponse 卡片。

**文件位置**：`frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`

**输入**：T3.2 ~ T3.5

**输出**：
```typescript
interface PlantResponseCardProps {
  response: PlantResponseResult | null;
  isLoading?: boolean;
  onRefresh?: () => void;
}

function PlantResponseCard({ response, isLoading, onRefresh }: PlantResponseCardProps) {
  // 结构:
  // - Header (标题 + 冷启动标签)
  // - TrendBadge + ConfidenceBar
  // - 生育期显示
  // - EvidenceList
  // - AbnormalityAlert
  // - ComparisonTable (非冷启动)
}
```

**依赖**：T3.2 ~ T3.5

**验收标准**：
- [ ] 组件结构完整
- [ ] Loading 状态显示骨架屏
- [ ] 冷启动状态正确处理
- [ ] 样式与系统一致

**预估工时**：1.5h

---

### T3.7 创建 ImageCompare 组件

**描述**：创建图像对比组件，支持左右对比和滑动对比。

**文件位置**：`frontend/src/components/ImageCompare/ImageCompare.tsx`

**输入**：
- react-compare-image 库
- design_27bu.md 7.2 节

**输出**：
```typescript
interface ImageCompareProps {
  imageYesterday: string;  // URL
  imageToday: string;
  yoloYesterday?: YOLOMetrics;
  yoloToday?: YOLOMetrics;
  mode?: 'side-by-side' | 'slider';
}

function ImageCompare({ ... }: ImageCompareProps) {
  // 两种模式切换
  // 显示 YOLO 指标差异
}
```

**依赖**：react-compare-image

**验收标准**：
- [ ] 左右对比模式正常
- [ ] 滑动对比模式正常
- [ ] 模式切换平滑
- [ ] YOLO 指标差异显示

**预估工时**：1.5h

---

### T3.8 创建 RAGReferences 组件

**描述**：创建 RAG 引用显示组件。

**文件位置**：`frontend/src/components/RAGReferences/RAGReferences.tsx`

**输入**：design_27bu.md RAGReference 模型

**输出**：
```typescript
interface RAGReferencesProps {
  references: RAGReference[];
  maxDisplay?: number;
}

function RAGReferences({ references, maxDisplay = 3 }: RAGReferencesProps) {
  // 引用卡片列表
  // - 标题 (可选)
  // - 片段预览
  // - 相关度评分
  // - 展开查看完整
}
```

**依赖**：无

**验收标准**：
- [ ] 引用列表正确显示
- [ ] 相关度可视化
- [ ] 支持展开详情
- [ ] 空列表处理正确

**预估工时**：1h

---

### T3.9 集成 PlantResponseCard 到 DailyDecision 页面

**描述**：将 PlantResponseCard 集成到今日决策页面，替换静态 Agent Insights。

**文件位置**：`frontend/src/pages/DailyDecision.tsx`

**输入**：T3.1, T3.6

**输出**：
```typescript
function DailyDecision() {
  const { date } = useParams();
  const { data: response, isLoading } = usePlantResponse(date);

  return (
    <div>
      {/* 现有内容 */}

      {/* 替换 Agent Insights 区域 */}
      <PlantResponseCard
        response={response}
        isLoading={isLoading}
      />

      {/* 添加图像对比 */}
      {response && !response.is_cold_start && (
        <ImageCompare
          imageYesterday={...}
          imageToday={...}
          yoloYesterday={...}
          yoloToday={...}
        />
      )}
    </div>
  );
}
```

**依赖**：T3.1, T3.6, T3.7

**验收标准**：
- [ ] PlantResponseCard 显示正常
- [ ] 图像对比显示正常
- [ ] 冷启动状态正确处理
- [ ] 页面布局合理

**预估工时**：1.5h

---

### T3.10 集成 RAGReferences 到 Knowledge 页面

**描述**：在 Knowledge 页面添加 RAG 引用显示。

**文件位置**：`frontend/src/pages/Knowledge.tsx`

**输入**：T3.8

**输出**：
```typescript
function Knowledge() {
  // 现有聊天逻辑...

  const handleSendMessage = async (message: string) => {
    // 调用 RAG 查询 API
    const result = await ragQuery({ question: message });

    // 显示回答
    addMessage({
      role: 'assistant',
      content: result.answer,
      references: result.references  // 新增
    });
  };

  return (
    <div>
      {/* 聊天消息 */}
      {messages.map(msg => (
        <div>
          {msg.content}
          {msg.references && (
            <RAGReferences references={msg.references} />
          )}
        </div>
      ))}
    </div>
  );
}
```

**依赖**：T2.2, T3.8

**验收标准**：
- [ ] RAG 问答功能正常
- [ ] 引用显示在回答下方
- [ ] 支持展开查看引用详情

**预估工时**：1h

---

## 任务依赖关系图

```
Phase 1: 核心功能
==================================================

T1.1 数据模型
  │
  ├──▶ T1.2 MemoryService ──────────────────┐
  │                                          │
  ├──▶ T1.3 LLM generate_plant_response ────┼──▶ T1.5 PredictionService
  │                                          │         │
  └──▶ T1.4 LLM sanity_check ───────────────┘         │
                                                       │
                                                       ├──▶ T1.6 冷启动处理
                                                       │
                                                       ├──▶ T1.9 PlantResponse 保存
                                                       │
                                                       └──▶ T1.10 Episode 生成
                                                              │
                                                              ▼
                                              T1.7 predict.py API
                                                       │
                                                       ▼
                                              T1.8 注册路由
                                                       │
                                                       ▼
                                              T1.11 服务初始化
                                                       │
                                                       ▼
                                              T1.12 集成测试


Phase 2: 记忆系统
==================================================

T2.1 RAGService ──────▶ T2.2 knowledge.py 增强
        │
        │              T2.3 WeeklyService ──────▶ T2.4 weekly.py 增强
        │                     │
        │                     ▼
        └──────────▶ T2.5 Working Context 注入
                            │
                            ▼
                     T2.6 RAG 集成到预测
                            │
                            ▼
                     T2.7 服务注册
                            │
                            ▼
                     T2.8 集成测试


Phase 3: 前端增强
==================================================

                     T3.2 TrendBadge ────────┐
                                             │
                     T3.3 ConfidenceBar ─────┼──▶ T3.6 PlantResponseCard
                                             │
                     T3.4 EvidenceList ──────┤
                                             │
                     T3.5 AbnormalityAlert ──┘


T3.1 useDailyPredict ───────┐
                            │
T3.6 PlantResponseCard ─────┼──▶ T3.9 DailyDecision 集成
                            │
T3.7 ImageCompare ──────────┘


T3.8 RAGReferences ──────────▶ T3.10 Knowledge 集成
```

---

## 检查清单

### Phase 1 完成检查
- [ ] T1.1 ~ T1.12 全部完成
- [ ] `/api/predict/daily` 可正常调用
- [ ] PlantResponse 自动生成并保存
- [ ] 冷启动情况正确处理
- [ ] SanityCheck 验证生效
- [ ] Episode 自动入库
- [ ] 所有测试通过

### Phase 2 完成检查
- [ ] T2.1 ~ T2.8 全部完成
- [ ] `/api/knowledge/query` RAG 问答可用
- [ ] `/api/weekly/generate` 周报生成可用
- [ ] Working Context 正确注入
- [ ] RAG 检索结果在预测中使用
- [ ] 所有测试通过

### Phase 3 完成检查
- [ ] T3.1 ~ T3.10 全部完成
- [ ] DailyDecision 页面显示 PlantResponse
- [ ] 图像对比功能正常
- [ ] Knowledge 页面显示 RAG 引用
- [ ] 所有组件样式统一
- [ ] 响应式布局正常

---

## 附录: 文件创建清单

### 新建文件

```
backend/app/
├── api/v1/
│   └── predict.py                    # T1.7
├── services/
│   ├── prediction_service.py         # T1.5
│   ├── memory_service.py             # T1.2
│   ├── rag_service.py                # T2.1
│   └── weekly_service.py             # T2.3
├── core/
│   └── dependencies.py               # T1.11
└── tests/
    ├── test_predict.py               # T1.12
    └── test_memory.py                # T2.8

frontend/src/
├── components/
│   ├── PlantResponseCard/
│   │   ├── PlantResponseCard.tsx     # T3.6
│   │   ├── PlantResponseCard.css
│   │   ├── TrendBadge.tsx            # T3.2
│   │   ├── ConfidenceBar.tsx         # T3.3
│   │   ├── EvidenceList.tsx          # T3.4
│   │   ├── AbnormalityAlert.tsx      # T3.5
│   │   └── index.ts
│   ├── ImageCompare/
│   │   ├── ImageCompare.tsx          # T3.7
│   │   ├── ImageCompare.css
│   │   └── index.ts
│   └── RAGReferences/
│       ├── RAGReferences.tsx         # T3.8
│       ├── RAGReferences.css
│       └── index.ts
└── hooks/
    └── useDailyPredict.ts            # T3.1
```

### 修改文件

```
backend/app/
├── models/schemas.py                 # T1.1
├── services/llm_service.py           # T1.3, T1.4
├── services/__init__.py              # T1.11, T2.7
├── api/v1/knowledge.py               # T2.2
├── api/v1/weekly.py                  # T2.4
├── core/config.py                    # T2.7
└── main.py                           # T1.8

frontend/src/
├── pages/DailyDecision.tsx           # T3.9
└── pages/Knowledge.tsx               # T3.10
```

---

> 文档结束
