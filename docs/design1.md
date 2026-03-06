# 温室黄瓜灌水智能体系统 - 补充设计文档 v1

> 版本：v1.0
> 更新日期：2024-12-26
> 基于：requirements1.md v1.1
> 文档状态：设计定稿

---

## 1. 核心目标

### 1.1 设计目标

| 目标编号 | 目标描述 | 对应需求 |
|----------|----------|----------|
| G1 | 实现 TSMixer 滚动预测与冷启动数据填充 | Q1 |
| G2 | 实现预测异常检测与 RAG 辅助判断 | Q2 |
| G3 | 实现 4 层记忆架构（L1-L4） | Q3 |
| G4 | 实现上下文注入预算控制（Rule-M1） | Q4 |
| G5 | 实现同实例分库的数据库架构 | Q5 |
| G6 | 实现周总结动态 Prompt 注入机制 | Q6 |

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个模块只负责一个明确的功能 |
| **依赖注入** | 服务间通过接口解耦，便于测试和替换 |
| **配置外置** | 阈值、路径等配置从代码中分离 |
| **渐进增强** | 核心功能先行，增强功能后续迭代 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              温室黄瓜灌水智能体系统 v2                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                              输入层 (Input Layer)                              │ │
│  │                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────────────────────┐  ┌─────────────────────┐  │ │
│  │  │ 📷 图像输入  │  │ 🌡️ 环境数据                  │  │ 👨‍🌾 用户交互         │  │ │
│  │  │             │  │  ├─ CSV文件 (批量/历史)      │  │  ├─ Override 反馈   │  │ │
│  │  │             │  │  └─ 前端输入 (实时)          │  │  └─ 评分/备注       │  │ │
│  │  │             │  │     • temperature (°C)      │  │                     │  │ │
│  │  │             │  │     • humidity (%)          │  │                     │  │ │
│  │  │             │  │     • light (lux)           │  │                     │  │ │
│  │  └──────┬──────┘  └──────────────┬──────────────┘  └──────────┬──────────┘  │ │
│  │         │                        │                            │              │ │
│  │         │         ┌──────────────┴──────────────┐             │              │ │
│  │         │         │ 📊 历史数据 (96天窗口)       │             │              │ │
│  │         │         │    来源: CSV 或 MongoDB     │             │              │ │
│  │         │         └──────────────┬──────────────┘             │              │ │
│  └─────────┼────────────────────────┼────────────────────────────┼──────────────┘ │
│            │                        │                            │                │
│            ▼                        ▼                            ▼                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                           数据处理层 (Data Layer)                              │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐   │ │
│  │  │  ColdStartFiller │  │  WindowBuilder  │  │  EnvInputHandler            │   │ │
│  │  │  冷启动数据填充   │  │  96步窗口构建    │  │  环境输入处理器              │   │ │
│  │  │                 │  │                 │  │  ├─ CSV 读取                 │   │ │
│  │  │                 │  │                 │  │  ├─ 前端输入解析              │   │ │
│  │  │                 │  │                 │  │  └─ 数据验证                 │   │ │
│  │  └────────┬────────┘  └────────┬────────┘  └─────────────────────────────┘   │ │
│  └───────────┼────────────────────┼─────────────────────────────────────────────┘ │
│              │                    │                                               │
│              ▼                    ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                           模型推理层 (Model Layer)                             │ │
│  │  ┌───────────────────────────┐    ┌───────────────────────────┐              │ │
│  │  │  🔍 YOLO Service          │    │  ⏱️ TSMixer Service        │              │ │
│  │  │  ├─ 图像分块处理           │    │  ├─ 滚动预测               │              │ │
│  │  │  ├─ 实例分割推理           │    │  ├─ 标准化/逆标准化        │              │ │
│  │  │  └─ 指标提取              │    │  └─ 灌水量输出             │              │ │
│  │  └───────────────────────────┘    └───────────────────────────┘              │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                          异常检测层 (Anomaly Layer)                            │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │ │
│  │  │  RangeChecker   │  │ ConflictDetector│  │  EnvAnomalyDet  │              │ │
│  │  │  A1: 范围检测    │  │  A2: 矛盾检测   │  │  A3: 环境异常   │              │ │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │ │
│  └───────────┼────────────────────┼────────────────────┼────────────────────────┘ │
│              │                    │                    │                          │
│              └────────────────────┼────────────────────┘                          │
│                                   ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                           LLM 评估层 (LLM Layer)                               │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │ │
│  │  │  PlantResponse  │  │  SanityCheck    │  │  WeeklySummary  │              │ │
│  │  │  长势评估        │──▶│  合理性复核     │  │  周度反思       │              │ │
│  │  └─────────────────┘  └────────┬────────┘  └─────────────────┘              │ │
│  └────────────────────────────────┼─────────────────────────────────────────────┘ │
│                                   │                                               │
│                                   ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                        4层记忆架构 (Memory Architecture)                       │ │
│  │                                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ L1. Working Context                                    [每次调用构建]    │ │ │
│  │  │     ├─ System Prompt (~500 tokens)                                      │ │ │
│  │  │     ├─ Weekly Context (≤800 tokens) ◄─── L3.prompt_block               │ │ │
│  │  │     ├─ Today Input (~2000 tokens)                                       │ │ │
│  │  │     └─ Retrieval (~1000 tokens) ◄─── L4.TopK检索                        │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ L2. Episodic Log                                       [永久存储]       │ │ │
│  │  │     └─ MongoDB: cucumber_irrigation.episodes                            │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ L3. Recent Summary                                     [永久存储]       │ │ │
│  │  │     └─ MongoDB: cucumber_irrigation.weekly_summaries                    │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ L4. Knowledge Memory                                   [永久存储]       │ │ │
│  │  │     ├─ Milvus: greenhouse_bge_m3 (向量检索)                             │ │ │
│  │  │     └─ MongoDB: greenhouse_db.literature_chunks (文档原文)               │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                               │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                            输出层 (Output Layer)                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │
│  │  │ 💧 灌水量    │  │ ⚠️ 预警信息  │  │ ✏️ Override │  │ 📝 日志记录  │          │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    数据流架构                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                              每日数据流                                       │   │
│  ├─────────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                             │   │
│  │   用户输入                   数据处理                    模型推理              │   │
│  │  ┌───────────────┐        ┌─────────────┐            ┌─────────────┐        │   │
│  │  │ 今日环境数据   │────────▶│ WindowBuilder│────────────▶│  TSMixer   │        │   │
│  │  │ ┌───────────┐ │        │ (96步窗口)   │            │  预测灌水量  │        │   │
│  │  │ │ 来源:     │ │        └──────┬──────┘            └──────┬──────┘        │   │
│  │  │ │ • CSV文件 │ │              │                          │               │   │
│  │  │ │ • 前端输入 │ │              │ 数据不足?                 │               │   │
│  │  │ └───────────┘ │              ▼                          │               │   │
│  │  └───────────────┘        ┌─────────────┐                   │               │   │
│  │       │                  │ColdStartFiller│                  │               │   │
│  │       │                  │ 2023年数据填充 │                  │               │   │
│  │       │                  └─────────────┘                   │               │   │
│  │       │                                                    │               │   │
│  │       ▼                                                    ▼               │   │
│  │  ┌─────────┐            ┌─────────────┐            ┌─────────────┐        │   │
│  │  │ YOLO    │────────────▶│PlantResponse│            │AnomalyDetect│        │   │
│  │  │ 推理    │            │  长势评估    │            │  异常检测   │        │   │
│  │  └─────────┘            └──────┬──────┘            └──────┬──────┘        │   │
│  │                                │                          │               │   │
│  │                                └──────────┬───────────────┘               │   │
│  │                                           ▼                               │   │
│  │                                    ┌─────────────┐                        │   │
│  │                                    │ SanityCheck │                        │   │
│  │                                    │  合理性复核  │                        │   │
│  │                                    └──────┬──────┘                        │   │
│  │                                           │                               │   │
│  │                          ┌────────────────┼────────────────┐              │   │
│  │                          ▼                ▼                ▼              │   │
│  │                   ┌───────────┐    ┌───────────┐    ┌───────────┐        │   │
│  │                   │ 灌水量输出 │    │  预警输出  │    │ Episode   │        │   │
│  │                   │           │    │           │    │  入库     │        │   │
│  │                   └───────────┘    └───────────┘    └───────────┘        │   │
│  │                                                                           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                              每周数据流                                       │   │
│  ├─────────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                             │   │
│  │   ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐    │   │
│  │   │  Episodes   │──────▶│WeeklySummary│──────▶│    prompt_block 生成    │    │   │
│  │   │  (7天)      │      │  周度反思    │      │    (≤800 tokens)        │    │   │
│  │   └─────────────┘      └─────────────┘      └───────────┬─────────────┘    │   │
│  │                                                         │                  │   │
│  │                                                         ▼                  │   │
│  │                                              ┌─────────────────────────┐    │   │
│  │                                              │  注入下周 L1.Weekly     │    │   │
│  │                                              │  Context               │    │   │
│  │                                              └─────────────────────────┘    │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 数据库架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  数据库架构                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  MongoDB 实例 (localhost:27017)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │   │
│  │  │  greenhouse_db (只读访问)        │  │  cucumber_irrigation (业务库)    │  │   │
│  │  │  ────────────────────────────── │  │  ────────────────────────────── │  │   │
│  │  │                                 │  │                                 │  │   │
│  │  │  📚 literature_chunks           │  │  📅 episodes                    │  │   │
│  │  │     ├─ FAO56 文献片段           │  │     ├─ 每日决策记录              │  │   │
│  │  │     ├─ 温室灌溉文献             │  │     ├─ 输入快照                  │  │   │
│  │  │     └─ chunk_id, content,       │  │     ├─ 模型输出                  │  │   │
│  │  │         embedding_id, is_fao56  │  │     └─ date (unique), season     │  │   │
│  │  │                                 │  │                                 │  │   │
│  │  └─────────────────────────────────┘  │  📊 weekly_summaries            │  │   │
│  │                                       │     ├─ 周度统计                  │  │   │
│  │                                       │     ├─ key_insights             │  │   │
│  │                                       │     └─ prompt_block (≤800 tok)  │  │   │
│  │                                       │                                 │  │   │
│  │                                       │  ✏️ overrides                   │  │   │
│  │                                       │     ├─ 人工覆盖记录              │  │   │
│  │                                       │     └─ original, replaced, reason│  │   │
│  │                                       │                                 │  │   │
│  │                                       │  📈 learning_events             │  │   │
│  │                                       │     └─ 偏差>20%的学习事件        │  │   │
│  │                                       │                                 │  │   │
│  │                                       └─────────────────────────────────┘  │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Milvus 实例 (localhost:19530)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │   │
│  │  │  greenhouse_bge_m3 (知识检索)    │  │  cucumber_episodes (可选)       │  │   │
│  │  │  ────────────────────────────── │  │  ────────────────────────────── │  │   │
│  │  │  ├─ BGE-M3 混合检索             │  │  ├─ Episode 向量化              │  │   │
│  │  │  ├─ 稀疏向量 + 稠密向量         │  │  └─ 相似异常检索                │  │   │
│  │  │  └─ 1024 维度                   │  │                                 │  │   │
│  │  └─────────────────────────────────┘  └─────────────────────────────────┘  │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块划分

