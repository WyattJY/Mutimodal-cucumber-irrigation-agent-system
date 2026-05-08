# 温室黄瓜灌水智能体系统 - 功能补充需求文档

> 版本：v1.0
> 创建日期：2024-12-27
> 文档状态：需求梳理

---

## 1. 文档目的

本文档用于明确：
1. 当前系统已实现的功能
2. 设计文档中定义但未实现的功能
3. 需要补充的功能需求和优先级

---

## 2. 系统架构回顾

根据 `docs/design.md`，系统应包含以下核心模块：

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据采集与预处理层                         │
│     图像加载器 | 环境数据读取器 | 时序窗口构建器 | 数据验证器        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        模型推理层 (并发)                          │
│              YOLO Service          |       TSMixer Service       │
│           (图像分割 → 表型指标)      |     (时序预测 → 灌水量)      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        LLM 评估层 (GPT-5.2)                       │
│    PlantResponse (长势评估) → SanityCheck (复核) → WeeklySummary  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        知识与记忆层                               │
│     L1 Working Context | L2 Episode | L3 Weekly | L4 RAG         │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        输出与反馈层                               │
│          灌水量输出 | 预警展示 | Override 记录 | 日志记录          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 当前已实现功能

### 3.1 后端服务 (backend/app/)

| 模块 | 文件位置 | 状态 | 说明 |
|------|----------|------|------|
| **YOLO 推理** | `services/yolo_service.py` | ✅ 完成 | 分块推理 (15 tiles)，输出表型指标 |
| **TSMixer 预测** | `services/tsmixer_service.py` | ✅ 完成 | 96 步窗口，z-score 反标准化 |
| **LLM 对话** | `services/llm_service.py` | ✅ 完成 | 支持流式对话、图片分析 |
| **Episode 服务** | `services/episode_service.py` | ✅ 完成 | 从 Excel 读取历史 Episode |
| **图片上传** | `api/v1/upload.py` | ✅ 完成 | 上传 → YOLO 处理 → 返回指标 |
| **聊天 API** | `api/v1/chat.py` | ✅ 完成 | 流式聊天 (SSE) |
| **设置 API** | `api/v1/settings.py` | ✅ 完成 | 模型配置、连接测试 |
| **统计 API** | `api/v1/stats.py` | ✅ 完成 | 趋势数据、汇总统计 |
| **周报 API** | `api/v1/weekly.py` | ✅ 完成 | 周度统计、洞察 |

### 3.2 核心模块 (src/cucumber_irrigation/)

| 模块 | 文件位置 | 状态 | 说明 |
|------|----------|------|------|
| **LLM Service** | `services/llm_service.py` | ✅ 完成 | PlantResponse 生成、SanityCheck |
| **环境输入处理** | `core/env_input_handler.py` | ✅ 完成 | 环境数据规范化 |
| **冷启动填充** | `core/cold_start.py` | ✅ 完成 | 数据不足时填充 |
| **窗口构建** | `core/window_builder.py` | ✅ 完成 | 96 步时序窗口 |
| **异常检测** | `core/anomaly_detector.py` | ✅ 完成 | 范围检测、趋势冲突 |
| **生育期检测** | `core/growth_stage_detector.py` | ✅ 完成 | 基于 LLM 判断生育期 |
| **Daily Pipeline** | `pipelines/daily_pipeline.py` | ⚠️ 部分 | 框架完成，但 `_generate_plant_response()` 返回 None |
| **Weekly Pipeline** | `pipelines/weekly_pipeline.py` | ⚠️ 部分 | 框架完成，未连接后端 |

### 3.3 记忆模块 (src/cucumber_irrigation/memory/)

| 模块 | 文件位置 | 状态 | 说明 |
|------|----------|------|------|
| **Budget Controller** | `budget_controller.py` | ✅ 完成 | Token 预算控制 |
| **Working Context** | `working_context.py` | ✅ 完成 | L1 上下文组装 |
| **Episode Store** | `episode_store.py` | ✅ 完成 | L2 存储 (MongoDB/JSON 双后端) |
| **Weekly Summary Store** | `weekly_summary_store.py` | ✅ 完成 | L3 存储 |
| **Knowledge Retriever** | `knowledge_retriever.py` | ⚠️ 部分 | L4 框架完成，Milvus 未连接 |

