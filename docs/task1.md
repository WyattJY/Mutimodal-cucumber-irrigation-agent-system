# 温室黄瓜灌水智能体系统 - 补充开发任务文档

> 版本：v1.1
> 更新日期：2024-12-26
> 基于：requirements1.md v1.2 + design1.md v1.0
> 文档状态：任务分解完成（含 Q7 知识增强 + 数据隔离设计）

---

## 1. 任务总览

### 1.1 开发阶段划分

| 阶段 | 名称 | 核心目标 | 预计任务数 |
|------|------|----------|------------|
| Phase 1 | 基础设施补充 | 新增配置、数据模型 | 6 |
| Phase 2 | 核心组件 | 冷启动、窗口构建、异常检测、环境输入、生育期检测 | 8 |
| Phase 3 | 记忆架构 | 4层记忆 L1-L4 实现 | 8 |
| Phase 4 | 服务封装 | TSMixer、RAG、数据库服务、知识增强 | 7 |
| Phase 5 | 流程管道 | 每日/每周 Pipeline 扩展（含知识增强） | 4 |
| Phase 6 | 集成测试 | 端到端测试、验收（含 Q7） | 6 |

### 1.2 任务依赖关系

```
Phase 1 (基础设施补充)
    │
    ├──▶ Phase 2 (核心组件)
    │        │
    │        └──▶ Phase 4 (服务封装)
    │                  │
    │                  └──▶ Phase 5 (流程管道)
    │                            │
    │                            └──▶ Phase 6 (集成测试)
    │
    └──▶ Phase 3 (记忆架构)
             │
             └──▶ Phase 4 (服务封装)
```

---

## 2. Phase 1: 基础设施补充

### 2.1 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P1-01 | thresholds.yaml 创建 | P0 | 无 | 包含 A1/A2/A3 阈值配置 |
| P1-02 | memory.yaml 创建 | P0 | 无 | 包含预算控制配置 |
| P1-03 | EnvInput 模型定义 | P0 | 无 | 支持 CSV 和前端输入 |
| P1-04 | AnomalyResult 模型定义 | P0 | 无 | 包含 A1/A2/A3 结果字段 |
| P1-05 | RAGResult 模型定义 | P0 | 无 | 包含检索结果字段 |
| P1-06 | knowledge_enhancement.yaml 创建 | P0 | 无 | 知识增强配置（Q7） |

### 2.2 任务详情

#### P1-01: thresholds.yaml 创建

**目标**: 创建阈值配置文件

**文件**: `configs/thresholds.yaml`

**内容** (参考 requirements1.md 9.1节):
```yaml
# A1: 历史范围阈值
irrigation_range:
  min: 0.1
  max: 15.0
  mean: 5.5
  std: 3.5

# A2: 长势-灌水矛盾阈值
trend_conflict:
  severe_decrease_threshold: -0.10
  moderate_increase_threshold: 0.10
  severe_abnormality_threshold: 0.20
  mild_increase_threshold: 0.30

# A3: 环境异常阈值
env_anomaly:
  consecutive_days: 3
  high_humidity: 85
  high_temperature: 35
  low_light: 2000
```

---

#### P1-02: memory.yaml 创建

**目标**: 创建记忆架构配置文件

**文件**: `configs/memory.yaml`

**内容** (参考 requirements1.md 9.2节):
```yaml
context_budget:
  total_max: 4500
  system_fixed: 500
  weekly_max: 800
  today_max: 2000
  retrieval_max: 1000
  retrieval_default_k: 3

compression:
  priority:
    retrieval: 1
    weekly: 2
    today: 3
  today_keep_fields:
    - trend
    - confidence
    - growth_stage
    - abnormalities

weekly_summary:
  prompt_block_max_tokens: 800
  max_key_insights: 5
```

---

#### P1-03: EnvInput 模型定义

**目标**: 定义环境输入数据模型

**文件**: `src/cucumber_irrigation/models/env_input.py`

**结构**:
```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class EnvInput(BaseModel):
    """环境输入数据"""
    date: str
    temperature: float = Field(..., ge=-10, le=50, description="温度 (°C)")
    humidity: float = Field(..., ge=0, le=100, description="湿度 (%)")
    light: float = Field(..., ge=0, le=200000, description="光照 (lux)")
    source: Literal["csv", "frontend"] = "csv"

    # 可选: YOLO 指标 (如果前端同时提供)
    leaf_instance_count: Optional[float] = None
    leaf_average_mask: Optional[float] = None
    flower_instance_count: Optional[float] = None
    flower_mask_pixel_count: Optional[float] = None
    terminal_average_mask: Optional[float] = None
    fruit_mask_average: Optional[float] = None
    all_leaf_mask: Optional[float] = None
```

---

#### P1-06: knowledge_enhancement.yaml 创建

**目标**: 创建知识增强配置文件

**文件**: `configs/knowledge_enhancement.yaml`

**内容** (参考 requirements1.md 8.5节):
```yaml
# 生育期预判
growth_stage_detection:
  enabled: true
  confidence_threshold: 0.7    # 低于此置信度时查询多个生育期

# PlantResponse 知识增强
plant_response_rag:
  enabled: true
  top_k: 2                     # 检索片段数
  max_tokens: 400              # 知识注入预算
  prefer_fao56: true

# WeeklySummary 知识增强
weekly_summary_rag:
  enabled: true
  top_k: 3                     # 检索片段数
  max_tokens: 500              # 知识注入预算
  insight_source_tags: true    # 是否标注来源 [文献]/[数据]

# 检索策略
retrieval:
  fao56_weight: 1.5
  cucumber_greenhouse_weight: 1.2
  general_weight: 1.0
  history_weight: 0.8
```

---

## 3. Phase 2: 核心组件

### 3.1 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P2-01 | EnvInputHandler 实现 | P0 | P1-03 | 支持 CSV 读取和前端输入解析 |
| P2-02 | ColdStartFiller 实现 | P0 | P1-03 | 2023年数据填充，日期对齐正确 |
| P2-03 | WindowBuilder 实现 | P0 | P2-02 | 构建96步×11特征窗口 |
| P2-04 | AnomalyDetector - A1 范围检测 | P0 | P1-04 | 范围检测 [0.1, 15.0] |
| P2-05 | AnomalyDetector - A2 矛盾检测 | P0 | P1-04 | 长势-灌水矛盾检测 |
| P2-06 | AnomalyDetector - A3 环境异常 | P0 | P1-04 | 环境异常检测 (连续3天) |
| P2-07 | AnomalyDetector 整合 | P0 | P2-04,05,06 | 三类异常统一检测接口 |
| P2-08 | GrowthStageDetector 实现 | P0 | P1-06 | 生育期预判（Q7），置信度≥0.7 |

### 3.2 任务详情

#### P2-01: EnvInputHandler 实现