### 3.1 模块总览

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    模块划分                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  src/cucumber_irrigation/                                                           │
│  │                                                                                  │
│  ├── 📁 core/                          # 核心业务逻辑                                │
│  │   ├── cold_start.py                 # 冷启动数据填充                              │
│  │   ├── window_builder.py             # 时序窗口构建                                │
│  │   ├── anomaly_detector.py           # 异常检测器                                  │
│  │   └── env_input_handler.py          # 环境输入处理 (CSV/前端)                      │
│  │                                                                                  │
│  ├── 📁 memory/                        # 4层记忆架构                                 │
│  │   ├── working_context.py            # L1: 工作上下文构建                          │
│  │   ├── episode_store.py              # L2: Episode 存储                           │
│  │   ├── weekly_summary.py             # L3: 周摘要管理                              │
│  │   ├── knowledge_retriever.py        # L4: 知识检索                               │
│  │   └── budget_controller.py          # Rule-M1: 预算控制                          │
│  │                                                                                  │
│  ├── 📁 services/                      # 外部服务封装                                │
│  │   ├── yolo_service.py               # YOLO 推理服务                              │
│  │   ├── tsmixer_service.py            # TSMixer 预测服务                           │
│  │   ├── llm_service.py                # LLM 调用服务                               │
│  │   ├── rag_service.py                # RAG 检索服务                               │
│  │   └── db_service.py                 # 数据库服务                                  │
│  │                                                                                  │
│  ├── 📁 pipelines/                     # 流程管道                                   │
│  │   ├── daily_pipeline.py             # 每日推理流程                                │
│  │   ├── weekly_pipeline.py            # 每周反思流程                                │
│  │   └── batch_pipeline.py             # 批量处理流程                                │
│  │                                                                                  │
│  ├── 📁 models/                        # 数据模型 (Pydantic)                         │
│  │   ├── episode.py                    # Episode 模型                               │
│  │   ├── plant_response.py             # PlantResponse 模型                         │
│  │   ├── sanity_check.py               # SanityCheck 模型                           │
│  │   ├── weekly_summary.py             # WeeklySummary 模型                         │
│  │   └── anomaly.py                    # 异常类型模型                               │
│  │                                                                                  │
│  └── 📁 utils/                         # 工具函数                                   │
│      ├── token_counter.py              # Token 计数                                 │
│      ├── date_utils.py                 # 日期处理                                   │
│      └── config_loader.py              # 配置加载                                   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  模块依赖关系                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│                              ┌─────────────────┐                                    │
│                              │   pipelines     │                                    │
│                              │  (流程编排层)    │                                    │
│                              └────────┬────────┘                                    │
│                                       │                                             │
│                    ┌──────────────────┼──────────────────┐                         │
│                    │                  │                  │                         │
│                    ▼                  ▼                  ▼                         │
│           ┌────────────────┐  ┌────────────────┐  ┌────────────────┐              │
│           │     core       │  │    memory      │  │   services     │              │
│           │  (核心业务)     │  │  (记忆架构)    │  │  (外部服务)     │              │
│           └────────┬───────┘  └────────┬───────┘  └────────┬───────┘              │
│                    │                   │                   │                       │
│                    └───────────────────┼───────────────────┘                       │
│                                        │                                           │
│                                        ▼                                           │
│                              ┌─────────────────┐                                   │
│                              │     models      │                                   │
│                              │   (数据模型)    │                                   │
│                              └────────┬────────┘                                   │
│                                       │                                            │
│                                       ▼                                            │
│                              ┌─────────────────┐                                   │
│                              │     utils       │                                   │
│                              │   (工具函数)    │                                   │
│                              └─────────────────┘                                   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 组件详细设计

