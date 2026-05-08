# AgriAgent - 温室黄瓜智能灌溉决策系统

## 项目技术文档 (Project Technical Documentation)

> **📌 版本说明**: 本文档针对 `cucumber-irrigation-linux` 项目版本
>
> 与 Windows 版本 (`cucumber-irrigation`) 的主要差异：
> - **启动脚本**: 使用 Bash 脚本 (`start.sh`, `status.sh`, `stop.sh`) 而非 PowerShell
> - **前端端口**: 默认 3003 (Windows 版为 3000)
> - **后端虚拟环境**: 预配置于 `backend/.venv/`
> - **数据目录结构**: 包含结构化子目录 (`coldstart/`, `csv/`, `demo_storage/`)
> - **项目文档**: 包含 198 个 `DIRECTORY.md` 文件，提供详细的目录级文档

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [技术路线图](#3-技术路线图)
4. [目录结构详解](#4-目录结构详解)
5. [前后端分离实现](#5-前后端分离实现)
6. [核心模块详解](#6-核心模块详解)
7. [数据流与通信机制](#7-数据流与通信机制)
8. [AI/ML 模型集成](#8-aiml-模型集成)
9. [4层记忆架构](#9-4层记忆架构)
10. [部署与运行](#10-部署与运行)
11. [论文结构建议](#11-论文结构建议)

---

## 1. 项目概述

### 1.1 项目目的

**AgriAgent** 是一个面向温室黄瓜种植的智能灌溉决策支持系统，旨在：

1. **精准灌溉预测** - 基于时序混合模型 (TSMixer) 预测每日最优灌水量
2. **多模态长势评估** - 结合计算机视觉 (YOLO11) 和大语言模型 (GPT) 评估植株生长状态
3. **知识增强决策** - 集成 FAO56 标准知识库，提供科学依据支撑
4. **人机协同** - 支持人工覆盖与反馈，持续优化决策质量
5. **经验积累** - 4层记忆架构实现知识的持久化与跨周期复用

### 1.2 核心创新点

| 创新点 | 描述 |
|--------|------|
| **多模态融合** | 环境传感器 + 图像分析 + 时序预测 + LLM 推理 |
| **4层记忆架构** | L1 工作上下文 → L2 日志 → L3 周摘要 → L4 知识库 |
| **三级异常检测** | A1 范围检测 → A2 趋势矛盾 → A3 环境异常 |
| **RAG 知识增强** | FAO56 向量检索 + 动态 Prompt 注入 |
| **12步决策流水线** | 端到端自动化决策链路 |

### 1.3 技术栈概览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Frontend)                       │
├─────────────────────────────────────────────────────────────┤
│  React 19 + TypeScript + Vite + Tailwind CSS + Zustand     │
│  TanStack Query + Chart.js + React Router DOM              │
└─────────────────────────────────────────────────────────────┘
                              ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                        后端 (Backend)                        │
├─────────────────────────────────────────────────────────────┤
│  FastAPI + Uvicorn + Pydantic + Python 3.11+               │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      AI/ML 服务层                            │
├─────────────────────────────────────────────────────────────┤
│  YOLO11 (实例分割) + TSMixer (时序预测) + GPT-5.2 (推理)    │
│  BGE-M3 (向量化) + Milvus (向量数据库)                      │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
├─────────────────────────────────────────────────────────────┤
│  MongoDB (主存储) / JSON (Fallback) + Milvus (向量)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构

### 2.1 整体架构图

```
                    ┌──────────────────────────────────────┐
                    │           用户界面层                  │
                    │   React SPA (Dashboard/Chat/Vision)  │
                    └──────────────────┬───────────────────┘
                                       │ HTTP/REST
                    ┌──────────────────▼───────────────────┐
                    │           API 网关层                  │
                    │   FastAPI + CORS + 静态文件服务       │
                    └──────────────────┬───────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
┌─────────▼─────────┐     ┌────────────▼────────────┐    ┌──────────▼──────────┐
│   业务逻辑服务     │     │      AI/ML 服务         │    │    知识检索服务      │
│                   │     │                         │    │                     │
│ • EpisodeService  │     │ • YOLOService           │    │ • RAGService        │
│ • WeeklyService   │     │ • TSMixerService        │    │ • KnowledgeRetriever│
│ • MemoryService   │     │ • LLMService            │    │ • Embedder          │
│ • PredictionSvc   │     │ • PlantResponseGen      │    │ • MultiSourceSearch │
└─────────┬─────────┘     └────────────┬────────────┘    └──────────┬──────────┘
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │           核心业务层                  │
                    │                                      │
                    │  DailyPipeline (12步决策流程)         │
                    │  WeeklyPipeline (周度总结)            │
                    │  AnomalyDetector (三级异常检测)       │
                    │  BudgetController (Token预算控制)    │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │         4层记忆架构                   │
                    │                                      │
                    │  L1: WorkingContext (单次调用)       │
                    │  L2: EpisodeStore (每日日志)         │
                    │  L3: WeeklySummaryStore (周摘要)     │
                    │  L4: KnowledgeBase (FAO56知识库)     │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │         持久化存储层                  │
                    │                                      │
                    │  MongoDB + Milvus + JSON Files       │
                    └──────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
frontend/
    ↓ 调用
backend/app/api/v1/
    ↓ 调用
backend/app/services/
    ↓ 调用
src/cucumber_irrigation/
    ├── pipelines/     ← 核心流程编排
    ├── services/      ← 基础服务
    ├── core/          ← 业务逻辑
    ├── memory/        ← 4层记忆
    ├── rag/           ← 知识检索
    └── models/        ← 数据模型
```

---

## 3. 技术路线图

### 3.1 决策流程技术路线

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          每日决策流程 (DailyPipeline)                        │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: 数据采集
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  环境传感器      │    │   监控摄像头     │    │   历史数据库     │
│  温度/湿度/光照  │    │   今日/昨日图像  │    │   CSV/MongoDB   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
Step 2: 特征工程
┌─────────────────────────────────────────────────────────────────────────────┐
│  WindowBuilder: 构建 96步 × 11特征 时序窗口                                  │
│  ├─ 环境特征: temperature, humidity, light                                  │
│  ├─ 视觉特征: leaf_count, leaf_mask, flower_count, flower_mask, ...        │
│  └─ 目标特征: historical_irrigation                                         │
│                                                                             │
│  ColdStartFiller: 新温室冷启动数据填充                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                ▼
Step 3: 多模态推理
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│    YOLO11 实例分割     │  │   TSMixer 时序预测    │  │   GPT-5.2 长势评估    │
│                       │  │                       │  │                       │
│ 输入: 3200×1920 图像  │  │ 输入: [96, 11] 窗口   │  │ 输入: 今/昨日图像     │
│ 输出: 叶/花/果指标    │  │ 输出: 预测灌水量      │  │      + YOLO指标       │
│      + 分割可视化     │  │      (L/m²)          │  │ 输出: PlantResponse   │
└───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       ▼
Step 4: 异常检测 (三级)
┌─────────────────────────────────────────────────────────────────────────────┐
│  A1 OutOfRange: 预测值 ∉ [0.1, 15.0] L/m²                                   │
│  A2 TrendConflict: 长势↑ 但灌水↓ / 有异常但灌水不增                          │
│  A3 EnvAnomaly: 连续3天高温/高湿/低光                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
Step 5: 知识增强
┌─────────────────────────────────────────────────────────────────────────────┐
│  RAG检索: 根据长势+异常构建查询 → Milvus向量检索 → Top-K知识片段             │
│  知识源: FAO56 (10,211块) + 用户文献                                         │
│  向量化: BGE-M3 (1024维) + 混合检索 (稀疏+稠密)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
Step 6: 上下文构建 (L1)
┌─────────────────────────────────────────────────────────────────────────────┐
│  WorkingContext = SystemPrompt + WeeklyContext + TodayInput + RAGResults    │
│                                                                             │
│  BudgetController: Token预算 ≤ 4500                                         │
│  ├─ SystemPrompt: ~500 tokens (固定)                                        │
│  ├─ WeeklyContext: ≤800 tokens (L3 prompt_block)                           │
│  ├─ TodayInput: ≤2000 tokens (当日数据)                                     │
│  └─ RAGResults: ≤1000 tokens (检索结果)                                     │
│                                                                             │
│  压缩策略: retrieval_k↓ → weekly简化 → today精简                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
Step 7: 合理性复核 (SanityCheck)
┌─────────────────────────────────────────────────────────────────────────────┐
│  LLM 判断: TSMixer预测 + 长势评估 + 异常结果 + 知识参考                       │
│  输出决策: Accept (采纳) / Adjust (微调) / Reject (拒绝)                     │
│  附加信息: adjustment值, confidence, questions                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
Step 8: 最终决策 & 存储
┌─────────────────────────────────────────────────────────────────────────────┐
│  FinalDecision: {value: 5.2, source: "tsmixer" | "adjusted" | "override"}   │
│                                                                             │
│  Episode 存储 (L2):                                                         │
│  ├─ 输入快照: environment, yolo_metrics, image_path                         │
│  ├─ 模型输出: tsmixer_raw, plant_response, sanity_check, growth_stage       │
│  ├─ 异常结果: out_of_range, trend_conflict, env_anomaly                     │
│  ├─ 最终决策: value, source, override_reason                                │
│  └─ 知识引用: rag_doc_ids, knowledge_references                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 周度流程技术路线

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          周度总结流程 (WeeklyPipeline)                       │
└─────────────────────────────────────────────────────────────────────────────┘

1. 数据聚合
   └─ 查询7天Episodes → 统计分析

2. 统计计算
   ├─ TrendStats: better_days, same_days, worse_days
   ├─ IrrigationStats: total, average, min, max, trend
   ├─ AnomalyEvents: [date, type, description]
   └─ OverrideSummary: count, reasons

3. 知识检索
   └─ 根据统计构建查询 → RAG检索相关知识

4. LLM洞察生成
   └─ 输入: 统计摘要 + 知识上下文
   └─ 输出: 3-5条 Key Insights

5. Prompt Block 生成
   └─ 格式化为下周注入的上下文片段
   └─ Token检查与压缩 (≤800)

6. 存储 (L3)
   └─ WeeklySummary → MongoDB/JSON
```

---

## 4. 目录结构详解

### 4.1 项目根目录

```
cucumber-irrigation-linux/
│
├── backend/                    # FastAPI 后端服务 (含预配置 .venv)
├── frontend/                   # React 前端应用 (含 dist/ 构建产物)
├── src/cucumber_irrigation/    # Python 核心库
├── configs/                    # YAML 配置文件
├── data/                       # 数据目录 (结构化子目录)
├── models/                     # 预训练模型
├── prompts/                    # LLM Prompt 模板
├── output/                     # 输出目录
├── logs/                       # 运行日志目录
│
├── pyproject.toml              # Python 项目配置 (uv)
├── config.ini                  # 启动配置
├── start.sh                    # Linux 一键启动脚本
├── status.sh                   # 服务状态检查脚本
├── stop.sh                     # 服务停止脚本
├── DIRECTORY.md                # 目录结构文档
├── PROJECT_DOCUMENTATION.md    # 本技术文档
└── README.md                   # 项目说明
```

> **DIRECTORY.md 文件**: Linux 版本在项目各个目录中包含 198 个 `DIRECTORY.md` 文件，
> 提供详细的目录级文档说明，便于理解项目结构。

### 4.2 后端目录 (`backend/`)

```
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   │                           # - CORS 配置
│   │                           # - 路由注册
│   │                           # - 生命周期管理
│   │
│   ├── api/v1/                 # API 路由层 (11个模块)
│   │   ├── episodes.py         # GET /episodes - 决策记录查询
│   │   ├── predict.py          # POST /predict - 灌水量预测
│   │   ├── vision.py           # POST /vision/analyze - YOLO分析
│   │   ├── knowledge.py        # GET /knowledge/search - 知识检索
│   │   ├── weekly.py           # GET /weekly - 周摘要
│   │   ├── stats.py            # GET /stats - 统计数据
│   │   ├── override.py         # POST /override - 人工覆盖
│   │   ├── chat.py             # POST /chat - 对话接口
│   │   ├── upload.py           # POST /upload - 文件上传
│   │   ├── settings.py         # GET/POST /settings - 配置管理
│   │   └── models/             # Pydantic 请求/响应模型
│   │
│   └── services/               # 服务层 (9个服务)
│       ├── yolo_service.py     # YOLO11 实例分割服务
│       ├── tsmixer_service.py  # TSMixer 时序预测服务
│       ├── llm_service.py      # LLM API 调用服务
│       ├── rag_service.py      # RAG 检索服务
│       ├── episode_service.py  # Episode CRUD 服务
│       ├── weekly_service.py   # 周摘要服务
│       ├── memory_service.py   # 记忆管理服务
│       └── prediction_service.py # 预测编排服务
│
└── requirements.txt            # Python 依赖
```

### 4.3 前端目录 (`frontend/`)

```
frontend/
├── src/
│   ├── main.tsx                # React 入口
│   │
│   ├── routes/
│   │   └── index.tsx           # 路由配置 (10条路由)
│   │
│   ├── pages/                  # 页面组件 (10个)
│   │   ├── Dashboard.tsx       # 主仪表板 - 最新决策展示
│   │   ├── DailyDecision.tsx   # 每日决策详情
│   │   ├── History.tsx         # 历史记录查询
│   │   ├── Knowledge.tsx       # 知识库问答 (Chat UI)
│   │   ├── PlantResponse.tsx   # 长势评估详情
│   │   ├── Vision.tsx          # YOLO 图像分析
│   │   ├── Predict.tsx         # 灌水预测
│   │   ├── Weekly.tsx          # 周报告
│   │   ├── Settings.tsx        # 系统设置
│   │   └── NotFound.tsx        # 404 页面
│   │
│   ├── components/             # UI 组件库
│   │   ├── common/             # 基础组件
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   ├── Badge/
│   │   │   └── ...
│   │   ├── layout/             # 布局组件
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar/
│   │   │   ├── Header.tsx
│   │   │   └── AuroraBackground.tsx  # 极光背景效果
│   │   ├── chat/               # 聊天组件
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── vision/             # 视觉分析组件
│   │   ├── prediction/         # 预测组件
│   │   ├── plant-response/     # 长势评估组件
│   │   └── charts/             # 图表组件
│   │
│   ├── stores/                 # Zustand 状态管理
│   │   └── chatStore.ts        # 聊天状态 (消息/流式/历史)
│   │
│   ├── services/               # API 客户端
│   │   ├── api.ts              # Axios 配置
│   │   ├── episodeService.ts
│   │   ├── weeklyService.ts
│   │   ├── knowledgeService.ts
│   │   ├── imageService.ts
│   │   └── predictService.ts
│   │
│   ├── hooks/                  # React Hooks
│   │   ├── useEpisodes.ts
│   │   ├── useDailyPredict.ts
│   │   ├── useKnowledgeSearch.ts
│   │   └── useWeeklySummary.ts
│   │
│   ├── types/                  # TypeScript 类型定义
│   │   ├── api.ts
│   │   ├── episode.ts
│   │   ├── knowledge.ts
│   │   └── predict.ts
│   │
│   ├── utils/                  # 工具函数
│   │   ├── constants.ts
│   │   ├── export.ts
│   │   └── index.ts
│   │
│   └── styles/                 # 样式文件
│       ├── index.css           # Tailwind 入口
│       └── cankao.css          # Gemini 设计系统
│
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

### 4.4 核心库目录 (`src/cucumber_irrigation/`)

```
src/cucumber_irrigation/
│
├── models/                     # 数据模型 (Dataclass)
│   ├── episode.py              # Episode 完整模型
│   ├── plant_response.py       # PlantResponse 模型
│   ├── env_input.py            # 环境输入模型
│   ├── anomaly.py              # 异常检测模型
│   ├── weekly_summary.py       # 周摘要模型
│   ├── yolo_metrics.py         # YOLO 指标模型
│   └── ...
│
├── services/                   # 基础服务
│   ├── llm_service.py          # OpenAI 兼容 API 调用
│   ├── tsmixer_service.py      # TSMixer 模型推理
│   ├── image_service.py        # 图像处理
│   ├── db_service.py           # 数据库连接
│   └── rag_service.py          # 知识检索
│
├── core/                       # 核心业务逻辑
│   ├── env_input_handler.py    # 环境数据处理
│   ├── window_builder.py       # 时序窗口构建
│   ├── anomaly_detector.py     # 三级异常检测
│   ├── cold_start.py           # 冷启动填充
│   ├── growth_stage_detector.py # 生育期检测
│   └── __init__.py
│
├── memory/                     # 4层记忆架构
│   ├── budget_controller.py    # L1 Token预算控制
│   ├── working_context.py      # L1 工作上下文构建
│   ├── episode_store.py        # L2 Episode存储
│   ├── weekly_summary_store.py # L3 周摘要存储
│   └── knowledge_retriever.py  # L4 知识检索
│
├── pipelines/                  # 流程编排
│   ├── daily_pipeline.py       # 每日决策流程
│   └── weekly_pipeline.py      # 周度总结流程
│
├── rag/                        # RAG 模块
│   ├── embedder.py             # BGE-M3 向量化
│   ├── retriever.py            # 多源检索器
│   ├── chunker.py              # 文本分块
│   ├── indexer.py              # 索引管理
│   ├── cli.py                  # 命令行工具
│   └── json_store.py           # JSON 本地存储
│
├── processors/                 # 数据处理器
│
├── utils/                      # 工具函数
│
└── config.py                   # 配置加载
```

### 4.5 配置目录 (`configs/`)

```
configs/
├── settings.yaml               # 全局设置
│   # - LLM API 配置
│   # - 数据路径配置
│   # - 输出路径配置
│   # - Prompt 版本配置
│
├── memory.yaml                 # 4层记忆配置
│   # - Token 预算分配
│   # - 压缩策略优先级
│   # - 字段保留规则
│
├── thresholds.yaml             # 异常检测阈值
│   # - 灌水范围 [min, max]
│   # - 趋势矛盾阈值
│   # - 环境异常阈值
│
├── rag.yaml                    # RAG 配置
│   # - Milvus 连接配置
│   # - 向量化模型配置
│   # - 检索权重配置
│
├── rules.yaml                  # 业务规则
│
└── knowledge_enhancement.yaml  # 知识增强配置
```

### 4.6 数据目录 (`data/`)

```
data/
├── images/                     # 监控图像 (116张)
│   └── *.jpg                   # 3200×1920 高分辨率
│
├── coldstart/                  # 冷启动数据
│   ├── irrigation_final_11.17.xlsx  # 历史灌溉数据
│   └── DIRECTORY.md
│
├── csv/                        # CSV 数据文件
│   ├── irrigation.csv          # 灌溉历史数据
│   ├── env.csv                 # 环境传感器数据
│   ├── irrigation_pre.csv      # 参考数据
│   └── DIRECTORY.md
│
├── demo_storage/               # 演示/示例存储
│   ├── episodes.json           # L2 Episode JSON存储
│   ├── weekly.json             # L3 周摘要JSON存储
│   └── DIRECTORY.md
│
└── knowledge_base/
    └── fao56_chunks.json       # FAO56 知识库 (10,211块)
```

> **注意**: Linux 版本的数据目录结构更加规范，包含 `coldstart/`、`csv/`、`demo_storage/` 等子目录，
> 每个目录都附带 `DIRECTORY.md` 文档说明其用途。

### 4.7 模型目录 (`models/`)

```
models/
├── yolo/
│   └── yolo11_seg_best.pt      # YOLO11 实例分割模型
│                               # - 任务: Instance Segmentation
│                               # - 类别: Leaf, Flower, Fruit, Terminal
│                               # - 输入: 640×640 (Tile处理)
│
└── tsmixer/
    ├── TSMixer.py              # 模型架构定义
    ├── tsmixer_irrigation.pt   # 完整模型文件
    └── model.pt                # 权重文件
                                # - 输入: [Batch, 96, 11]
                                # - 输出: [Batch, 1, 1]
```

### 4.8 Prompt 目录 (`prompts/`)

```
prompts/
├── plant_response/             # 长势评估 Prompt
│   ├── system_v1.txt           # 系统角色定义
│   ├── system_v1.md            # Markdown 版本
│   ├── user_v1.txt             # 用户输入模板
│   ├── user_v1.md              # Markdown 版本
│   └── examples_v1.jsonl       # Few-shot 示例
│
├── sanity_check/               # 合理性复核 Prompt
│   ├── system.txt
│   └── user.txt
│
└── weekly_reflection/          # 周度反思 Prompt
    ├── system.txt
    └── user.txt
```

---

## 5. 前后端分离实现

### 5.1 分离架构设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端 (React SPA)                                │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Dashboard  │    │   History   │    │  Knowledge  │    │   Vision    │  │
│  │    页面     │    │     页面    │    │     页面    │    │     页面    │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│  ┌──────▼──────────────────▼──────────────────▼──────────────────▼──────┐  │
│  │                        服务层 (services/)                             │  │
│  │  episodeService.ts  |  knowledgeService.ts  |  imageService.ts       │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                      │
│  ┌──────────────────────────────────▼───────────────────────────────────┐  │
│  │                        Axios 客户端 (api.ts)                          │  │
│  │  baseURL: http://localhost:8000/api                                  │  │
│  │  timeout: 30s | retry: 3 | interceptors: error handling             │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
                              HTTP/REST API
                              (JSON 数据交换)
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────┐
│                              后端 (FastAPI)                                  │
│                                     │                                       │
│  ┌──────────────────────────────────▼───────────────────────────────────┐  │
│  │                        CORS 中间件                                    │  │
│  │  origins: [3000, 3001, 3002, 3003, 5173]                             │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                      │
│  ┌──────────────────────────────────▼───────────────────────────────────┐  │
│  │                        路由层 (api/v1/)                               │  │
│  │  /episodes | /predict | /vision | /knowledge | /weekly | ...         │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                      │
│  ┌──────────────────────────────────▼───────────────────────────────────┐  │
│  │                        服务层 (services/)                             │  │
│  │  YOLOService | TSMixerService | LLMService | RAGService | ...        │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                      │
│  ┌──────────────────────────────────▼───────────────────────────────────┐  │
│  │                        核心库 (src/cucumber_irrigation/)              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 API 设计规范

#### 统一响应格式

```typescript
// 成功响应
interface ApiResponse<T> {
  success: true;
  data: T;
  timestamp: string;
}

// 错误响应
interface ApiErrorResponse {
  success: false;
  error: {
    code: string;      // "NOT_FOUND" | "VALIDATION_ERROR" | ...
    message: string;   // 人类可读错误信息
  };
  timestamp: string;
}

// 分页响应
interface PaginatedResponse<T> {
  success: true;
  data: {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
  timestamp: string;
}
```

#### RESTful 端点设计

| HTTP Method | 端点 | 描述 | 请求体 | 响应 |
|-------------|------|------|--------|------|
| GET | `/api/episodes` | 查询决策记录 | Query Params | PaginatedResponse<Episode> |
| GET | `/api/episodes/latest` | 获取最新记录 | - | ApiResponse<Episode> |
| GET | `/api/episodes/{date}` | 按日期查询 | - | ApiResponse<Episode> |
| POST | `/api/predict` | 灌水预测 | PredictRequest | ApiResponse<PredictResult> |
| POST | `/api/vision/analyze` | 图像分析 | FormData (file) | ApiResponse<VisionResult> |
| GET | `/api/knowledge/search` | 知识检索 | Query Params | ApiResponse<KnowledgeResults> |
| GET | `/api/weekly` | 周摘要 | Query Params | ApiResponse<WeeklySummary> |
| POST | `/api/override` | 人工覆盖 | OverrideRequest | ApiResponse<Episode> |
| GET | `/api/settings` | 获取配置 | - | ApiResponse<Settings> |
| POST | `/api/settings` | 更新配置 | Settings | ApiResponse<Settings> |

### 5.3 前端状态管理

#### Zustand Store (聊天状态)

```typescript
// stores/chatStore.ts
interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  error: string | null;

  // Actions
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
}

const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  error: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateLastMessage: (content) => set((state) => ({
    messages: state.messages.map((msg, i) =>
      i === state.messages.length - 1
        ? { ...msg, content: msg.content + content }
        : msg
    )
  })),

  // ...
}));
```

#### TanStack Query (数据获取)

```typescript
// hooks/useEpisodes.ts
export const useEpisodes = (params: EpisodeQueryParams) => {
  return useQuery({
    queryKey: ['episodes', params],
    queryFn: () => episodeService.getEpisodes(params),
    staleTime: 5 * 60 * 1000,  // 5分钟缓存
    refetchOnWindowFocus: false,
  });
};

export const useLatestEpisode = () => {
  return useQuery({
    queryKey: ['episodes', 'latest'],
    queryFn: () => episodeService.getLatest(),
    refetchInterval: 30 * 1000,  // 30秒自动刷新
  });
};
```

### 5.4 跨域配置

#### 后端 CORS (FastAPI)

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",   # Vite 开发服务器
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",   # Vite 默认端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 前端环境变量

```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api

# frontend/.env.production
VITE_API_BASE_URL=https://api.example.com/api
```

---

## 6. 核心模块详解

### 6.1 YOLO11 实例分割服务

```python
# backend/app/services/yolo_service.py

class YOLOService:
    """YOLO11 实例分割服务 (Singleton)"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if YOLOService._model is None:
            self._model = YOLO("models/yolo/yolo11_seg_best.pt")

    def process_image(self, image_path: str, conf: float = 0.25) -> dict:
        """
        处理单张图像

        Args:
            image_path: 图像路径
            conf: 置信度阈值

        Returns:
            {
                "metrics": {
                    "leaf_instance_count": 12,
                    "leaf_average_mask": 1250,
                    "flower_instance_count": 5,
                    ...
                },
                "visualization": <base64>,
                "filename": "..."
            }
        """
        # 1. 读取图像
        image = cv2.imread(image_path)

        # 2. Tile 推理 (3200x1920 → 5x3 tiles)
        results = self._tile_inference(image, conf)

        # 3. 提取指标
        metrics = self._extract_metrics(results)

        # 4. 生成可视化
        vis_image = self._visualize(image, results)
        vis_base64 = self._to_base64(vis_image)

        return {
            "metrics": metrics,
            "visualization": vis_base64,
            "filename": Path(image_path).stem
        }
```

### 6.2 TSMixer 时序预测服务

```python
# src/cucumber_irrigation/services/tsmixer_service.py

class TSMixerService:
    """TSMixer 时序预测服务"""

    def __init__(self, model_path: str, scaler_path: str = None):
        self.model = self._load_model(model_path)
        self.scaler = self._load_scaler(scaler_path)

    def predict(self, window: np.ndarray) -> float:
        """
        预测灌水量

        Args:
            window: [96, 11] 时序窗口

        Returns:
            预测的灌水量 (L/m²)
        """
        # 1. 标准化
        window_scaled = self.scaler.transform(window)

        # 2. 转换为 Tensor
        x = torch.tensor(window_scaled, dtype=torch.float32)
        x = x.unsqueeze(0)  # [1, 96, 11]

        # 3. 推理
        with torch.no_grad():
            pred = self.model(x)  # [1, 1, 1]

        # 4. 逆标准化
        pred_value = pred.squeeze().item()
        irrigation = self.scaler.inverse_transform_target(pred_value)

        return round(irrigation, 2)
```

### 6.3 LLM 服务 (多模态)

```python
# src/cucumber_irrigation/services/llm_service.py

class LLMService:
    """OpenAI 兼容 LLM 服务"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://yunwu.zeabur.app/v1",
        model: str = "gpt-5.2",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_plant_response(
        self,
        system_prompt: str,
        user_prompt: str,
        image_today_b64: str,
        image_yesterday_b64: str,
        examples: List[dict] = None
    ) -> str:
        """
        生成长势评估 (多模态)

        Args:
            system_prompt: 系统角色定义
            user_prompt: 用户输入模板
            image_today_b64: 今日图像 Base64
            image_yesterday_b64: 昨日图像 Base64
            examples: Few-shot 示例

        Returns:
            PlantResponse JSON 字符串
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Few-shot 示例
        if examples:
            for ex in examples:
                messages.append({"role": "user", "content": ex["user"]})
                messages.append({"role": "assistant", "content": ex["assistant"]})

        # 多模态用户消息
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_today_b64}"}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_yesterday_b64}"}
                }
            ]
        })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content
```

### 6.4 RAG 检索服务

```python
# src/cucumber_irrigation/rag/retriever.py

class MultiSourceRetriever:
    """多源知识检索器"""

    def __init__(self, milvus_uri: str, embedder: BGEEmbedder):
        self.milvus = MilvusClient(uri=milvus_uri)
        self.embedder = embedder
        self.system_collection = "greenhouse_bge_m3"
        self.user_collection = "cucumber_user_literature"

    def search(
        self,
        query: str,
        top_k: int = 5,
        growth_stage: str = None,
        include_user: bool = True
    ) -> List[RAGResult]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回数量
            growth_stage: 生育期过滤
            include_user: 是否包含用户文献

        Returns:
            RAGResult 列表
        """
        # 1. 向量化查询
        query_embedding = self.embedder.encode([query])[0]

        # 2. 系统文献检索
        system_results = self.milvus.search(
            collection_name=self.system_collection,
            data=[query_embedding],
            limit=top_k,
            filter=f'growth_stage == "{growth_stage}"' if growth_stage else None,
            output_fields=["content", "source", "page", "growth_stage"]
        )[0]

        # 3. 用户文献检索 (可选)
        user_results = []
        if include_user:
            user_results = self.milvus.search(
                collection_name=self.user_collection,
                data=[query_embedding],
                limit=top_k,
                output_fields=["content", "filename", "uploaded_at"]
            )[0]

        # 4. 合并排序 (系统权重 1.5, 用户权重 0.8)
        all_results = []
        for r in system_results:
            all_results.append(RAGResult(
                content=r["entity"]["content"],
                source=r["entity"]["source"],
                score=r["distance"] * 1.5,
                source_type="SYSTEM"
            ))
        for r in user_results:
            all_results.append(RAGResult(
                content=r["entity"]["content"],
                source=r["entity"]["filename"],
                score=r["distance"] * 0.8,
                source_type="USER"
            ))

        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
```

---

## 7. 数据流与通信机制

### 7.1 完整数据流图

```
用户操作                    前端                      后端                       AI/ML
────────                    ────                      ────                       ─────

[上传图像] ─────────────────→ Vision.tsx
                              │
                              │ POST /api/vision/analyze
                              │ (FormData: image file)
                              ▼
                            api.ts ─────────────────→ vision.py
                                                       │
                                                       │ 调用 YOLOService
                                                       ▼
                                                    yolo_service.py ──→ YOLO11
                                                       │                  │
                                                       │ ←────────────────┘
                                                       │ 返回 metrics + visualization
                                                       ▼
                              ←───────────────────── ApiResponse<VisionResult>
                              │
                              ▼
                            显示分割结果


[请求预测] ─────────────────→ Predict.tsx
                              │
                              │ POST /api/predict
                              │ (JSON: env_data, yolo_metrics)
                              ▼
                            api.ts ─────────────────→ predict.py
                                                       │
                                                       │ 1. 构建窗口
                                                       │ 2. TSMixer 预测
                                                       │ 3. LLM 长势评估
                                                       │ 4. 异常检测
                                                       │ 5. RAG 检索
                                                       │ 6. SanityCheck
                                                       ▼
                                                    DailyPipeline
                                                       │
                                                       ├──→ TSMixerService
                                                       ├──→ LLMService
                                                       ├──→ AnomalyDetector
                                                       ├──→ RAGService
                                                       └──→ EpisodeStore
                                                       │
                                                       ▼
                              ←───────────────────── ApiResponse<PredictResult>
                              │
                              ▼
                            显示预测结果


[知识问答] ─────────────────→ Knowledge.tsx
                              │
                              │ GET /api/knowledge/search?q=xxx
                              ▼
                            api.ts ─────────────────→ knowledge.py
                                                       │
                                                       │ RAGService.search()
                                                       ▼
                                                    retriever.py ──→ Milvus
                                                       │               │
                                                       │               │ 向量检索
                                                       │ ←─────────────┘
                                                       ▼
                              ←───────────────────── ApiResponse<KnowledgeResults>
                              │
                              ▼
                            显示知识片段
```

### 7.2 SSE 流式响应 (Chat)

```typescript
// 前端: stores/chatStore.ts
const streamChat = async (query: string) => {
  const eventSource = new EventSource(
    `${API_BASE}/chat/stream?query=${encodeURIComponent(query)}`
  );

  eventSource.addEventListener('content', (e) => {
    const { text, references } = JSON.parse(e.data);
    updateLastMessage(text);
  });

  eventSource.addEventListener('done', () => {
    setStreaming(false);
    eventSource.close();
  });

  eventSource.addEventListener('error', () => {
    setError('Stream connection failed');
    eventSource.close();
  });
};
```

```python
# 后端: api/v1/chat.py
from fastapi.responses import StreamingResponse

@router.get("/chat/stream")
async def stream_chat(query: str):
    async def generate():
        async for chunk in llm_service.stream_chat(query):
            yield f"event: content\ndata: {json.dumps(chunk)}\n\n"
        yield f"event: done\ndata: {{}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

---

## 8. AI/ML 模型集成

### 8.1 模型概览

| 模型 | 任务 | 输入 | 输出 | 框架 |
|------|------|------|------|------|
| YOLO11-seg | 实例分割 | 3200×1920 图像 | 4类实例掩码 | Ultralytics |
| TSMixer | 时序预测 | [96, 11] 窗口 | 灌水量预测 | PyTorch |
| GPT-5.2 | 多模态推理 | 文本 + 图像 | JSON 结构化输出 | OpenAI API |
| BGE-M3 | 文本向量化 | 文本 | 1024维向量 | FlagEmbedding |

### 8.2 YOLO11 配置

```yaml
# 模型信息
Model: yolo11_seg_best.pt
Task: Instance Segmentation
Classes:
  0: Leaf      # 叶片
  1: Terminal  # 顶芽
  2: Flower    # 花
  3: Fruit     # 果实

# 推理配置
Input Size: 640 × 640 (per tile)
Original Size: 3200 × 1920
Tile Grid: 5 × 3 = 15 tiles
Confidence Threshold: 0.25
NMS IoU Threshold: 0.45

# 输出指标
Metrics:
  - leaf_instance_count      # 叶片实例数
  - leaf_average_mask        # 叶片平均掩码面积
  - all_leaf_mask            # 叶片总掩码面积
  - flower_instance_count    # 花实例数
  - flower_mask_pixel_count  # 花掩码像素数
  - fruit_mask_average       # 果实平均掩码
  - terminal_average_mask_pixel_count  # 顶芽平均掩码
```

### 8.3 TSMixer 配置

```yaml
# 模型架构
Model: TSMixer
Type: Time-Series Mixing Model

# 输入配置
Sequence Length: 96 (days)
Feature Dimensions: 11
Features:
  - temperature         # 日均温度 (°C)
  - humidity           # 日均湿度 (%)
  - light              # 日均光照 (lux)
  - leaf_instance      # 叶片数
  - leaf_mask          # 叶片掩码
  - flower_instance    # 花数
  - flower_mask        # 花掩码像素
  - terminal_mask      # 顶芽掩码
  - fruit_mask         # 果实掩码
  - all_leaf_mask      # 总掩码
  - irrigation_target  # 历史灌水量

# 输出配置
Prediction Horizon: 1 (day)
Output: irrigation_amount (L/m²)

# 训练配置
Training Data: 3 years historical data
StandardScaler: Applied
```

### 8.4 LLM Prompt 设计

#### PlantResponse System Prompt

```markdown
# 角色定义
你是一位经验丰富的温室黄瓜种植专家，专注于精准灌溉和植物生长评估。

# 任务
根据今日和昨日的植株图像，评估植株生长状态变化。

# 评估维度
1. **trend** (长势趋势): better / same / worse
2. **confidence** (置信度): 0.0 - 1.0
3. **evidence** (支撑证据): 4个观察点
   - leaf_color: 叶片颜色变化
   - leaf_size: 叶片大小变化
   - plant_height: 植株高度变化
   - overall_vigor: 整体活力变化
4. **abnormalities** (异常检测): 4种异常
   - wilting: 萎蔫程度 (none/mild/moderate/severe)
   - yellowing: 黄化程度
   - pest_damage: 病虫害
   - nutrient_deficiency: 营养缺乏
5. **growth_stage** (生育期): seedling/vegetative/flowering/fruiting/mature
6. **comparison** (对比描述): 5个方面的描述性文字

# 输出格式
严格输出 JSON 格式，符合以下 Schema:
{
  "trend": "better" | "same" | "worse",
  "confidence": 0.85,
  "evidence": {...},
  "abnormalities": {...},
  "growth_stage": "flowering",
  "growth_stage_confidence": 0.9,
  "comparison": {...}
}
```

---

## 9. 4层记忆架构

### 9.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              4层记忆架构                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  L1: 工作上下文 (Working Context)                                           │
│  ──────────────────────────────────────────────────────────────────────────│
│  生命周期: 单次 LLM 调用                                                     │
│  存储: 内存                                                                 │
│  内容: System Prompt + Weekly Context + Today Input + RAG Results          │
│  预算: ≤ 4500 tokens                                                       │
│  管理: BudgetController (压缩策略)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↑
                          (注入 prompt_block)
                                      │
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  L3: 周摘要 (Weekly Summary)                                                │
│  ──────────────────────────────────────────────────────────────────────────│
│  生命周期: 每周生成                                                          │
│  存储: MongoDB / JSON                                                       │
│  内容:                                                                      │
│    - trend_stats: 长势统计 (better/same/worse 天数)                         │
│    - irrigation_stats: 灌水统计 (总量/均值/趋势)                             │
│    - anomaly_events: 异常事件列表                                           │
│    - key_insights: LLM 生成的 3-5 条洞察                                    │
│    - prompt_block: 下周注入的 Prompt 片段 (≤800 tokens)                      │
│  管理: WeeklySummaryStore                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↑
                          (聚合 7 天数据)
                                      │
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  L2: 日志 (Episode Log)                                                     │
│  ──────────────────────────────────────────────────────────────────────────│
│  生命周期: 每日生成                                                          │
│  存储: MongoDB / JSON                                                       │
│  内容:                                                                      │
│    - inputs: 环境数据 + YOLO指标 + 图像路径                                  │
│    - predictions: TSMixer预测 + PlantResponse + SanityCheck + 生育期        │
│    - anomalies: A1/A2/A3 检测结果                                           │
│    - final_decision: 最终灌水决策 + 来源 + 覆盖原因                          │
│    - user_feedback: 用户反馈 + 评分                                         │
│    - knowledge_references: RAG 引用列表                                     │
│  管理: EpisodeStore                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↑
                          (检索相关知识)
                                      │
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  L4: 知识库 (Knowledge Base)                                                │
│  ──────────────────────────────────────────────────────────────────────────│
│  生命周期: 持久化 (一次性索引)                                                │
│  存储: Milvus 向量数据库                                                     │
│  内容:                                                                      │
│    - 系统文献: FAO56 标准 (10,211 块)                                        │
│    - 用户文献: 上传的 PDF/TXT/MD                                             │
│  索引: BGE-M3 向量化 (1024 维)                                              │
│  检索: 混合检索 (稀疏 0.3 + 稠密 0.7)                                        │
│  管理: MultiSourceRetriever                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Token 预算控制

```yaml
# configs/memory.yaml
context_budget:
  total_max: 4500           # 总预算
  system_fixed: 500         # System Prompt (固定)
  weekly_max: 800           # L3 prompt_block 上限
  today_max: 2000           # 今日输入上限
  retrieval_max: 1000       # 检索结果上限
  retrieval_default_k: 3    # 默认 Top-K

compression:
  priority:                 # 压缩优先级 (数字越小越先压缩)
    retrieval: 1
    weekly: 2
    today: 3
  today_keep_fields:        # 压缩时保留的字段
    - trend
    - confidence
    - growth_stage
    - abnormalities
```

---

## 10. 部署与运行

### 10.1 一键启动 (Linux - 推荐)

本项目提供三个 Bash 脚本用于服务管理：

```bash
# 启动所有服务 (后端 + 前端)
./start.sh

# 检查服务状态
./status.sh

# 停止所有服务
./stop.sh
```

**start.sh 执行流程：**
1. 设置 PYTHONPATH 环境变量
2. 使用 nohup 在后台启动后端 (端口 8000)
3. 使用 nohup 在后台启动前端 (端口 3003)
4. 通过 curl 轮询健康检查接口
5. 日志输出到 `logs/backend.log` 和 `logs/frontend.log`

**访问地址：**
- 前端: http://localhost:3003
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

### 10.2 手动启动 (开发环境)

```bash
# 1. 克隆项目
git clone https://github.com/xxx/cucumber-irrigation-linux.git
cd cucumber-irrigation-linux

# 2. 后端启动 (终端1)
cd backend
source .venv/bin/activate   # 激活预配置虚拟环境
# 或者使用 uv:
# uv sync && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 前端启动 (终端2)
cd frontend
npm install                # 首次运行需安装依赖
npm run dev -- --port 3003 # 启动开发服务器
```

### 10.3 生产部署

```bash
# 后端 (使用 gunicorn 或 uvicorn workers)
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端构建
cd frontend
npm run build
# dist/ 目录已包含构建产物，部署到 Nginx / CDN
```

### 10.4 环境变量

```bash
# .env 文件位于项目根目录
LLM_API_KEY=your_api_key_here
MONGO_URI=mongodb://localhost:27017
MILVUS_URI=http://localhost:19530
LOG_LEVEL=INFO
```

### 10.5 进程管理命令

```bash
# 查看运行中的进程
ps aux | grep -E "(uvicorn|npm)"

# 手动停止 (使用 stop.sh 更安全)
pkill -f "uvicorn app.main:app"
fuser -k 3003/tcp

# 查看日志
tail -f logs/backend.log
tail -f logs/frontend.log
```


---

## 11. 论文结构建议

### 11.1 推荐论文结构

```
第1章 绪论
├── 1.1 研究背景与意义
│   ├─ 温室农业灌溉现状
│   ├─ 人工智能在农业中的应用
│   └─ 研究问题与目标
├── 1.2 国内外研究现状
│   ├─ 传统灌溉决策方法 (FAO56, Penman-Monteith)
│   ├─ 机器学习方法 (时序预测, 深度学习)
│   ├─ 计算机视觉方法 (YOLO, 实例分割)
│   └─ 大语言模型应用 (RAG, 多模态推理)
├── 1.3 研究内容与创新点
│   ├─ 多模态融合决策框架
│   ├─ 4层记忆架构
│   ├─ 三级异常检测机制
│   └─ 知识增强的人机协同
└── 1.4 论文组织结构

第2章 相关技术与理论基础
├── 2.1 FAO56 Penman-Monteith 模型
├── 2.2 时序混合模型 (TSMixer)
├── 2.3 YOLO11 实例分割
├── 2.4 大语言模型与多模态推理
├── 2.5 检索增强生成 (RAG)
└── 2.6 向量数据库与相似度检索

第3章 系统总体设计
├── 3.1 系统需求分析
│   ├─ 功能需求
│   └─ 非功能需求
├── 3.2 系统架构设计
│   ├─ 整体架构
│   ├─ 模块划分
│   └─ 技术选型
├── 3.3 数据流设计
│   ├─ 每日决策流程
│   └─ 周度总结流程
└── 3.4 接口设计
    ├─ RESTful API
    └─ 前后端通信

第4章 核心模块设计与实现
├── 4.1 多模态融合模块
│   ├─ YOLO11 视觉分析
│   ├─ TSMixer 时序预测
│   └─ GPT 长势评估
├── 4.2 4层记忆架构
│   ├─ L1 工作上下文
│   ├─ L2 Episode 日志
│   ├─ L3 周摘要
│   └─ L4 知识库
├── 4.3 异常检测模块
│   ├─ A1 范围检测
│   ├─ A2 趋势矛盾检测
│   └─ A3 环境异常检测
├── 4.4 知识增强模块
│   ├─ FAO56 知识库构建
│   ├─ 向量化与索引
│   └─ 混合检索策略
└── 4.5 人机协同模块
    ├─ 合理性复核
    └─ 人工覆盖机制

第5章 系统实现
├── 5.1 开发环境与工具
├── 5.2 后端实现
│   ├─ FastAPI 框架
│   ├─ 服务层实现
│   └─ 数据持久化
├── 5.3 前端实现
│   ├─ React 组件设计
│   ├─ 状态管理
│   └─ UI/UX 设计
└── 5.4 AI 模型集成
    ├─ YOLO11 部署
    ├─ TSMixer 部署
    └─ LLM API 集成

第6章 系统测试与实验
├── 6.1 功能测试
├── 6.2 性能测试
├── 6.3 模型评估
│   ├─ YOLO11 分割精度
│   ├─ TSMixer 预测精度
│   └─ 异常检测准确率
├── 6.4 用户测试
└── 6.5 对比实验
    ├─ 与传统方法对比
    └─ 消融实验

第7章 总结与展望
├── 7.1 工作总结
├── 7.2 创新点总结
├── 7.3 不足与局限
└── 7.4 未来工作展望

参考文献

附录
├── 附录A: API 接口文档
├── 附录B: 数据库 Schema
├── 附录C: Prompt 模板
└── 附录D: 系统部署指南
```

### 11.2 各章节写作要点

#### 第1章 绪论
- 突出温室灌溉精准化的重要性
- 对比传统方法与 AI 方法的优劣
- 明确提出"多模态融合 + 知识增强 + 人机协同"的创新框架

#### 第3章 系统设计
- 使用本文档的架构图
- 详细说明 12 步决策流程
- 强调 4 层记忆架构的设计理念

#### 第4章 核心模块
- 每个模块配合代码片段说明
- 使用公式说明 TSMixer、FAO56
- 配合流程图说明异常检测逻辑

#### 第5章 系统实现
- 配合界面截图
- 说明技术选型理由
- 展示代码实现细节

#### 第6章 实验
- 准备充分的测试数据集
- 设计合理的评估指标
- 进行消融实验验证各模块贡献

### 11.3 图表清单建议

| 图表编号 | 名称 | 位置 |
|----------|------|------|
| 图1-1 | 研究技术路线图 | 第1章 |
| 图3-1 | 系统总体架构图 | 第3章 |
| 图3-2 | 每日决策流程图 | 第3章 |
| 图3-3 | 4层记忆架构图 | 第3章 |
| 图4-1 | YOLO11 实例分割示例 | 第4章 |
| 图4-2 | TSMixer 模型架构 | 第4章 |
| 图4-3 | 三级异常检测流程 | 第4章 |
| 图4-4 | RAG 检索流程 | 第4章 |
| 图5-1 | 系统界面截图 (Dashboard) | 第5章 |
| 图5-2 | 系统界面截图 (Chat) | 第5章 |
| 图5-3 | 系统界面截图 (Vision) | 第5章 |
| 表3-1 | API 接口列表 | 第3章 |
| 表4-1 | YOLO11 输出指标 | 第4章 |
| 表4-2 | TSMixer 输入特征 | 第4章 |
| 表6-1 | 功能测试用例 | 第6章 |
| 表6-2 | 模型评估结果 | 第6章 |

---

## 文档版本

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| 1.0 | 2024-12-28 | Claude | 初始版本 |

---

*本文档由 Claude Code 自动生成，基于对项目代码的全面分析。*