**目标**: 实现环境数据输入处理器，支持多种输入来源

**文件**: `src/cucumber_irrigation/core/env_input_handler.py`

**功能**:
1. CSV 文件读取 (批量/历史数据)
2. 前端输入解析 (实时数据: temperature, humidity, light)
3. 数据验证
4. 统一输出 EnvInput 格式

**接口设计**:
```python
class EnvInputHandler:
    """环境数据输入处理器"""

    def __init__(self, csv_path: Optional[str] = None):
        """
        Args:
            csv_path: CSV 文件路径 (可选)
        """
        pass

    def from_csv(self, date: str) -> EnvInput:
        """从 CSV 读取指定日期的环境数据"""
        pass

    def from_frontend(
        self,
        date: str,
        temperature: float,
        humidity: float,
        light: float
    ) -> EnvInput:
        """从前端输入构建环境数据"""
        pass

    def validate(self, env: EnvInput) -> tuple[bool, list[str]]:
        """
        验证环境数据

        Returns:
            (是否有效, 错误信息列表)
        """
        pass
```

**验收标准**:
- 支持 CSV 格式读取 (irrigation.csv)
- 支持前端 dict 格式输入
- 数据验证：temperature [-10, 50], humidity [0, 100], light [0, 200000]
- 验证失败时返回详细错误信息

---

#### P2-02: ColdStartFiller 实现

**目标**: 实现冷启动数据填充，解决数据不足问题

**文件**: `src/cucumber_irrigation/core/cold_start.py`

**数据源**: `data/csv/irrigation_pre.csv` (2023年春茬数据)

**算法** (参考 requirements1.md 2.4节):
```
输入：
  - target_date: "2025-03-14"
  - user_data: 用户已有数据 (可能为空)

输出：
  - 96 步完整序列

流程：
1. 计算需填充天数 = 95 - len(user_data)
2. 映射日期到参考年份：2025-03-14 → 2023-03-14
3. 从 irrigation_pre.csv 获取 ref_date 之前的 fill_days 天数据
4. 拼接顺序：[填充数据 | 用户数据 | 今日数据]
5. 返回总长度 = 96 的序列
```

**接口设计**:
```python
class ColdStartFiller:
    """冷启动数据填充器"""

    def __init__(self, reference_data_path: str):
        """
        Args:
            reference_data_path: 参考数据路径 (irrigation_pre.csv)
        """
        self.reference_data = self._load_reference_data(reference_data_path)

    def fill(
        self,
        user_data: pd.DataFrame,
        target_date: str,
        today_data: Optional[dict] = None,
        required_length: int = 96
    ) -> pd.DataFrame:
        """
        填充数据到指定长度

        Args:
            user_data: 用户已有数据
            target_date: 目标预测日期 (YYYY-MM-DD)
            today_data: 今日输入数据 (可选)
            required_length: 需要的序列长度

        Returns:
            填充后的完整数据 (96行)
        """
        pass

    def _map_date_to_reference_year(self, date: str) -> str:
        """将目标日期映射到参考年份 (2023)"""
        pass
```

**验收标准**:
- 填充后序列长度 = 96
- 日期对齐正确 (月日相同: 03-14 → 03-14)
- 支持春茬 (3-6月) 日期范围
- 用户数据优先级高于填充数据

---

#### P2-03: WindowBuilder 实现

**目标**: 构建 TSMixer 输入窗口

**文件**: `src/cucumber_irrigation/core/window_builder.py`

**特征列** (11列):
```python
FEATURE_COLUMNS = [
    'temperature',           # 日均温度
    'humidity',              # 日均湿度
    'light',                 # 日均光照
    'leaf Instance Count',   # 叶片实例数量
    'leaf average mask',     # 叶片平均掩码
    'flower Instance Count', # 花朵实例数量
    'flower Mask Pixel Count', # 花朵掩码像素
    'terminal average Mask Pixel Count', # 顶芽平均掩码
    'fruit Mask average',    # 果实平均掩码
    'all leaf mask',         # 全部叶片掩码
    'Target'                 # 历史灌水量
]
```

**接口设计**:
```python
class WindowBuilder:
    """时序窗口构建器"""

    def __init__(self, cold_start_filler: ColdStartFiller):
        self.cold_start_filler = cold_start_filler
        self.feature_columns = FEATURE_COLUMNS

    def build(
        self,
        data: pd.DataFrame,
        target_date: str,
        today_data: Optional[dict] = None
    ) -> np.ndarray:
        """
        构建时序窗口

        Args:
            data: 历史数据
            target_date: 目标日期
            today_data: 今日输入数据 (可选)

        Returns:
            shape [96, 11] 的输入矩阵
        """
        pass
```

**验收标准**:
- 输出 shape: [96, 11]
- 自动调用 ColdStartFiller 填充不足数据
- 支持今日数据可选输入 (来自前端或 CSV)
- 特征列顺序与 TSMixer 训练一致

---

#### P2-04: AnomalyDetector - A1 范围检测

**目标**: 实现灌水量范围异常检测

**文件**: `src/cucumber_irrigation/core/anomaly_detector.py`

**规则** (参考 requirements1.md 3.2节):
```python
def check_range(prediction: float) -> bool:
    """
    A1: 检测预测值是否超出历史范围

    阈值:
      - min: 0.1 L/m²
      - max: 15.0 L/m²

    Returns:
        True if 超出范围
    """
    return prediction < 0.1 or prediction > 15.0
```

---

#### P2-05: AnomalyDetector - A2 矛盾检测

**目标**: 实现长势-灌水矛盾检测

**规则** (参考 requirements1.md 3.3节):
```python
def check_conflict(
    prediction: float,
    yesterday_irrigation: float,
    plant_response: PlantResponse
) -> tuple[bool, str]:
    """
    A2: 检测长势-灌水矛盾

    Returns:
        (是否矛盾, 严重程度: none/mild/moderate/severe)
    """
    change_ratio = (prediction - yesterday_irrigation) / max(yesterday_irrigation, 0.1)
    trend = plant_response.comparison.trend
    has_severe_abnormality = (
        plant_response.abnormalities.wilting or
        plant_response.abnormalities.yellowing
    )

    if trend == "worse":
        if change_ratio < -0.10:  # 灌水减少>10%
            return True, "severe"
        elif change_ratio < 0.10:  # 灌水增加<10%
            return True, "moderate"
        elif has_severe_abnormality and change_ratio < 0.20:
            return True, "moderate"
    elif trend == "better":
        if change_ratio > 0.30:  # 灌水增加>30%
            return True, "mild"

    return False, "none"
```

---

#### P2-06: AnomalyDetector - A3 环境异常

**目标**: 实现连续环境异常检测