### 4.1 核心组件 (core/)

#### 4.1.1 ColdStartFiller - 冷启动数据填充

```python
class ColdStartFiller:
    """
    冷启动数据填充器

    当用户数据不足96天时，使用2023年春茬数据填充
    """

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
        required_length: int = 96
    ) -> pd.DataFrame:
        """
        填充数据到指定长度

        Args:
            user_data: 用户已有数据
            target_date: 目标预测日期 (2025-03-14)
            required_length: 需要的序列长度 (96)

        Returns:
            填充后的完整数据 (96行)

        Algorithm:
            1. 计算需要填充的天数: fill_days = 95 - len(user_data)
            2. 将目标日期映射到2023年: 2025-03-14 → 2023-03-14
            3. 从参考数据中取 ref_date 之前 fill_days 天
            4. 拼接: [填充数据 | 用户数据 | 今日数据]
        """
        pass

    def _map_date_to_reference_year(self, date: str) -> str:
        """将2025年日期映射到2023年"""
        pass
```

#### 4.1.2 WindowBuilder - 时序窗口构建

```python
class WindowBuilder:
    """
    时序窗口构建器

    构建 TSMixer 所需的 96步×11特征 输入矩阵
    """

    FEATURE_COLUMNS = [
        'temperature', 'humidity', 'light',
        'leaf Instance Count', 'leaf average mask',
        'flower Instance Count', 'flower Mask Pixel Count',
        'terminal average Mask Pixel Count', 'fruit Mask average',
        'all leaf mask', 'Target'
    ]

    def __init__(self, cold_start_filler: ColdStartFiller):
        self.cold_start_filler = cold_start_filler

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

#### 4.1.3 AnomalyDetector - 异常检测器

```python
@dataclass
class AnomalyResult:
    """异常检测结果"""
    out_of_range: bool = False           # A1: 超出历史范围
    trend_conflict: bool = False          # A2: 长势-灌水矛盾
    trend_conflict_severity: str = "none" # none/mild/moderate/severe
    env_anomaly: bool = False             # A3: 环境异常
    env_anomaly_type: Optional[str] = None # high_humidity/high_temperature/low_light

    def has_anomaly(self) -> bool:
        return self.out_of_range or self.trend_conflict or self.env_anomaly