### 3.4 RAG 模块 (src/cucumber_irrigation/rag/)

| 模块 | 文件位置 | 状态 | 说明 |
|------|----------|------|------|
| **Embedder** | `embedder.py` | ✅ 完成 | 文本向量化 |
| **Chunker** | `chunker.py` | ✅ 完成 | 文档分块 |
| **Indexer** | `indexer.py` | ✅ 完成 | 向量索引构建 |
| **Retriever** | `retriever.py` | ✅ 完成 | 相似检索 |
| **Local RAG Service** | `services/local_rag_service.py` | ✅ 完成 | 本地 JSON 后端 |

### 3.5 前端 (frontend/)

| 模块 | 状态 | 说明 |
|------|------|------|
| **Dashboard** | ✅ 完成 | HeroCard, TrendChart, WarningCard |
| **DailyDecision** | ✅ 完成 | 传感器卡片、预测卡片、YOLO 图像、Agent Insights |
| **History** | ✅ 完成 | 日期筛选、趋势图、统计卡片 |
| **Weekly** | ✅ 完成 | 周选择器、统计、洞察 |
| **Knowledge** | ✅ 完成 | 聊天界面、流式回复 |
| **Settings** | ✅ 完成 | 模型配置、决策引擎、传感器、告警 |
| **PlantResponse** | ⚠️ 部分 | 图像查看器完成，但无对比分析展示 |
| **Predict** | ⚠️ 部分 | 基础预测完成 |

### 3.6 预生成数据

| 数据 | 位置 | 数量 | 说明 |
|------|------|------|------|
| **PlantResponse JSON** | `output/responses/*.json` | 78 个 | 2024-03-15 ~ 2024-06-14 的历史分析 |
| **YOLO 分割图** | `output/segmented_images/` | ~85 张 | 分割可视化结果 |
| **YOLO 指标** | `output/yolo_metrics/` | ~85 个 | JSON 格式指标 |

---

## 4. 未实现功能 (需补充)

### 4.1 🔴 P0 - 核心功能缺失

#### 4.1.1 PlantResponse 自动生成

**问题描述**：
- 用户上传图片后，系统只执行 YOLO 分割
- 没有调用 GPT-5.2 生成 PlantResponse（今日 vs 昨日对比分析）
- `daily_pipeline.py:_generate_plant_response()` 返回 None

**设计要求** (来自 `design.md` 3.3 LLM Service)：
```python
def evaluate_plant(
    self,
    image_today: str,
    image_yesterday: str,
    yolo_today: YOLOMetrics,
    yolo_yesterday: YOLOMetrics
) -> PlantResponse:
    """
    长势评估
    对比今日与昨日图像，结合 YOLO 指标评估植物长势
    """
```

**期望输出**：
```json
{
  "trend": "better | same | worse",
  "confidence": 0.85,
  "evidence": {
    "leaf_observation": "...",
    "flower_observation": "...",
    "fruit_observation": "..."
  },
  "abnormalities": {
    "wilting": "none | mild | severe",
    "yellowing": "none | mild | severe",
    "pest_damage": "..."
  },
  "growth_stage": "vegetative | flowering | fruiting"
}
```

**补充需求**：
1. 新建 `/api/predict/daily` 端点
2. 在图片上传后自动触发 PlantResponse 生成
3. 保存结果到 `output/responses/{date}.json`
4. 更新 Episode 记录

---

#### 4.1.2 单张图片处理（冷启动）

**问题描述**：
- PlantResponse 需要"今日 vs 昨日"对比
- 如果用户只上传了一张图片（没有昨日图片），无法进行对比

**补充需求**：
1. **冷启动模式**：
   - 如果没有昨日图片，生成"单日分析"而非"对比分析"
   - 只描述当前状态，不输出 trend
   - 标记 `is_cold_start: true`

2. **提示用户**：
   - 前端提示"建议连续上传多天图片以获得完整分析"

3. **自动匹配**：
   - 根据日期自动查找昨日图片
   - 支持跳过缺失日期（如 0530 的昨日是 0529，但如果 0529 不存在则尝试 0528）

---

#### 4.1.3 Episode 自动生成与存储