**规则** (参考 requirements1.md 3.4节):
```python
def check_env_anomaly(
    env_history: list[dict],
    consecutive_days: int = 3
) -> tuple[bool, Optional[str]]:
    """
    A3: 检测连续环境异常

    异常类型:
      - high_humidity: 连续≥3天, humidity > 85%
      - high_temperature: 连续≥3天, temperature > 35°C
      - low_light: 连续≥3天, light < 2000 lux

    Returns:
        (是否异常, 异常类型)
    """
    if len(env_history) < consecutive_days:
        return False, None

    recent = env_history[-consecutive_days:]

    # 高湿检测
    if all(e['humidity'] > 85 for e in recent):
        return True, "high_humidity"

    # 高温检测
    if all(e['temperature'] > 35 for e in recent):
        return True, "high_temperature"

    # 弱光检测
    if all(e['light'] < 2000 for e in recent):
        return True, "low_light"

    return False, None
```

---

#### P2-08: GrowthStageDetector 实现

**目标**: 实现基于图像的生育期预判（Q7）

**文件**: `src/cucumber_irrigation/core/growth_stage_detector.py`

**功能** (参考 requirements1.md 8.2节):
1. 调用 GPT-5.2 视觉模型分析图像
2. 判断当前生育期（vegetative/flowering/fruiting/mixed）
3. 返回生育期及置信度

**判断依据**:
```
- vegetative: 主要可见叶片，无明显花朵/果实
- flowering: 可见黄色花朵，可能有小果
- fruiting: 可见发育中的果实（黄瓜）
- mixed: 多种生育期特征并存
```

**接口设计**:
```python
from typing import Literal, Tuple

GrowthStage = Literal["vegetative", "flowering", "fruiting", "mixed"]

class GrowthStageDetector:
    """生育期检测器"""

    def __init__(self, llm_service, config: dict):
        """
        Args:
            llm_service: LLM 服务实例
            config: knowledge_enhancement.yaml 配置
        """
        self.llm = llm_service
        self.confidence_threshold = config.get('confidence_threshold', 0.7)

    def detect(self, image_path: str) -> Tuple[GrowthStage, float]:
        """
        检测生育期

        Args:
            image_path: 图像路径

        Returns:
            (生育期, 置信度)
        """
        pass

    def get_retrieval_query(self, stage: GrowthStage) -> str:
        """
        根据生育期生成检索查询

        Args:
            stage: 生育期

        Returns:
            RAG 检索查询字符串
        """
        queries = {
            "vegetative": "cucumber vegetative stage Kc leaf growth water requirement",
            "flowering": "cucumber flowering stage Kc flower development water stress",
            "fruiting": "cucumber fruiting stage Kc fruit development irrigation",
            "mixed": "cucumber transition growth stage Kc adjustment"
        }
        return queries.get(stage, queries["mixed"])
```

**验收标准**:
- GPT-5.2 成功识别生育期
- 返回置信度 ≥ 0.7 时使用单一生育期
- 置信度 < 0.7 时标记为 mixed 或查询多个生育期

---

## 4. Phase 3: 记忆架构

### 4.1 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P3-01 | TokenCounter 实现 | P0 | 无 | tiktoken 集成，准确计数 |
| P3-02 | BudgetController 实现 | P0 | P3-01, P1-02 | Rule-M1 预算控制，总上下文≤4500 |
| P3-03 | WorkingContextBuilder 实现 | P0 | P3-02 | L1 工作上下文构建 |
| P3-04 | EpisodeStore 实现 | P0 | 无 | L2 Episode 存储到 MongoDB |
| P3-05 | WeeklySummaryStore 实现 | P0 | P3-01 | L3 周摘要管理，prompt_block≤800 |
| P3-06 | KnowledgeRetriever 实现 | P1 | 无 | L4 Milvus 知识检索 |
| P3-07 | RAG 查询构建器 | P1 | P3-06 | 根据异常类型构建 RAG 查询 |
| P3-08 | 压缩策略实现 | P1 | P3-02 | Retrieval→Weekly→Today 压缩 |

### 4.2 任务详情

#### P3-01: TokenCounter 实现

**目标**: 实现 Token 计数器

**文件**: `src/cucumber_irrigation/utils/token_counter.py`

**接口设计**:
```python
import tiktoken

class TokenCounter:
    """Token 计数器"""

    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)

    def count(self, text: str) -> int:
        """计算文本的 token 数"""
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        """计算 messages 列表的总 token 数"""
        total = 0
        for msg in messages:
            total += self.count(msg.get("content", ""))
        return total
```

---

#### P3-02: BudgetController 实现

**目标**: 实现 Rule-M1 上下文预算控制

**文件**: `src/cucumber_irrigation/memory/budget_controller.py`

**预算分配** (参考 requirements1.md 5.1节):
| 组成部分 | 预算上限 | 说明 |
|----------|----------|------|
| System | ~500 tokens | 固定，不可压缩 |
| Weekly | ≤800 tokens | prompt_block 上限 |
| Today | ~2000 tokens | 环境+YOLO+对比结论 |
| Retrieval | ~1000 tokens | TopK=3-5 片段 |
| **总计** | **≤4500** | 预留空间给输出 |

**压缩优先级** (数字越小越先压缩):
1. Retrieval: 5→3→1→删除
2. Weekly: 只保留 key_insights
3. Today: 只保留核心字段

---

#### P3-05: WeeklySummaryStore 实现

**目标**: 实现 L3 周摘要管理

**文件**: `src/cucumber_irrigation/memory/weekly_summary_store.py`

**prompt_block 生成规则** (参考 requirements1.md 4.5节):
```
优先级:
1. key_insights (必须保留)
2. dominant_trend + irrigation_trend
3. anomaly_events 摘要
4. override_summary
```

**超限压缩策略**:
```
IF prompt_block_tokens > 800:
    1. 删除 override_summary
    2. 只保留 severe 级别异常
    3. 只保留前3条 key_insights
    4. 如仍超限，只保留第1条
```

---

#### P3-07: RAG 查询构建器

**目标**: 根据异常类型构建 RAG 检索查询

**文件**: `src/cucumber_irrigation/memory/knowledge_retriever.py` (方法)

**查询模板** (参考 requirements1.md 3.6节):

| 异常类型 | 查询模板 |
|----------|----------|
| A2-长势矛盾 | `cucumber water stress irrigation adjustment crop coefficient Kc under stress conditions plant {abnormality} water requirement growth stage: {stage}` |
| A3-高湿异常 | `high humidity greenhouse irrigation reduction disease prevention` |
| A3-高温胁迫 | `high temperature water stress crop evapotranspiration cooling` |
| A3-弱光异常 | `low light photosynthesis reduction irrigation adjustment` |

---

## 5. Phase 4: 服务封装