class AnomalyDetector:
    """
    异常检测器

    检测三类异常: A1(范围), A2(矛盾), A3(环境)
    """

    def __init__(self, config: dict):
        self.config = config
        # A1 阈值
        self.irrigation_min = config['irrigation_range']['min']  # 0.1
        self.irrigation_max = config['irrigation_range']['max']  # 15.0
        # A2 阈值
        self.severe_decrease = config['trend_conflict']['severe_decrease_threshold']  # -0.10
        # A3 阈值
        self.consecutive_days = config['env_anomaly']['consecutive_days']  # 3
        self.high_humidity = config['env_anomaly']['high_humidity']  # 85

    def detect(
        self,
        prediction: float,
        yesterday_irrigation: float,
        plant_response: PlantResponse,
        env_history: List[dict]
    ) -> AnomalyResult:
        """
        执行异常检测

        Args:
            prediction: TSMixer 预测值
            yesterday_irrigation: 昨日灌水量
            plant_response: 长势评估结果
            env_history: 近N天环境数据

        Returns:
            AnomalyResult
        """
        result = AnomalyResult()

        # A1: 范围检测
        result.out_of_range = self._check_range(prediction)

        # A2: 矛盾检测
        result.trend_conflict, result.trend_conflict_severity = \
            self._check_conflict(prediction, yesterday_irrigation, plant_response)

        # A3: 环境异常检测
        result.env_anomaly, result.env_anomaly_type = \
            self._check_env_anomaly(env_history)

        return result

    def _check_range(self, prediction: float) -> bool:
        """A1: 检测预测值是否超出历史范围"""
        return prediction < self.irrigation_min or prediction > self.irrigation_max

    def _check_conflict(
        self,
        prediction: float,
        yesterday: float,
        plant_response: PlantResponse
    ) -> Tuple[bool, str]:
        """
        A2: 检测长势-灌水矛盾

        矛盾严重程度:
        - severe: trend=worse 且 灌水减少>10%
        - moderate: trend=worse 且 灌水增加<10%
        - moderate: trend=worse 且 有严重异常 且 灌水增加<20%
        - mild: trend=better 且 灌水增加>30%
        - none: 无矛盾
        """
        change_ratio = (prediction - yesterday) / max(yesterday, 0.1)
        trend = plant_response.comparison.trend
        has_severe_abnormality = (
            plant_response.abnormalities.wilting or
            plant_response.abnormalities.yellowing
        )

        if trend == "worse":
            if change_ratio < self.severe_decrease:
                return True, "severe"
            elif change_ratio < 0.10:
                return True, "moderate"
            elif has_severe_abnormality and change_ratio < 0.20:
                return True, "moderate"
        elif trend == "better":
            if change_ratio > 0.30:
                return True, "mild"

        return False, "none"

    def _check_env_anomaly(self, env_history: List[dict]) -> Tuple[bool, Optional[str]]:
        """A3: 检测连续环境异常"""
        if len(env_history) < self.consecutive_days:
            return False, None

        recent = env_history[-self.consecutive_days:]

        # 高湿检测
        if all(e['humidity'] > self.high_humidity for e in recent):
            return True, "high_humidity"

        # 高温检测
        if all(e['temperature'] > 35 for e in recent):
            return True, "high_temperature"

        # 弱光检测
        if all(e['light'] < 2000 for e in recent):
            return True, "low_light"

        return False, None
```

### 4.2 记忆组件 (memory/)

#### 4.2.1 WorkingContextBuilder - L1 工作上下文构建

```python
@dataclass
class WorkingContext:
    """L1 工作上下文"""
    system_prompt: str
    weekly_context: Optional[str]
    today_input: dict
    retrieval_results: List[str]
    total_tokens: int

    def to_messages(self) -> List[dict]:
        """转换为 LLM messages 格式"""
        pass


class WorkingContextBuilder:
    """
    L1 工作上下文构建器

    组装单次 LLM 调用的完整输入上下文
    """

    def __init__(
        self,
        budget_controller: BudgetController,
        weekly_store: WeeklySummaryStore,
        knowledge_retriever: KnowledgeRetriever
    ):
        self.budget = budget_controller
        self.weekly_store = weekly_store
        self.retriever = knowledge_retriever

    def build(
        self,
        system_prompt: str,
        today_input: dict,
        retrieval_query: Optional[str] = None
    ) -> WorkingContext:
        """
        构建工作上下文

        Budget 分配:
        - System: ~500 tokens (固定)
        - Weekly: ≤800 tokens (prompt_block)
        - Today: ~2000 tokens
        - Retrieval: ~1000 tokens (TopK=3-5)
        - Total: ≤4500 tokens
        """
        # 1. 获取周摘要
        weekly_summary = self.weekly_store.get_latest()
        weekly_context = weekly_summary.prompt_block if weekly_summary else None

        # 2. 执行知识检索
        retrieval_results = []
        if retrieval_query:
            retrieval_results = self.retriever.search(retrieval_query, top_k=3)

        # 3. 预算控制
        context = WorkingContext(
            system_prompt=system_prompt,
            weekly_context=weekly_context,
            today_input=today_input,
            retrieval_results=retrieval_results,
            total_tokens=0
        )

        # 4. 检查并压缩
        context = self.budget.apply(context)

        return context