**问题描述**：
- Episode 模型已定义 (`models/episode.py`)
- EpisodeStore 已实现 (`memory/episode_store.py`)
- 但后端 API 不会创建或更新 Episode

**设计要求** (来自 `design.md` Episode Schema)：
```json
{
  "date": "2024-05-30",
  "inputs": {
    "environment": {...},
    "yolo_metrics": {...}
  },
  "predictions": {
    "tsmixer_raw": 5.2,
    "growth_stage": "fruiting"
  },
  "llm_outputs": {
    "plant_response": {...},
    "sanity_check": {...}
  },
  "final_decision": {
    "value": 5.2,
    "source": "tsmixer | override",
    "override_reason": null
  }
}
```

**补充需求**：
1. 每次完整预测流程后自动创建 Episode
2. Override 时更新 Episode
3. 支持 MongoDB 或 JSON 文件存储
4. 提供 Episode 查询 API

---

#### 4.1.4 SanityCheck 合理性复核

**问题描述**：
- `llm_service.sanity_check()` 方法已实现
- 但后端 API 没有调用它

**设计要求** (来自 `design.md` 3.3)：
- 在 TSMixer 预测后，使用 PlantResponse + 预测值进行交叉验证
- 判断预测是否与长势评估一致
- 如不一致，给出调整建议

**补充需求**：
1. 在 `/api/predict/daily` 流程中添加 SanityCheck 步骤
2. 如果 `is_consistent: false`，标记需要人工确认
3. 调整后的值记录在 Episode 中

---

### 4.2 🟡 P1 - 记忆系统集成

#### 4.2.1 L1 Working Context 注入

**问题描述**：
- Working Context 模块已实现
- 但 LLM 调用时没有注入周摘要和 RAG 结果

**补充需求**：
1. 在调用 GPT-5.2 前，构建 Working Context
2. 自动注入最近的 Weekly Summary (如果存在)
3. 自动注入相关 RAG 检索结果

---

#### 4.2.2 L3 Weekly Summary 自动生成

**问题描述**：
- WeeklySummaryStore 已实现
- WeeklyPipeline 框架已完成
- 但没有定时任务触发，也没有 API 触发

**设计要求**：
```json
{
  "week_start": "2024-05-27",
  "week_end": "2024-06-02",
  "patterns": ["规律1", "规律2"],
  "risk_triggers": ["风险条件1", "风险条件2"],
  "overrides": [...],
  "prompt_notes": ["注入建议1"],
  "statistics": {
    "avg_irrigation": 5.2,
    "override_rate": 0.1
  }
}
```

**补充需求**：
1. 提供 `/api/weekly/generate` 手动触发端点
2. 可选：定时任务每周日自动运行
3. 生成的 `prompt_block` 注入后续决策

---

#### 4.2.3 L4 RAG 知识检索集成

**问题描述**：
- RAG 模块已实现 (`rag/*.py`, `services/local_rag_service.py`)
- 但 Knowledge 页面只是普通聊天，没有使用 RAG
- 决策流程也没有使用 RAG

**补充需求**：
1. Knowledge 页面改为 RAG 增强问答：
   - 用户提问 → 向量检索 → 检索结果 + 问题一起发给 LLM
   - 显示引用来源
2. 决策流程中使用 RAG：
   - 根据生育期检索相关知识
   - 根据异常类型检索处理建议
3. 支持用户对检索结果评分

---

### 4.3 🟢 P2 - 前端展示增强

#### 4.3.1 PlantResponse 结果展示

**问题描述**：
- DailyDecision 页面有 "Agent Insights" 区域
- 但显示的是静态内容，不是真正的 PlantResponse

**补充需求**：
1. 调用后端获取当日 PlantResponse
2. 展示 trend (better/same/worse) + confidence
3. 展示 evidence 详细观察
4. 展示 abnormalities 异常检测结果
5. 展示 growth_stage 生育期

---

#### 4.3.2 图像对比查看器

**问题描述**：
- PlantResponse 页面有图像查看器
- 但没有"今日 vs 昨日"并排对比功能

**补充需求**：
1. 左右分屏对比（昨日 | 今日）
2. 滑动对比（slider）
3. 显示两日的 YOLO 指标差异

---

#### 4.3.3 RAG 引用显示

**补充需求**：
1. Knowledge 页面显示引用来源
2. 鼠标悬停显示完整片段
3. 支持点击跳转到原始文档