### 5.1 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P4-01 | DBService 扩展 | P0 | 无 | 支持跨库访问 (cucumber_irrigation + greenhouse_db) |
| P4-02 | TSMixerService 实现 | P0 | P2-03 | 滚动预测，标准化/逆标准化 |
| P4-03 | RAGService 实现 | P1 | P3-06 | Milvus 检索封装，FAO56 优先 |
| P4-04 | LLMService 扩展 | P1 | P3-03 | SanityCheck 支持 Weekly Context 注入 |
| P4-05 | 异常处理中间件 | P1 | P2-07, P4-03 | 异常检测 + RAG 辅助判断整合 |
| P4-06 | KnowledgeEnhancedPlantResponse 服务 | P1 | P2-08, P4-03 | 知识增强的长势评估（Q7） |
| P4-07 | KnowledgeEnhancedWeeklySummary 服务 | P1 | P4-06, P3-05 | 知识增强的周度总结（Q7） |

### 5.2 任务详情

#### P4-01: DBService 扩展

**目标**: 扩展数据库服务，支持同实例分库访问

**文件**: `src/cucumber_irrigation/services/db_service.py`

**数据库架构** (参考 requirements1.md 6.1节):
```
MongoDB 实例 (localhost:27017)
├── greenhouse_db (只读访问)
│   └── literature_chunks  # FAO56 文献片段
│
└── cucumber_irrigation (业务库)
    ├── episodes           # 每日决策记录
    ├── weekly_summaries   # 周摘要
    ├── overrides          # 人工覆盖记录
    └── learning_events    # 学习事件
```

**索引设计**:
```python
# episodes
episodes.create_index("date", unique=True)
episodes.create_index("season")

# weekly_summaries
weekly_summaries.create_index("week_start", unique=True)

# overrides
overrides.create_index("date")
overrides.create_index([("reason", "text")])
```

---

#### P4-02: TSMixerService 实现

**目标**: 封装 TSMixer 预测服务

**文件**: `src/cucumber_irrigation/services/tsmixer_service.py`

**流程**:
```
1. 调用 WindowBuilder 构建 96 步窗口
   └─ 自动处理冷启动填充

2. 加载 StandardScaler
   └─ 路径: ../Irrigation/scaler.pkl

3. 标准化输入
   └─ window_scaled = scaler.transform(window)

4. 加载模型推理
   └─ 路径: ../Irrigation/model.pt

5. 逆标准化 Target 列
   └─ 只对第11列 (index=10) 逆变换

6. 返回预测灌水量 (L/m²)
```

---

#### P4-05: 异常处理中间件

**目标**: 整合异常检测与 RAG 辅助判断

**文件**: `src/cucumber_irrigation/services/anomaly_middleware.py`

**流程** (参考 requirements1.md 3.5节):
```
1. 执行异常检测
   ├─ A1: 范围检测
   ├─ A2: 矛盾检测
   └─ A3: 环境异常

2. 如有异常，构建 RAG 查询
   └─ 根据异常类型选择查询模板

3. 执行 Milvus 检索
   ├─ 稀疏向量: 关键词精确匹配
   └─ 稠密向量: 语义相似度 (BGE-M3)

4. 优先返回 is_fao56=true 的片段

5. 将结果注入 SanityCheck.rag_advice
```

---

#### P4-06: KnowledgeEnhancedPlantResponse 服务

**目标**: 实现知识增强的长势评估服务（Q7）

**文件**: `src/cucumber_irrigation/services/knowledge_enhanced_response.py`

**流程** (参考 requirements1.md 8.2节):
```
1. 生育期预判
   ├─ 调用 GrowthStageDetector.detect(image)
   └─ 获取 growth_stage + confidence

2. 知识库检索
   ├─ 根据 growth_stage 构建查询
   │   └─ "cucumber {stage} Kc water requirement"
   ├─ 执行 Milvus 检索 (TopK=2)
   └─ 优先返回 FAO56 片段

3. 知识增强 Prompt 构建
   ├─ 注入 <growth_stage_knowledge> 块
   │   ├─ FAO56 Kc 系数
   │   └─ 生育期典型特征
   └─ 请求 LLM 结合知识评估长势

4. 生成增强版 PlantResponse
   ├─ comparison.evidence 引用文献依据
   ├─ key_observations 结合 Kc 分析
   └─ knowledge_references 记录引用
```

**接口设计**:
```python
class KnowledgeEnhancedPlantResponseService:
    """知识增强的长势评估服务"""

    def __init__(
        self,
        growth_detector: GrowthStageDetector,
        rag_service: RAGService,
        llm_service: LLMService,
        config: dict
    ):
        self.growth_detector = growth_detector
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.config = config

    def generate(
        self,
        image_path: str,
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        env_data: dict
    ) -> PlantResponse:
        """
        生成知识增强的 PlantResponse

        Returns:
            PlantResponse 包含:
            - growth_stage: 生育期
            - growth_stage_confidence: 置信度
            - comparison.evidence: 文献依据
            - knowledge_references: 引用列表
        """
        pass
```

**验收标准**:
- 生育期预判成功，置信度 ≥ 0.7
- evidence 字段引用 FAO56/文献内容
- knowledge_references 包含引用的 doc_id

---

#### P4-07: KnowledgeEnhancedWeeklySummary 服务

**目标**: 实现知识增强的周度总结服务（Q7）

**文件**: `src/cucumber_irrigation/services/knowledge_enhanced_weekly.py`

**流程** (参考 requirements1.md 8.3节):
```
1. 本周数据聚合
   ├─ 获取 7 天 Episodes
   ├─ 统计主要生育期 (dominant_stage)
   ├─ 统计趋势 (better/same/worse)
   ├─ 统计异常事件
   └─ 统计灌水量

2. 知识库检索
   ├─ A. 生育期相关知识
   │   └─ "cucumber {dominant_stage} weekly management"
   ├─ B. 异常处理知识 (如有异常)
   │   └─ "cucumber {anomaly_type} recovery"
   └─ C. 季节性知识
       └─ "cucumber spring greenhouse irrigation pattern"

3. 知识增强经验生成
   ├─ 注入 <weekly_knowledge_context> 块
   ├─ 结合数据和文献生成 key_insights
   └─ 每条 insight 标注来源:
       - [文献]: 主要依据文献
       - [数据]: 主要依据统计数据
       - [文献+数据]: 结合两者
       - [经验]: 基于历史 Override

4. 生成 WeeklySummary
   ├─ key_insights 包含来源标签
   ├─ knowledge_references 记录引用
   └─ prompt_block 用于下周注入
```

**接口设计**:
```python
class KnowledgeEnhancedWeeklySummaryService:
    """知识增强的周度总结服务"""

    def __init__(
        self,
        episode_store: EpisodeStore,
        rag_service: RAGService,
        llm_service: LLMService,
        config: dict
    ):
        self.episode_store = episode_store
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.config = config

    def generate(self, week_start: str, week_end: str) -> WeeklySummary:
        """
        生成知识增强的 WeeklySummary

        Returns:
            WeeklySummary 包含:
            - key_insights: 带来源标签的洞察
            - knowledge_references: 引用列表
            - prompt_block: 用于注入的压缩文本
        """
        pass
```