```

#### 4.2.2 BudgetController - Rule-M1 预算控制

```python
class BudgetController:
    """
    Rule-M1 上下文预算控制器

    控制总上下文不超过预算，超限时按优先级压缩
    """

    def __init__(self, config: dict):
        self.total_max = config['total_max']           # 4500
        self.system_fixed = config['system_fixed']     # 500
        self.weekly_max = config['weekly_max']         # 800
        self.today_max = config['today_max']           # 2000
        self.retrieval_max = config['retrieval_max']   # 1000
        self.compression_priority = config['compression']['priority']
        self.today_keep_fields = config['compression']['today_keep_fields']

    def apply(self, context: WorkingContext) -> WorkingContext:
        """
        应用预算控制

        压缩优先级 (数字越小越先压缩):
        1. Retrieval: TopK 5→3→1→删除
        2. Weekly: 只保留 key_insights
        3. Today: 删除 evidence 详情，保留核心字段
        """
        total = self._count_tokens(context)

        if total <= self.total_max:
            context.total_tokens = total
            return context

        # 按优先级压缩
        for component in sorted(
            self.compression_priority.keys(),
            key=lambda k: self.compression_priority[k]
        ):
            if component == 'retrieval':
                context = self._compress_retrieval(context)
            elif component == 'weekly':
                context = self._compress_weekly(context)
            elif component == 'today':
                context = self._compress_today(context)

            total = self._count_tokens(context)
            if total <= self.total_max:
                break

        context.total_tokens = total
        return context

    def _count_tokens(self, context: WorkingContext) -> int:
        """使用 tiktoken 计算 token 数"""
        pass

    def _compress_retrieval(self, context: WorkingContext) -> WorkingContext:
        """压缩检索结果: 5→3→1→删除"""
        if len(context.retrieval_results) > 3:
            context.retrieval_results = context.retrieval_results[:3]
        elif len(context.retrieval_results) > 1:
            context.retrieval_results = context.retrieval_results[:1]
        else:
            context.retrieval_results = []
        return context

    def _compress_weekly(self, context: WorkingContext) -> WorkingContext:
        """压缩周摘要: 只保留第一条 key_insight"""
        # 实现略
        pass

    def _compress_today(self, context: WorkingContext) -> WorkingContext:
        """压缩今日输入: 只保留核心字段"""
        keep_fields = self.today_keep_fields
        context.today_input = {
            k: v for k, v in context.today_input.items()
            if k in keep_fields
        }
        return context