---

### 4.4 🔵 P3 - 增强功能

#### 4.4.1 Override 理由管理

**补充需求**：
1. 常用理由模板选择
2. 理由关键词自动提取
3. 历史理由统计分析

#### 4.4.2 异常预警推送

**补充需求**：
1. 严重异常时前端弹窗提示
2. 可选邮件/短信通知

#### 4.4.3 数据导出增强

**补充需求**：
1. 导出 Episode 历史
2. 导出 Weekly Summary
3. 批量导出 PlantResponse

---

## 5. 数据流补充说明

### 5.1 完整的每日决策流程（期望实现）

```
用户上传图片 (date: 2024-05-30)
    ↓
1. 保存图片到 data/images/0530.jpg
    ↓
2. YOLO 推理 → yolo_today (叶片数、面积、花朵数...)
    ↓
3. 查找昨日图片 (0529.jpg)
    ├── 存在 → 获取 yolo_yesterday
    └── 不存在 → 冷启动模式
    ↓
4. 构建时序窗口 (96 天)
    ↓
5. TSMixer 预测 → irrigation_amount = 5.2 L/m²
    ↓
6. 生育期检测 → growth_stage = "fruiting"
    ↓
7. RAG 检索 → 相关知识片段 (FAO56、历史案例)
    ↓
8. 构建 Working Context (L1)
    ├── System Prompt
    ├── Weekly Summary (如有)
    ├── Today's Input
    └── RAG Results
    ↓
9. GPT-5.2 长势评估 → PlantResponse
    {
      "trend": "same",
      "confidence": 0.72,
      "evidence": {...},
      "abnormalities": {...},
      "growth_stage": "fruiting"
    }
    ↓
10. GPT-5.2 合理性复核 → SanityCheck
    {
      "is_consistent": true,
      "adjusted_value": 5.2,
      "reason": "预测值与长势一致"
    }
    ↓
11. 创建/更新 Episode (L2)
    ↓
12. 保存 PlantResponse 到 output/responses/
    ↓
13. 返回结果给前端
    {
      "irrigation_amount": 5.2,
      "source": "tsmixer",
      "plant_response": {...},
      "sanity_check": {...},
      "warnings": [],
      "rag_references": [...]
    }
```

### 5.2 冷启动处理

```
用户首次上传图片 (没有昨日图片)
    ↓
检测到冷启动
    ↓
生成单日分析 (而非对比分析)
{
  "is_cold_start": true,
  "trend": null,  // 无法判断趋势
  "current_state": {
    "growth_stage": "flowering",
    "health_status": "良好",
    "observations": [...]
  },
  "abnormalities": {...}
}
    ↓
前端提示："已记录今日状态。建议明天继续上传以获得趋势分析。"
```

---

## 6. 接口补充设计

### 6.1 POST /api/predict/daily

**完整的每日预测接口**

Request:
```json
{
  "date": "2024-05-30",
  "image_base64": "...",  // 可选，如果不传则从 data/images/ 读取
  "env_data": {           // 可选，如果不传则从 CSV 读取
    "temperature": 25.0,
    "humidity": 70.0,
    "light": 8000
  },
  "options": {
    "run_sanity_check": true,
    "use_rag": true,
    "save_episode": true
  }
}
```

Response:
```json
{
  "success": true,
  "data": {
    "date": "2024-05-30",
    "irrigation_amount": 5.2,
    "source": "tsmixer",
    "is_cold_start": false,

    "yolo_metrics": {
      "leaf_instance_count": 8.0,
      "leaf_average_mask": 7287.8,
      "flower_instance_count": 1.4,
      ...
    },

    "plant_response": {
      "trend": "same",
      "confidence": 0.72,
      "evidence": {...},
      "abnormalities": {...},
      "growth_stage": "fruiting"
    },

    "sanity_check": {
      "is_consistent": true,
      "confidence": 0.85,
      "adjusted_value": 5.2,
      "reason": "预测值与长势评估一致"
    },

    "rag_references": [
      {
        "doc_id": "fao56_ch8_p3",
        "snippet": "开花期作物系数 Kc = 1.0-1.15...",
        "relevance": 0.85
      }
    ],

    "warnings": [],
    "suggestions": [],

    "episode_id": "2024-05-30"
  }
}
```