**key_insights 来源标注**:

| 标签 | 说明 | 示例 |
|------|------|------|
| `[文献]` | 主要依据文献 | "根据FAO56，开花期Kc=0.9-1.0" |
| `[数据]` | 主要依据统计 | "本周出现2次矛盾事件" |
| `[文献+数据]` | 结合两者 | "高湿期减灌20%（参考文献），效果良好（数据）" |
| `[经验]` | 基于历史 Override | "该用户倾向于阴天多灌水" |

**验收标准**:
- key_insights 每条都标注来源
- knowledge_references 包含引用的 doc_id
- prompt_block ≤ 800 tokens

---

## 6. Phase 5: 流程管道

### 6.1 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P5-01 | DailyPipeline 扩展 | P0 | Phase 2-4, P4-06 | 支持前端输入，异常检测，知识增强长势评估 |
| P5-02 | WeeklyPipeline 扩展 | P0 | P3-05, P4-07 | prompt_block 生成与压缩，知识增强周总结 |
| P5-03 | 动态 Prompt 注入 | P0 | P5-02 | 周总结注入下周 SanityCheck |
| P5-04 | Override 处理增强 | P1 | P5-01 | 支持前端 Override 输入 |

### 6.2 任务详情

#### P5-01: DailyPipeline 扩展

**目标**: 扩展每日流程，支持 requirements1.md 新功能（含 Q7 知识增强）

**文件**: `src/cucumber_irrigation/pipelines/daily_pipeline.py`

**扩展点**:
1. 支持前端环境输入 (EnvInputHandler.from_frontend)
2. 集成异常检测 (AnomalyDetector)
3. 集成 RAG 辅助判断 (AnomalyMiddleware)
4. L1 Working Context 构建 (BudgetController)
5. 知识增强长势评估 (KnowledgeEnhancedPlantResponseService)  ← Q7 新增

**流程**:
```
1. 获取输入
   ├─ 图像路径
   ├─ 环境数据 (CSV 或 前端输入)  ← 新增前端支持
   └─ 历史数据

2. 构建时序窗口
   ├─ WindowBuilder
   └─ ColdStartFiller (自动)

3. 并发推理
   ├─ YOLO → YOLOMetrics
   └─ TSMixer → 预测灌水量

4. 生育期预判  ← Q7 新增
   ├─ GrowthStageDetector.detect(image)
   └─ 返回 (growth_stage, confidence)

5. 知识库检索  ← Q7 新增
   ├─ 根据生育期构建查询
   └─ 检索 FAO56 / 文献片段

6. 知识增强长势评估  ← Q7 新增
   ├─ 注入 <growth_stage_knowledge> 块
   ├─ LLM → PlantResponse
   └─ evidence 引用文献依据

7. 异常检测
   ├─ A1: 范围检测
   ├─ A2: 矛盾检测
   └─ A3: 环境异常

8. RAG 辅助 (如有异常)
   └─ 检索 FAO56 建议

9. 构建 L1 Working Context
   ├─ System Prompt
   ├─ Weekly Context (L3.prompt_block)
   ├─ Today Input
   └─ Retrieval (L4.TopK)

10. 预算控制
    └─ BudgetController.apply()

11. 合理性复核
    └─ LLM → SanityCheck

12. 存储 Episode (L2)
    └─ 包含 knowledge_references

13. 输出
    ├─ 灌水量
    ├─ 预警信息
    ├─ RAG 建议
    ├─ 知识引用  ← Q7 新增
    └─ 需确认问题
```

---

#### P5-02: WeeklyPipeline 扩展

**目标**: 扩展每周流程，生成符合预算的 prompt_block（含 Q7 知识增强）

**文件**: `src/cucumber_irrigation/pipelines/weekly_pipeline.py`

**扩展点**:
1. prompt_block 生成
2. Token 计数与压缩
3. 存储到 L3
4. 知识增强周度总结 (KnowledgeEnhancedWeeklySummaryService)  ← Q7 新增

**流程**:
```
1. 获取近 7 天 Episodes (L2)

2. 聚合统计
   ├─ trend_stats
   ├─ irrigation_stats
   ├─ anomaly_events
   └─ dominant_stage (主要生育期)  ← Q7 新增

3. 知识库检索  ← Q7 新增
   ├─ 生育期相关知识
   ├─ 异常处理知识 (如有)
   └─ 季节性知识

4. 知识增强 LLM 周度反思  ← Q7 新增
   ├─ 注入 <weekly_knowledge_context>
   ├─ 生成 key_insights
   └─ 每条标注来源 [文献]/[数据]/[经验]

5. 生成 prompt_block
   └─ 格式: ## 上周经验 (week_start - week_end)

6. Token 检查
   IF tokens > 800:
       压缩 prompt_block

7. 存储 WeeklySummary (L3)
   ├─ 完整统计 (不注入)
   ├─ prompt_block (用于注入)
   └─ knowledge_references  ← Q7 新增

8. 更新动态 Prompt
   └─ 下周 SanityCheck 可用
```

---

#### P5-03: 动态 Prompt 注入

**目标**: 实现周总结动态注入到 SanityCheck Prompt

**注入位置** (参考 requirements1.md 7.2节):
```
Prompt 结构:
├─ 1. System Prompt (固定)
├─ 2. Weekly Context (动态注入)  ← 这里
│      └─ <recent_experience>
│           {prompt_block}
│         </recent_experience>
└─ 3. User Prompt (每日变化)
```

**注入格式**:
```markdown
<recent_experience>
## 上周经验总结 (2025-03-10 - 2025-03-16)

### 长势趋势
- 本周主要趋势：better
- 好转天数：3，持平：2，变差：2

### 灌水量统计
- 日均灌水量：6.07 L/m²
- 变化趋势：increasing

### 关键事件
- 3/12-3/14 连续高湿，已减少灌水20%

### 经验提示
- 本周进入开花期，需水量上升15%
- 3/14 出现长势-灌水矛盾，建议关注

请结合上周经验，分析今日植物状态和灌水建议。
</recent_experience>
```

---

## 7. Phase 6: 集成测试

### 7.1 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P6-01 | 核心组件单元测试 | P0 | Phase 2 | 冷启动、窗口构建、异常检测、生育期检测 |
| P6-02 | 记忆架构单元测试 | P0 | Phase 3 | 预算控制、压缩策略 |
| P6-03 | 每日流程集成测试 | P0 | P5-01 | 单日端到端运行（含知识增强） |
| P6-04 | 每周流程集成测试 | P0 | P5-02 | 周总结生成与注入（含知识增强） |
| P6-05 | Q1-Q6 需求验收 | P0 | 全部 | 全部需求验收通过 |
| P6-06 | Q7 知识增强验收 | P0 | P4-06, P4-07 | 生育期预判、知识引用、来源标注 |