```

#### 4.2.3 EpisodeStore - L2 Episode 存储

```python
class EpisodeStore:
    """
    L2 Episodic Log 存储

    永久存储每日决策记录，不直接注入 LLM 上下文
    """

    def __init__(self, db_service: DBService):
        self.db = db_service
        self.collection = db_service.get_collection('episodes')

    def save(self, episode: Episode) -> str:
        """保存 Episode"""
        doc = episode.model_dump()
        doc['created_at'] = datetime.utcnow()
        result = self.collection.update_one(
            {'date': episode.date},
            {'$set': doc},
            upsert=True
        )
        return episode.date

    def get_by_date(self, date: str) -> Optional[Episode]:
        """按日期获取"""
        doc = self.collection.find_one({'date': date})
        return Episode.model_validate(doc) if doc else None

    def get_recent(self, days: int = 7) -> List[Episode]:
        """获取最近 N 天"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        docs = self.collection.find(
            {'created_at': {'$gte': cutoff}}
        ).sort('date', -1)
        return [Episode.model_validate(d) for d in docs]

    def search_similar_anomaly(
        self,
        anomaly_type: str,
        growth_stage: str,
        limit: int = 5
    ) -> List[Episode]:
        """检索相似异常案例"""
        query = {
            f'anomalies.{anomaly_type}': True,
            'llm_outputs.plant_response.growth_stage': growth_stage
        }
        docs = self.collection.find(query).limit(limit)
        return [Episode.model_validate(d) for d in docs]
```

#### 4.2.4 WeeklySummaryStore - L3 周摘要管理

```python
class WeeklySummaryStore:
    """
    L3 Recent Summary 存储

    永久存储周摘要，只有 prompt_block 字段被注入 LLM 上下文
    """

    PROMPT_BLOCK_MAX_TOKENS = 800

    def __init__(self, db_service: DBService, token_counter: TokenCounter):
        self.db = db_service
        self.collection = db_service.get_collection('weekly_summaries')
        self.token_counter = token_counter

    def save(self, summary: WeeklySummary) -> str:
        """
        保存周摘要

        保存前检查 prompt_block 是否超限，超限则压缩
        """
        # 检查 prompt_block token 数
        tokens = self.token_counter.count(summary.prompt_block)
        if tokens > self.PROMPT_BLOCK_MAX_TOKENS:
            summary = self._compress_prompt_block(summary)

        summary.prompt_block_tokens = self.token_counter.count(summary.prompt_block)

        doc = summary.model_dump()
        doc['created_at'] = datetime.utcnow()
        self.collection.update_one(
            {'week_start': summary.week_start},
            {'$set': doc},
            upsert=True
        )
        return summary.week_start

    def get_latest(self) -> Optional[WeeklySummary]:
        """获取最新周摘要"""
        doc = self.collection.find_one(sort=[('week_start', -1)])
        return WeeklySummary.model_validate(doc) if doc else None

    def _compress_prompt_block(self, summary: WeeklySummary) -> WeeklySummary:
        """
        压缩 prompt_block 到 ≤800 tokens

        压缩策略:
        1. 删除 override_summary
        2. 只保留 severe 级别异常
        3. 只保留前3条 key_insights
        4. 如仍超限，只保留第1条
        """
        # 只保留 key_insights
        key_insights = summary.key_insights[:3]

        # 重新生成 prompt_block
        prompt_block = self._generate_prompt_block(
            week_start=summary.week_start,
            week_end=summary.week_end,
            key_insights=key_insights
        )

        # 如仍超限，只保留第1条
        if self.token_counter.count(prompt_block) > self.PROMPT_BLOCK_MAX_TOKENS:
            prompt_block = self._generate_prompt_block(
                week_start=summary.week_start,
                week_end=summary.week_end,
                key_insights=key_insights[:1]
            )

        summary.prompt_block = prompt_block
        return summary

    def _generate_prompt_block(
        self,
        week_start: str,
        week_end: str,
        key_insights: List[str]
    ) -> str:
        """生成 prompt_block 文本"""
        lines = [f"## 上周经验 ({week_start} - {week_end})"]
        for insight in key_insights:
            lines.append(f"- {insight}")
        return "\n".join(lines)
```

#### 4.2.5 KnowledgeRetriever - L4 知识检索

```python
class KnowledgeRetriever:
    """
    L4 Knowledge Memory 检索

    从 Greenhouse_RAG 的 Milvus/MongoDB 检索 FAO56 等知识
    """

    def __init__(
        self,
        milvus_client,
        mongo_client,
        embedding_model: str = "BAAI/bge-m3"
    ):
        self.milvus = milvus_client
        self.mongo = mongo_client
        self.collection_name = "greenhouse_bge_m3"
        self.embedding_model = embedding_model

    def search(
        self,
        query: str,
        top_k: int = 3,
        prefer_fao56: bool = True
    ) -> List[RAGResult]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回数量
            prefer_fao56: 是否优先返回 FAO56 内容

        Returns:
            检索结果列表
        """
        # 1. 向量化查询
        query_embedding = self._embed(query)

        # 2. Milvus 检索
        results = self.milvus.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k * 2,  # 多取一些，后续过滤
            output_fields=["doc_id", "is_fao56"]
        )

        # 3. 优先 FAO56
        if prefer_fao56:
            fao56_results = [r for r in results[0] if r.entity.get("is_fao56")]
            other_results = [r for r in results[0] if not r.entity.get("is_fao56")]
            sorted_results = fao56_results + other_results
        else:
            sorted_results = results[0]

        # 4. 获取文档内容
        doc_ids = [r.entity.get("doc_id") for r in sorted_results[:top_k]]
        docs = self._fetch_docs(doc_ids)

        return [
            RAGResult(
                doc_id=doc["_id"],
                snippet=doc["content"],
                relevance_score=sorted_results[i].score,
                source=doc.get("source", "unknown")
            )
            for i, doc in enumerate(docs)
        ]

    def build_anomaly_query(
        self,
        anomaly_result: AnomalyResult,
        plant_response: PlantResponse
    ) -> str:
        """
        根据异常类型构建检索查询

        参考 requirements1.md 3.6 节的查询模板
        """
        if anomaly_result.trend_conflict:
            abnormalities = []
            if plant_response.abnormalities.wilting:
                abnormalities.append("wilting")
            if plant_response.abnormalities.yellowing:
                abnormalities.append("yellowing")

            return (
                f"cucumber water stress irrigation adjustment "
                f"crop coefficient Kc under stress conditions "
                f"plant {' '.join(abnormalities)} water requirement "
                f"growth stage: {plant_response.growth_stage}"
            )

        elif anomaly_result.env_anomaly_type == "high_humidity":
            return "high humidity greenhouse irrigation reduction disease prevention"

        elif anomaly_result.env_anomaly_type == "high_temperature":
            return "high temperature water stress crop evapotranspiration cooling"

        elif anomaly_result.env_anomaly_type == "low_light":
            return "low light photosynthesis reduction irrigation adjustment"

        else:
            return "cucumber irrigation range greenhouse water management"

    def _embed(self, text: str) -> List[float]:
        """文本向量化"""
        pass

    def _fetch_docs(self, doc_ids: List[str]) -> List[dict]:
        """从 MongoDB 获取文档"""
        literature_collection = self.mongo["greenhouse_db"]["literature_chunks"]
        return list(literature_collection.find({"_id": {"$in": doc_ids}}))
```

### 4.3 服务组件 (services/)

#### 4.3.1 TSMixerService - 时序预测服务

```python
class TSMixerService:
    """
    TSMixer 时序预测服务

    封装滚动预测逻辑
    """

    def __init__(
        self,
        model_path: str,
        scaler_path: str,
        window_builder: WindowBuilder,
        device: str = "cuda"
    ):
        self.model = self._load_model(model_path)
        self.scaler = self._load_scaler(scaler_path)
        self.window_builder = window_builder
        self.device = device

    def predict(
        self,
        data: pd.DataFrame,
        target_date: str,
        today_data: Optional[dict] = None
    ) -> float:
        """
        预测灌水量

        Args:
            data: 历史数据
            target_date: 目标日期
            today_data: 今日输入 (可选，用于实时预测)

        Returns:
            预测灌水量 (L/m²)

        流程:
            1. 构建96步窗口 (含冷启动填充)
            2. 标准化
            3. 模型推理
            4. 逆标准化
        """
        # 1. 构建窗口
        window = self.window_builder.build(data, target_date, today_data)

        # 2. 标准化
        window_scaled = self.scaler.transform(window)

        # 3. 转 tensor 并推理
        x = torch.tensor(window_scaled).unsqueeze(0).float().to(self.device)
        with torch.no_grad():
            pred = self.model(x)

        # 4. 逆标准化
        pred_np = pred.cpu().numpy()
        pred_denorm = self._inverse_transform_target(pred_np)

        return float(pred_denorm)

    def _inverse_transform_target(self, pred: np.ndarray) -> float:
        """只对 Target 列进行逆标准化"""
        # Target 是第11列 (index=10)
        target_mean = self.scaler.mean_[10]
        target_std = self.scaler.scale_[10]
        return pred[0, 0, 0] * target_std + target_mean