### 6.2 POST /api/knowledge/query (RAG 增强)

Request:
```json
{
  "question": "开花期最佳灌水量是多少？",
  "context": {
    "growth_stage": "flowering",
    "current_irrigation": 5.2
  },
  "top_k": 5
}
```

Response:
```json
{
  "success": true,
  "data": {
    "answer": "根据 FAO56 标准，开花期黄瓜的作物系数 Kc 约为 1.0-1.15...",
    "references": [
      {
        "doc_id": "fao56_ch8",
        "title": "FAO56 作物蒸发蒸腾量指南 - 第八章",
        "snippet": "...",
        "relevance": 0.92
      }
    ],
    "model": "gpt-5.2"
  }
}
```

### 6.3 POST /api/weekly/generate

Request:
```json
{
  "week_start": "2024-05-27",
  "week_end": "2024-06-02"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "week_start": "2024-05-27",
    "week_end": "2024-06-02",
    "patterns": [
      "本周日均灌水量 5.1 L/m²，较上周增加 8%",
      "开花期转结果期，需水量上升"
    ],
    "risk_triggers": [
      "连续高温 (>30°C) 时需增加灌水"
    ],
    "overrides": [],
    "statistics": {
      "avg_irrigation": 5.1,
      "max_irrigation": 6.2,
      "min_irrigation": 4.1,
      "override_rate": 0.0
    },
    "prompt_block": "本周总结：作物从开花期进入结果期..."
  }
}
```

---

## 7. 优先级排序

| 优先级 | 功能 | 工作量 | 依赖 |
|--------|------|--------|------|
| **P0** | PlantResponse 自动生成 | 中 | YOLO, LLM |
| **P0** | 单张图片冷启动处理 | 小 | PlantResponse |
| **P0** | Episode 自动存储 | 小 | PlantResponse |
| **P0** | SanityCheck 集成 | 小 | PlantResponse |
| **P1** | Weekly Summary 生成 | 中 | Episode |
| **P1** | Working Context 注入 | 小 | Weekly Summary |
| **P1** | RAG 知识检索集成 | 中 | RAG 模块 |
| **P2** | PlantResponse 前端展示 | 中 | PlantResponse API |
| **P2** | 图像对比查看器 | 中 | - |
| **P2** | RAG 引用显示 | 小 | RAG API |
| **P3** | Override 理由管理 | 小 | - |
| **P3** | 异常预警推送 | 中 | - |
| **P3** | 数据导出增强 | 小 | - |

---

## 8. 下一步计划

### Phase 1: 核心功能补齐 (P0)

1. 创建 `/api/predict/daily` 端点
2. 集成 PlantResponse 生成（含冷启动处理）
3. 集成 SanityCheck
4. 自动创建/更新 Episode

### Phase 2: 记忆系统集成 (P1)

1. Weekly Summary 生成 API
2. Working Context 自动注入
3. RAG 知识检索集成

### Phase 3: 前端增强 (P2)

1. PlantResponse 结果展示
2. 图像对比查看器
3. RAG 引用显示

### Phase 4: 增强功能 (P3)

1. Override 理由管理
2. 异常预警推送
3. 数据导出增强

---

## 附录 A: 相关文件位置

| 功能 | 核心模块 | 后端 API | 前端页面 |
|------|----------|----------|----------|
| PlantResponse | `src/.../services/llm_service.py` | 待创建 | `DailyDecision.tsx` |
| Episode | `src/.../memory/episode_store.py` | `episodes.py` | `History.tsx` |
| Weekly Summary | `src/.../memory/weekly_summary_store.py` | `weekly.py` | `Weekly.tsx` |
| RAG | `src/.../rag/*.py` | `knowledge.py` | `Knowledge.tsx` |
| SanityCheck | `src/.../services/llm_service.py` | 待创建 | - |

## 附录 B: 环境配置

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| LLM API | yunwu.ai/v1 | OpenAI 兼容接口 |
| 模型 (文本) | gpt-5.2-chat-latest | 纯文本对话 |
| 模型 (视觉) | gpt-5.2 | 图片分析 |
| MongoDB | 未启用 | 使用 JSON 文件存储 |
| Milvus | 未启用 | 使用本地 RAG |

---

> 文档结束