### 7.2 验收标准对照

| 需求 | 验收项 | 测试方法 | 通过标准 |
|------|--------|----------|----------|
| Q1.1 | 滚动预测 | 输入96步序列 | 输出单一灌水量值 |
| Q1.2 | 冷启动填充 | 数据不足时 | 自动用2023年数据填充 |
| Q1.3 | 日期对齐 | 2025-03-14 | 填充2023-03-14数据 |
| Q2.1 | A1 范围检测 | 预测值15.5 | 触发 out_of_range |
| Q2.2 | A2 矛盾检测 | trend=worse, 灌水-15% | 触发 severe |
| Q2.3 | A3 环境异常 | 连续3天humidity>85% | 触发 high_humidity |
| Q2.4 | RAG 辅助 | 有异常时 | 返回 FAO56 片段 |
| Q3.1 | 4层记忆落库 | Episode 存储 | MongoDB 可查询 |
| Q3.2 | 注入预算控制 | 构建上下文 | 总 tokens ≤ 4500 |
| Q3.3 | 超限压缩 | tokens > 4500 | 按优先级压缩 |
| Q4.1 | prompt_block 限制 | 周摘要生成 | ≤ 800 tokens |
| Q5.1 | 同实例分库 | 数据库访问 | 两个库独立可访问 |
| Q5.2 | 知识库复用 | FAO56 检索 | 从 greenhouse_db 读取 |
| Q6.1 | Prompt 注入 | 下周运行 | Weekly Context 包含周总结 |
| Q6.2 | 记忆连贯性 | LLM 输出 | 引用上周经验 |
| **Q7.1** | **生育期预判** | GPT-5.2 图像分析 | 置信度 ≥ 0.7 |
| **Q7.2** | **知识增强 PlantResponse** | 长势评估 | evidence 引用 FAO56/文献 |
| **Q7.3** | **知识增强 WeeklySummary** | 周总结生成 | key_insights 标注来源 |
| **Q7.4** | **检索优先级** | Milvus 检索 | FAO56 优先返回 (权重 1.5x) |
| **Q7.5** | **知识引用记录** | Episode/WeeklySummary | 包含 knowledge_references |

---

## 8. Phase 7: RAG 组件迁移与文献管理（扩展）

### 8.1 设计说明

**背景**：当前设计依赖 Greenhouse_RAG 项目的 MongoDB 和 Milvus。为提升独立性和可维护性，建议将必要的 RAG 组件迁移到 cucumber-irrigation 项目中，并支持用户自定义文献上传。

**迁移策略**：
- 从 Greenhouse_RAG 迁移核心 RAG 功能
- 保持与原有数据库的兼容性
- 新增用户文献管理功能

### 8.2 数据隔离设计

**核心原则**：用户上传的文献**不能污染**系统预置的 FAO56 等权威文献。

**隔离策略**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           文献数据隔离架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Milvus 向量库                                                              │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │  greenhouse_bge_m3 (只读)       │  │  cucumber_user_literature       │  │
│  │  ──────────────────────────────│  │  ──────────────────────────────│  │
│  │  • FAO56 文献                   │  │  • 用户上传的 PDF/TXT          │  │
│  │  • 系统预置温室文献             │  │  • 可增删改                     │  │
│  │  • is_system = true            │  │  • is_user = true              │  │
│  │  • 权重: 1.5x (FAO56)          │  │  • 权重: 0.8x (可配置)          │  │
│  │  • ❌ 禁止用户写入              │  │  • ✅ 用户可管理                │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  MongoDB 文档库                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │  greenhouse_db.literature_chunks│  │  cucumber_irrigation.user_docs  │  │
│  │  ──────────────────────────────│  │  ──────────────────────────────│  │
│  │  • 系统文献原文                 │  │  • 用户文献原文                 │  │
│  │  • 只读访问                     │  │  • 用户可删除                   │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**检索策略**：

| 场景 | 检索范围 | 说明 |
|------|----------|------|
| 默认检索 | 系统文献 + 用户文献 | 合并结果，系统文献权重更高 |
| 仅系统文献 | greenhouse_bge_m3 | 确保权威性 |
| 仅用户文献 | cucumber_user_literature | 用户自定义场景 |
| 优先系统 | 系统优先，用户补充 | FAO56 无匹配时使用用户文献 |

**配置示例**：

```yaml
# configs/rag.yaml

# 文献来源配置
literature:
  system:
    milvus_collection: "greenhouse_bge_m3"
    mongo_collection: "greenhouse_db.literature_chunks"
    readonly: true           # 禁止写入
    weight: 1.5              # FAO56 权重

  user:
    milvus_collection: "cucumber_user_literature"
    mongo_collection: "cucumber_irrigation.user_docs"
    readonly: false          # 允许增删改
    weight: 0.8              # 用户文献权重
    max_docs: 100            # 最大文献数限制

# 检索策略
retrieval:
  default_sources: ["system", "user"]  # 默认两者都检索
  fallback_to_user: true               # 系统无匹配时使用用户文献
  merge_strategy: "weighted"           # weighted | interleave | system_first
```

### 8.3 任务列表

| 任务ID | 任务名称 | 优先级 | 依赖 | 验收标准 |
|--------|----------|--------|------|----------|
| P7-01 | RAG 核心组件迁移 | P1 | P3-06 | Embedding、检索逻辑独立运行，支持多源隔离检索 |
| P7-02 | 文献上传 API | P2 | P7-01 | 支持 PDF/TXT 上传到用户专属集合 |
| P7-03 | 文献分块处理 | P2 | P7-02 | 自动分块、向量化，标记 source_type="user" |
| P7-04 | 文献入库服务（隔离） | P2 | P7-03 | 用户文献入库到独立集合，系统文献不受影响 |
| P7-05 | 用户文献管理界面 | P2 | P7-04 | 查看、删除、重建索引（仅用户文献），提供隔离状态检查 |

### 8.4 任务详情

#### P7-01: RAG 核心组件迁移

**目标**: 从 Greenhouse_RAG 迁移必要的 RAG 组件到 cucumber-irrigation，支持多数据源检索

**迁移内容**:
```
Greenhouse_RAG/
├── embedding/
│   └── bge_m3_embedder.py      # BGE-M3 向量化
├── retrieval/
│   └── hybrid_retriever.py     # 混合检索 (稀疏+稠密)
└── chunking/
    └── pdf_chunker.py          # PDF 分块处理

迁移到 →

cucumber-irrigation/
└── src/cucumber_irrigation/
    └── rag/
        ├── __init__.py
        ├── embedder.py          # BGE-M3 向量化
        ├── retriever.py         # 混合检索 (支持多源)
        └── chunker.py           # 文档分块
```