```

#### 4.3.2 DBService - 数据库服务

```python
class DBService:
    """
    数据库服务

    封装 MongoDB 连接，支持跨库访问
    """

    def __init__(self, uri: str = "mongodb://localhost:27017"):
        self.client = MongoClient(uri)

        # 业务库 (读写)
        self.cucumber_db = self.client["cucumber_irrigation"]

        # 知识库 (只读)
        self.greenhouse_db = self.client["greenhouse_db"]

    def get_collection(self, name: str):
        """获取业务库集合"""
        return self.cucumber_db[name]

    def get_literature_collection(self):
        """获取知识库集合 (只读)"""
        return self.greenhouse_db["literature_chunks"]

    def init_indexes(self):
        """初始化索引"""
        # episodes
        self.cucumber_db["episodes"].create_index("date", unique=True)
        self.cucumber_db["episodes"].create_index("season")

        # weekly_summaries
        self.cucumber_db["weekly_summaries"].create_index("week_start", unique=True)

        # overrides
        self.cucumber_db["overrides"].create_index("date")
        self.cucumber_db["overrides"].create_index([("reason", "text")])
```

---

## 5. 项目结构

### 5.1 完整目录结构

```
cucumber-irrigation/
├── 📁 src/
│   └── 📁 cucumber_irrigation/          # 主包
│       ├── __init__.py
│       │
│       ├── 📁 core/                     # 核心业务
│       │   ├── __init__.py
│       │   ├── cold_start.py            # 冷启动填充
│       │   ├── window_builder.py        # 窗口构建
│       │   └── anomaly_detector.py      # 异常检测
│       │
│       ├── 📁 memory/                   # 4层记忆
│       │   ├── __init__.py
│       │   ├── working_context.py       # L1
│       │   ├── episode_store.py         # L2
│       │   ├── weekly_summary.py        # L3
│       │   ├── knowledge_retriever.py   # L4
│       │   └── budget_controller.py     # Rule-M1
│       │
│       ├── 📁 services/                 # 外部服务
│       │   ├── __init__.py
│       │   ├── yolo_service.py
│       │   ├── tsmixer_service.py
│       │   ├── llm_service.py
│       │   ├── rag_service.py
│       │   └── db_service.py
│       │
│       ├── 📁 pipelines/                # 流程管道
│       │   ├── __init__.py
│       │   ├── daily_pipeline.py
│       │   ├── weekly_pipeline.py
│       │   └── batch_pipeline.py
│       │
│       ├── 📁 models/                   # 数据模型
│       │   ├── __init__.py
│       │   ├── episode.py
│       │   ├── plant_response.py
│       │   ├── sanity_check.py
│       │   ├── weekly_summary.py
│       │   └── anomaly.py
│       │
│       └── 📁 utils/                    # 工具
│           ├── __init__.py
│           ├── token_counter.py
│           ├── date_utils.py
│           └── config_loader.py
│
├── 📁 configs/                          # 配置文件
│   ├── settings.yaml                    # 全局配置
│   ├── thresholds.yaml                  # 阈值配置
│   ├── memory.yaml                      # 记忆配置
│   └── 📁 schema/                       # JSON Schema
│       ├── episode.schema.json
│       └── ...
│
├── 📁 prompts/                          # Prompt 模板
│   ├── 📁 plant_response/
│   ├── 📁 sanity_check/
│   └── 📁 weekly_reflection/
│
├── 📁 data/                             # 数据目录
│   ├── 📁 images/
│   ├── 📁 csv/
│   │   ├── irrigation.csv
│   │   └── irrigation_pre.csv          # 冷启动参考数据
│   └── 📁 processed/
│
├── 📁 tests/                            # 测试
│   ├── 📁 unit/
│   ├── 📁 integration/
│   └── conftest.py
│
├── 📁 scripts/                          # 脚本
│   ├── init_db.py
│   ├── batch_process.py
│   └── eval_consistency.py
│
├── 📁 docs/                             # 文档
│   ├── requirements.md
│   ├── requirements1.md
│   ├── design.md
│   └── design1.md
│
├── pyproject.toml                       # uv 项目配置
├── uv.lock                              # 依赖锁定
├── .env.example                         # 环境变量示例
├── .python-version                      # Python 版本
└── README.md
```

### 5.2 pyproject.toml (uv 配置)

```toml
[project]
name = "cucumber-irrigation"
version = "0.2.0"
description = "温室黄瓜灌水智能体系统"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Wyatt" }
]

dependencies = [
    # Deep Learning
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "ultralytics>=8.0.0",

    # Data Processing
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "openpyxl>=3.1.0",

    # Image Processing
    "opencv-python>=4.8.0",
    "Pillow>=10.0.0",

    # Database
    "pymongo>=4.5.0",
    "pymilvus>=2.3.0",

    # LLM & Embeddings
    "openai>=1.3.0",
    "tiktoken>=0.5.0",
    "FlagEmbedding>=1.2.0",

    # Configuration
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",

    # Data Validation
    "pydantic>=2.5.0",

    # Logging
    "loguru>=0.7.0",

    # HTTP Client
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "ipython>=8.0.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## 6. 依赖管理

### 6.1 使用 uv 管理依赖

```bash
# 安装 uv (如果未安装)
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或者使用 pip
pip install uv
```

### 6.2 项目初始化

```bash
# 进入项目目录
cd cucumber-irrigation

# 初始化 uv 项目 (如果从头开始)
uv init

# 同步依赖 (根据 pyproject.toml)
uv sync

# 安装开发依赖
uv sync --dev
```

### 6.3 依赖操作

```bash
# 添加依赖
uv add pandas numpy torch

# 添加开发依赖
uv add --dev pytest ruff

# 移除依赖
uv remove pandas

# 更新依赖
uv lock --upgrade

# 查看依赖树
uv tree
```

### 6.4 运行命令

```bash
# 运行 Python 脚本
uv run python src/cucumber_irrigation/main.py

# 运行测试
uv run pytest

# 运行特定模块
uv run python -m cucumber_irrigation.pipelines.daily_pipeline
```

### 6.5 虚拟环境

```bash
# uv 自动管理虚拟环境在 .venv/
# 激活虚拟环境 (可选，uv run 自动使用)
# Windows
.venv\Scripts\activate

# 查看当前 Python
uv run python --version
```

---

## 7. 配置文件

### 7.1 configs/settings.yaml

```yaml
# 全局配置
app:
  name: "cucumber-irrigation-agent"
  version: "0.2.0"
  log_level: "INFO"
  log_dir: "logs/"

# 数据路径
data:
  images_dir: "data/images/"
  csv_path: "data/csv/irrigation.csv"
  cold_start_csv: "data/csv/irrigation_pre.csv"
  processed_dir: "data/processed/"

# 模型配置
models:
  yolo:
    weight_path: "../v11_4seg/runs/segment/exp21/weights/best.pt"
    device: "cuda"
  tsmixer:
    weight_path: "../Irrigation/model.pt"
    scaler_path: "../Irrigation/scaler.pkl"
    seq_len: 96
    pred_len: 1
    feature_dim: 11

# 数据库配置
database:
  mongodb:
    uri: "mongodb://localhost:27017"
    business_db: "cucumber_irrigation"
    knowledge_db: "greenhouse_db"
  milvus:
    host: "localhost"
    port: 19530
    collection: "greenhouse_bge_m3"

# LLM 配置
llm:
  base_url: "https://yunwu.ai/v1"
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 2000
```

### 7.2 configs/thresholds.yaml

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

### 7.3 configs/memory.yaml

```yaml
# 上下文预算配置
context_budget:
  total_max: 4500
  system_fixed: 500
  weekly_max: 800
  today_max: 2000
  retrieval_max: 1000
  retrieval_default_k: 3

# 压缩配置
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

# 周摘要配置
weekly_summary:
  prompt_block_max_tokens: 800
  max_key_insights: 5
```

### 7.4 .env.example

```bash
# LLM API
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://yunwu.ai/v1

# MongoDB
MONGODB_URI=mongodb://localhost:27017

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# GPU 设备
CUDA_VISIBLE_DEVICES=0

# 日志级别
LOG_LEVEL=INFO
```

---

## 8. 验收对照

| 需求编号 | 需求描述 | 设计组件 | 验收标准 |
|----------|----------|----------|----------|
| Q1 | TSMixer 滚动预测与冷启动 | ColdStartFiller, WindowBuilder, TSMixerService | 输入96步输出单值，冷启动自动填充 |
| Q2 | 异常检测与 RAG 辅助 | AnomalyDetector, KnowledgeRetriever | A1/A2/A3 检测 + FAO56 检索 |
| Q3 | 4层记忆架构 | memory/ 模块 | L1-L4 分层存储与检索 |
| Q4 | 上下文预算控制 | BudgetController | 总上下文≤4500 tokens |
| Q5 | 同实例分库 | DBService | cucumber_irrigation + greenhouse_db |
| Q6 | 周总结动态注入 | WeeklySummaryStore | prompt_block≤800 tokens |

---

## 9. 附录

### 9.1 核心类型定义

```python
# models/anomaly.py
from pydantic import BaseModel
from typing import Optional, Literal

class AnomalyResult(BaseModel):
    """异常检测结果"""
    out_of_range: bool = False
    trend_conflict: bool = False
    trend_conflict_severity: Literal["none", "mild", "moderate", "severe"] = "none"
    env_anomaly: bool = False
    env_anomaly_type: Optional[Literal["high_humidity", "high_temperature", "low_light"]] = None

    def has_anomaly(self) -> bool:
        return self.out_of_range or self.trend_conflict or self.env_anomaly


class RAGResult(BaseModel):
    """RAG 检索结果"""
    doc_id: str
    snippet: str
    relevance_score: float
    source: str
    is_fao56: bool = False
```

### 9.2 开发命令速查

```bash
# 依赖管理
uv sync                      # 同步依赖
uv add <package>             # 添加依赖
uv add --dev <package>       # 添加开发依赖

# 运行
uv run python <script>       # 运行脚本
uv run pytest                # 运行测试
uv run ruff check .          # 代码检查
uv run mypy src/             # 类型检查

# 格式化
uv run ruff format .         # 格式化代码
```