**多源检索设计**:
```python
class MultiSourceRetriever:
    """多源文献检索器"""

    def __init__(self, config: dict):
        self.system_collection = config['literature']['system']['milvus_collection']
        self.user_collection = config['literature']['user']['milvus_collection']
        self.system_weight = config['literature']['system']['weight']  # 1.5
        self.user_weight = config['literature']['user']['weight']      # 0.8

    def search(
        self,
        query: str,
        top_k: int = 5,
        sources: list[str] = ["system", "user"]  # 可选择检索范围
    ) -> list[RAGResult]:
        """
        多源检索

        Args:
            query: 查询文本
            top_k: 返回数量
            sources: 检索范围 ["system"] / ["user"] / ["system", "user"]

        Returns:
            合并后的检索结果，按加权分数排序
        """
        results = []

        if "system" in sources:
            # 从系统文献集合检索 (FAO56 等)
            system_results = self._search_collection(
                self.system_collection, query, top_k
            )
            for r in system_results:
                r.score *= self.system_weight
                r.source_type = "system"
            results.extend(system_results)

        if "user" in sources:
            # 从用户文献集合检索
            user_results = self._search_collection(
                self.user_collection, query, top_k
            )
            for r in user_results:
                r.score *= self.user_weight
                r.source_type = "user"
            results.extend(user_results)

        # 按加权分数排序，取 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
```

**验收标准**:
- Embedding 独立运行，不依赖 Greenhouse_RAG
- 支持多源检索（系统 + 用户）
- 系统文献只读，用户无法写入
- 支持连接原有 greenhouse_bge_m3 集合（向后兼容）

---

#### P7-02: 文献上传 API

**目标**: 支持用户上传自定义文献（入库到用户专属集合）

**文件**: `src/cucumber_irrigation/rag/literature_api.py`

**支持格式**:
- PDF (主要)
- TXT
- Markdown

**接口设计**:
```python
class LiteratureUploadService:
    """用户文献上传服务"""

    def upload(
        self,
        file_path: str,
        metadata: dict
    ) -> str:
        """
        上传文献到用户集合

        Args:
            file_path: 文件路径
            metadata: 元数据
                - title: 标题
                - author: 作者
                - category: 类别 (irrigation/cucumber/general)

        Returns:
            literature_id

        Note:
            自动标记 is_user=true, source_type="user"
            入库目标: cucumber_user_literature (Milvus)
                      cucumber_irrigation.user_docs (MongoDB)
        """
        pass

    def list_user_literature(self) -> list[dict]:
        """列出用户上传的文献（仅用户集合）"""
        pass

    def delete(self, literature_id: str) -> bool:
        """删除用户文献（仅限用户集合，不影响系统文献）"""
        pass
```

**验收标准**:
- 支持 PDF 上传并解析
- 元数据正确存储到用户集合
- 上传后可通过 MultiSourceRetriever 检索
- 系统文献集合不受影响

---

#### P7-03: 文献分块处理

**目标**: 将上传的文献分块处理，为入库到用户集合做准备

**文件**: `src/cucumber_irrigation/rag/chunker.py`

**分块策略**:
```
1. PDF 解析
   ├─ 使用 PyPDF2 或 pdfplumber
   └─ 提取文本 + 表格

2. 分块规则
   ├─ chunk_size: 512 tokens
   ├─ overlap: 50 tokens
   └─ 保留段落完整性

3. 元数据附加（用户文献标记）
   ├─ source: 原文献 ID
   ├─ page: 页码
   ├─ chunk_index: 分块序号
   ├─ source_type: "user"  ← 标记为用户文献
   └─ is_user: true        ← 用于隔离检索
```

**验收标准**:
- 正确解析 PDF/TXT/Markdown 格式
- 分块大小符合 512 token 限制
- 每个分块包含 `source_type="user"` 和 `is_user=true` 标记

---

#### P7-04: 文献入库服务（隔离）

**目标**: 将分块后的文献向量化并入库到**用户专属集合**，确保不污染系统文献

**文件**: `src/cucumber_irrigation/rag/indexer.py`

**数据隔离原则**:
```
⚠️ 关键：用户上传的文献只能写入用户集合，禁止写入系统集合

系统集合（只读）:
├─ Milvus: greenhouse_bge_m3
└─ MongoDB: greenhouse_db.literature_chunks

用户集合（可写）:
├─ Milvus: cucumber_user_literature  ← 用户文献入库目标
└─ MongoDB: cucumber_irrigation.user_docs  ← 用户文献入库目标
```

**入库流程**:
```
1. 文本分块
   └─ Chunker.chunk(document)

2. 向量化
   └─ Embedder.embed(chunks)

3. Milvus 入库（用户集合）
   ├─ 集合: cucumber_user_literature  ← 隔离的用户集合
   ├─ 字段: id, embedding, doc_id, source_type="user"
   └─ 索引: HNSW

4. MongoDB 入库（用户集合）
   ├─ 集合: cucumber_irrigation.user_docs  ← 隔离的用户集合
   └─ 字段: content, metadata, is_user=true, created_at
```

**接口设计**:
```python
class UserLiteratureIndexer:
    """用户文献入库服务（隔离设计）"""

    def __init__(self, config: dict):
        # 只连接用户集合，禁止访问系统集合
        self.milvus_collection = config['literature']['user']['milvus_collection']
        self.mongo_collection = config['literature']['user']['mongo_collection']

    def index(self, chunks: list[dict], literature_id: str) -> int:
        """
        将文献分块入库到用户集合

        Args:
            chunks: 分块列表
            literature_id: 文献 ID

        Returns:
            入库的分块数量

        Note:
            所有数据标记 source_type="user" 和 is_user=true
        """
        pass

    def delete(self, literature_id: str) -> bool:
        """删除用户文献（仅限用户集合）"""
        pass
```

**验收标准**:
- 向量正确存储到 Milvus `cucumber_user_literature` 集合
- 原文和元数据存储到 MongoDB `cucumber_irrigation.user_docs` 集合
- 入库后可通过 MultiSourceRetriever 检索（sources=["user"]）
- **确保系统集合 greenhouse_bge_m3 和 greenhouse_db.literature_chunks 未被修改**

---

#### P7-05: 用户文献管理界面

**目标**: 提供简单的文献管理界面（CLI 或 简单 Web），**仅管理用户集合**

**文件**: `src/cucumber_irrigation/rag/cli.py`

**功能**（仅限用户文献）:
1. 列出所有用户上传的文献（从 `cucumber_irrigation.user_docs` 读取）
2. 查看文献详情和分块数量
3. 删除文献（同时删除 `cucumber_user_literature` 和 `cucumber_irrigation.user_docs` 数据）
4. 重建索引（仅重建用户文献索引）

**CLI 示例**:
```bash
# 列出用户文献（不含系统文献）
uv run python -m cucumber_irrigation.rag.cli list

# 上传文献（入库到用户集合）
uv run python -m cucumber_irrigation.rag.cli upload /path/to/file.pdf --title "文献标题"

# 删除用户文献（仅限用户集合）
uv run python -m cucumber_irrigation.rag.cli delete <literature_id>

# 重建用户文献索引（不影响系统文献）
uv run python -m cucumber_irrigation.rag.cli reindex

# 查看数据隔离状态
uv run python -m cucumber_irrigation.rag.cli status
```

**隔离保护机制**:
```python
class UserLiteratureCLI:
    """用户文献 CLI（隔离设计）"""

    def __init__(self, config: dict):
        # 只初始化用户集合连接
        self.user_milvus = config['literature']['user']['milvus_collection']
        self.user_mongo = config['literature']['user']['mongo_collection']
        # ❌ 不初始化系统集合连接，从设计上阻止误操作

    def status(self) -> dict:
        """
        显示数据隔离状态

        Returns:
            {
                "system_literature_count": 1234,  # 系统文献数（只读统计）
                "user_literature_count": 15,       # 用户文献数
                "isolation_status": "healthy"      # 隔离状态
            }
        """
        pass
```

**验收标准**:
- 所有管理操作仅作用于用户集合
- 提供 `status` 命令验证数据隔离状态
- 无法通过 CLI 删除或修改系统文献

---

## 9. 任务执行计划

### 9.1 执行顺序

```
Week 1: 基础设施 + 核心组件(上)
├─ P1-01 thresholds.yaml
├─ P1-02 memory.yaml
├─ P1-03 EnvInput 模型
├─ P1-04 AnomalyResult 模型
├─ P1-05 RAGResult 模型
├─ P1-06 knowledge_enhancement.yaml  ← Q7 新增
├─ P2-01 EnvInputHandler
└─ P2-02 ColdStartFiller

Week 2: 核心组件(下)
├─ P2-03 WindowBuilder
├─ P2-04 AnomalyDetector - A1
├─ P2-05 AnomalyDetector - A2
├─ P2-06 AnomalyDetector - A3
├─ P2-07 AnomalyDetector 整合
└─ P2-08 GrowthStageDetector  ← Q7 新增

Week 3: 记忆架构
├─ P3-01 TokenCounter
├─ P3-02 BudgetController
├─ P3-03 WorkingContextBuilder
├─ P3-04 EpisodeStore
├─ P3-05 WeeklySummaryStore
└─ P3-06 KnowledgeRetriever

Week 4: 服务与管道
├─ P4-01 DBService 扩展
├─ P4-02 TSMixerService
├─ P4-05 异常处理中间件
├─ P4-06 KnowledgeEnhancedPlantResponse  ← Q7 新增
├─ P4-07 KnowledgeEnhancedWeeklySummary  ← Q7 新增
├─ P5-01 DailyPipeline 扩展
└─ P5-02 WeeklyPipeline 扩展

Week 5: 集成与验收
├─ P5-03 动态 Prompt 注入
├─ P6-01 核心组件单元测试
├─ P6-02 记忆架构单元测试
├─ P6-03 每日流程集成测试
├─ P6-05 Q1-Q6 需求验收
└─ P6-06 Q7 知识增强验收  ← Q7 新增

Week 6 (扩展): RAG 迁移与文献管理
├─ P7-01 RAG 核心组件迁移
├─ P7-02 文献上传 API
├─ P7-03 文献分块处理
├─ P7-04 文献入库服务
└─ P7-05 用户文献管理界面
```

### 9.2 关键里程碑

| 里程碑 | 完成任务 | 验收标准 |
|--------|----------|----------|
| M1: 配置完成 | P1-01 ~ P1-06 | 配置文件可加载（含知识增强配置） |
| M2: 输入处理完成 | P2-01 ~ P2-03 | 96步窗口正确生成 |
| M3: 异常检测完成 | P2-04 ~ P2-08 | 三类异常正确识别 + 生育期检测 |
| M4: 记忆架构完成 | P3-01 ~ P3-06 | L1-L4 读写正常 |
| M5: 预算控制完成 | P3-02, P3-08 | 上下文 ≤ 4500 tokens |
| M6: 每日流程完成 | P5-01 | 单日端到端运行（含知识增强） |
| M7: 每周流程完成 | P5-02, P5-03 | 周总结注入成功（含知识增强） |
| M8: 系统验收 | P6-05 | Q1-Q6 全部通过 |
| **M9: Q7 知识增强验收** | P6-06 | 生育期预判、知识引用验收通过 |
| **M10: RAG 独立运行** | P7-01 ~ P7-05 | 用户文献上传入库可用，数据隔离验证通过 |

---

## 10. 附录

### 10.1 文件清单

| 模块 | 文件 | 任务ID |
|------|------|--------|
| configs | thresholds.yaml | P1-01 |
| configs | memory.yaml | P1-02 |
| configs | knowledge_enhancement.yaml | P1-06 |
| configs | rag.yaml | P7-01 |
| models | env_input.py | P1-03 |
| models | anomaly.py | P1-04, P1-05 |
| core | env_input_handler.py | P2-01 |
| core | cold_start.py | P2-02 |
| core | window_builder.py | P2-03 |
| core | anomaly_detector.py | P2-04 ~ P2-07 |
| core | growth_stage_detector.py | P2-08 |
| utils | token_counter.py | P3-01 |
| memory | budget_controller.py | P3-02, P3-08 |
| memory | working_context.py | P3-03 |
| memory | episode_store.py | P3-04 |
| memory | weekly_summary_store.py | P3-05 |
| memory | knowledge_retriever.py | P3-06, P3-07 |
| services | db_service.py | P4-01 |
| services | tsmixer_service.py | P4-02 |
| services | rag_service.py | P4-03 |
| services | llm_service.py | P4-04 |
| services | anomaly_middleware.py | P4-05 |
| services | knowledge_enhanced_response.py | P4-06 |
| services | knowledge_enhanced_weekly.py | P4-07 |
| pipelines | daily_pipeline.py | P5-01 |
| pipelines | weekly_pipeline.py | P5-02, P5-03 |
| rag | embedder.py | P7-01 |
| rag | retriever.py | P7-01 |
| rag | chunker.py | P7-03 |
| rag | literature_api.py | P7-02 |
| rag | indexer.py | P7-04 |
| rag | cli.py | P7-05 |

### 10.2 任务状态定义

| 状态 | 图标 | 说明 |
|------|------|------|
| TODO | 📋 | 待开始 |
| WIP | 🚧 | 进行中 |
| REVIEW | 🔍 | 待审核 |
| DONE | ✅ | 已完成 |
| BLOCKED | ⏸️ | 阻塞中 |
