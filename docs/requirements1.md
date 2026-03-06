# 温室黄瓜灌水智能体系统 - 需求补充文档 v1

> 版本：v1.2
> 更新日期：2024-12-26
> 文档状态：需求分析完成（含4层记忆架构 + 知识增强机制）

---

## 1. 文档目的

本文档针对以下核心问题进行需求澄清和设计补充：

| 问题编号 | 问题描述 |
|----------|----------|
| Q1 | TSMixer 滚动预测与冷启动数据填充 |
| Q2 | TSMixer 预测异常处理与 RAG 辅助判断 |
| Q3 | 4层记忆架构设计（Working Context / Episodic Log / Recent Summary / Knowledge Memory） |
| Q4 | 上下文注入预算控制机制（Rule-M1） |
| Q5 | 数据库架构设计（同实例分库方案） |
| Q6 | 周总结动态 Prompt 注入机制 |
| Q7 | 知识增强评估机制（生育期预判 + 文献支撑的长势描述与经验总结） |

---

## 2. Q1: TSMixer 滚动预测与冷启动设计

### 2.1 输入输出规格

| 项目 | 规格 |
|------|------|
| **输入序列长度** | 96 步（天） |
| **输入特征维度** | 11 个特征 |
| **输出** | 单一灌水量值（L/m²） |
| **预测方式** | 滚动预测（窗口滑动） |

### 2.2 输入特征定义

参考 `cucumber-irrigation/data/csv/irrigation_pre.csv` 和 `Irrigation` 项目：

| 序号 | 特征名 | 说明 |
|------|--------|------|
| 1 | temperature | 日均温度 (°C) |
| 2 | humidity | 日均湿度 (%) |
| 3 | light | 日均光照 (lux) |
| 4 | leaf Instance Count | 叶片实例数量 |
| 5 | leaf average mask | 叶片平均掩码面积 |
| 6 | flower Instance Count | 花朵实例数量 |
| 7 | flower Mask Pixel Count | 花朵掩码像素总数 |
| 8 | terminal average Mask Pixel Count | 顶芽平均掩码面积 |
| 9 | fruit Mask average | 果实平均掩码面积 |
| 10 | all leaf mask | 全部叶片掩码总面积 |
| 11 | Target | 历史灌水量 (L/m²) |

### 2.3 滚动预测逻辑

```
┌─────────────────────────────────────────────────────────────┐
│                    滚动预测流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入构建：                                                  │
│  ├─ 获取目标日期之前的 95 天历史数据                         │
│  ├─ 加上今日输入数据（用户提供或传感器采集）                  │
│  └─ 拼接成 96 步 × 11 特征的输入矩阵                        │
│                                                             │
│  预测执行：                                                  │
│  ├─ 输入 → 标准化 (StandardScaler)                         │
│  ├─ 标准化输入 → TSMixer 模型                               │
│  └─ 模型输出 → 逆标准化 → 灌水量预测值                      │
│                                                             │
│  窗口滑动：                                                  │
│  ├─ 下一天预测时，剔除窗口最早的一天                         │
│  └─ 加入新一天的数据，保持窗口长度为 96                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 冷启动数据填充策略

**场景**：用户无法提供完整的 96 天历史数据（正常情况下都提供不了）

**填充数据源**：`cucumber-irrigation/data/csv/irrigation_pre.csv`
- 包含 2023 年春茬（3月-6月）的完整数据
- 数据字段与 TSMixer 输入完全一致

**填充规则**：

| 茬口类型 | 目标日期范围 | 参考数据范围 | 说明 |
|----------|--------------|--------------|------|
| 春茬 | 2025年3月-6月 | 2023年3月-6月 | 日期对应（月日相同） |
| 秋茬 | 2025年9月-11月 | 2023年9月-11月 | 待补充数据后支持 |

**填充算法**：

```
输入：target_date = "2025-03-14", 用户数据 = today_data
输出：96 步完整输入序列

1. 计算需要填充的天数：
   - 用户已有数据天数 = len(user_history)
   - 需填充天数 = 95 - 用户已有数据天数

2. 获取参考日期：
   - ref_date = target_date.replace(year=2023)
   - 即 2025-03-14 → 2023-03-14

3. 从 irrigation_pre.csv 获取填充数据：
   - 取 ref_date 之前的 (需填充天数) 天数据
   - 例：预测 3月14日，用户无历史数据
   - 则取 2023年从3月12日往前推95天的数据

4. 拼接顺序：
   - [填充数据 | 用户历史数据 | 今日数据]
   - 总长度 = 96 步
```

**示例**：

```
预测日期：2025-03-14
用户提供：仅今日数据
填充策略：
  - 从 irrigation_pre.csv 取 2023/3/13 及之前 95 天数据
  - 拼接今日数据（2025/3/14）
  - 形成 [95天历史填充 + 1天今日] = 96步输入
```

### 2.5 数据源配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 填充数据路径 | `data/csv/irrigation_pre.csv` | 2023年春茬完整数据 |
| 日期列名 | `date` | 格式：YYYY/M/D |
| 特征列 | 第2-12列 | 11个特征 |

---

## 3. Q2: TSMixer 预测异常处理与 RAG 辅助判断

### 3.1 异常类型定义

| 异常类型 | 编号 | 说明 |
|----------|------|------|
| 预测值超出历史范围 | A1 | TSMixer 输出超出合理边界 |
| 长势-灌水矛盾 | A2 | PlantResponse 趋势与灌水量预测矛盾 |
| 连续异常环境 | A3 | 连续多天环境参数异常 |

### 3.2 历史范围阈值（A1）

基于 `irrigation_pre.csv` 统计得出：

| 指标 | 值 | 用途 |
|------|-----|------|
| historical_min | 0.1 L/m² | 灌水量最小值 |
| historical_max | 15.0 L/m² | 灌水量最大值 |
| historical_mean | 5.5 L/m² | 灌水量均值 |
| historical_std | 3.5 L/m² | 灌水量标准差 |

**判断规则**：
- 预测值 < 0.1 或 > 15.0 → 触发"超出历史范围"异常
- 建议调用 RAG 获取 FAO56 参考建议

### 3.3 长势-灌水矛盾阈值（A2）

**核心矛盾场景**：
- PlantResponse.trend = "worse"，但灌水预测反而减少
- PlantResponse.trend = "better"，但灌水预测大幅增加

**矛盾严重程度判定**：

| 条件 | 严重程度 | 说明 |
|------|----------|------|
| trend=worse 且 灌水变化率 < -10% | **severe** | 长势差但灌水反而减少 |
| trend=worse 且 灌水变化率 < +10% | **moderate** | 长势差但灌水增加不足 |
| trend=worse 且 有严重异常(萎蔫/黄化) 且 灌水变化率 < +20% | **moderate** | 有严重异常但灌水响应不足 |
| trend=better 且 灌水变化率 > +30% | **mild** | 长势好但灌水过度增加 |
| 其他情况 | **none** | 无矛盾 |

**灌水变化率计算**：
```
change_ratio = (今日预测 - 昨日灌水) / max(昨日灌水, 0.1)
```

**阈值设定依据**（参考 FAO56）：
- 长势 worse 时，植物需水压力增大，灌水应增加 10-30%
- 长势 better 时，植物需水稳定，灌水可适当减少 5-15%
- 有萎蔫/黄化等严重异常时，需更大幅度增加灌水（+20% 以上）

### 3.4 连续异常环境阈值（A3）

| 异常类型 | 触发条件 | 说明 |
|----------|----------|------|
| 高湿异常 | 连续 ≥3 天，humidity > 85% | 易发病害，需减少灌水 |
| 高温胁迫 | 连续 ≥3 天，temperature > 35°C | 蒸腾增加，需增加灌水 |
| 弱光异常 | 连续 ≥3 天，light < 2000 lux | 光合减弱，需减少灌水 |

**参考来源**：FAO56 Table 4（不同气象条件下的作物需水调整系数）

### 3.5 RAG 辅助判断流程

当检测到异常时，调用 Greenhouse_RAG 系统获取专业建议：

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 辅助判断流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 异常检测触发 RAG 查询                                    │
│     ├─ A1(超出范围) → 查询"irrigation range cucumber"       │
│     ├─ A2(长势矛盾) → 查询"water stress {growth_stage}"     │
│     └─ A3(环境异常) → 查询具体环境条件相关内容               │
│                                                             │
│  2. Milvus 混合检索                                         │
│     ├─ 稀疏向量：关键词精确匹配（Kc, ETo 等专业术语）        │
│     └─ 稠密向量：语义相似度（BGE-M3 模型）                   │
│                                                             │
│  3. 结果优先级                                               │
│     ├─ 优先返回 is_fao56=true 的文档片段                     │
│     └─ 次选返回其他温室灌溉相关文献                           │
│                                                             │
│  4. 建议生成                                                 │
│     └─ 将检索结果整合为可读建议，注入 SanityCheck.rag_advice │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.6 RAG 查询构建规则

| 异常类型 | 查询模板 | 示例 |
|----------|----------|------|
| A2-长势矛盾 | `cucumber water stress irrigation adjustment crop coefficient Kc under stress conditions plant {abnormality} water requirement growth stage: {stage}` | `cucumber water stress irrigation adjustment crop coefficient Kc under stress conditions plant wilting yellowing water requirement growth stage: flowering` |
| A3-高湿异常 | `high humidity greenhouse irrigation reduction disease prevention` | - |
| A3-高温胁迫 | `high temperature water stress crop evapotranspiration cooling` | - |
| A3-弱光异常 | `low light photosynthesis reduction irrigation adjustment` | - |

---

## 4. Q3: 4层记忆架构设计

### 4.1 架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           4 层记忆架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ L1. Working Context（工作上下文）                                    │   │
│  │     生命周期：一次任务/一天                                          │   │
│  │     落库：可选（默认不落库）                                         │   │
│  │     注入：✅ 必注入                                                  │   │
│  │     预算：2000~6000 tokens                                          │   │
│  │     内容：今日输入 + 昨今对比结论 + 周摘要(可选) + TopK检索片段       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ L2. Episodic Log（每日日志）                                         │   │
│  │     生命周期：永久                                                   │   │
│  │     落库：✅ 永久存储到 MongoDB.episodes                             │   │
│  │     注入：❌ 默认不注入，按需检索                                    │   │
│  │     用途：留档、回放、做数据集、检索相似异常/同生育期冲突             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ L3. Recent Summary（周摘要）                                         │   │
│  │     生命周期：永久                                                   │   │
│  │     落库：✅ 永久存储到 MongoDB.weekly_summaries                     │   │
│  │     注入：✅ 仅注入 prompt_block 字段                                │   │
│  │     预算：prompt_block ≤ 800 tokens（约1200字）                      │   │
│  │     超限处理：只保留 key_insights，删除统计细节                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ L4. Knowledge Memory（知识库）                                       │   │
│  │     生命周期：永久                                                   │   │
│  │     落库：✅ Milvus 向量库 + MongoDB 文档                            │   │
│  │     注入：✅ 按需 TopK 检索注入                                      │   │
│  │     内容：FAO56 / 温室灌溉文献 / 历史经验片段                         │   │
│  │     默认 K=3~5                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 层级对比表

| 层级 | 名称 | 生命周期 | 落库 | 注入 | 预算限制 |
|------|------|----------|------|------|----------|
| L1 | Working Context | 一天 | 可选 | ✅ 必注入 | 2k~6k tokens |
| L2 | Episodic Log | 永久 | ✅ | ❌ 按需检索 | 不注入 |
| L3 | Recent Summary | 永久 | ✅ | ✅ prompt_block | ≤800 tokens |
| L4 | Knowledge Memory | 永久 | ✅ | ✅ TopK检索 | K=3~5 片段 |

### 4.3 L1 Working Context（工作上下文）

**定义**：单次 LLM 调用的完整输入上下文，是"注入层"的核心。

**构成**：

| 组成部分 | 来源 | 预算分配 | 说明 |
|----------|------|----------|------|
| System Prompt | 固定模板 | ~500 tokens | 角色定义、输出格式 |
| Weekly Context | L3.prompt_block | ≤800 tokens | 上周经验总结 |
| Today Input | 当日数据 | ~1500 tokens | 环境+YOLO+图像描述 |
| Retrieval | L4 TopK检索 | ~1000 tokens | FAO56/文献片段 |
| **总计** | - | **≤4000 tokens** | 可配置上限 |

**不落库内容**：
- 图像 Base64 编码
- 中间推理过程
- 临时计算结果

**可选落库内容**：
- 完整的 prompt 模板（用于调试）
- token 使用统计

### 4.4 L2 Episodic Log（每日日志）

**定义**：每日完整决策记录，永久存储，用于回放和分析。

**关键原则**：
- ✅ 永久落库到 `MongoDB.episodes`
- ❌ 默认**不注入** LLM 上下文
- ✅ 只在需要时检索（相似异常、同生育期对比）

**数据结构**：

```
MongoDB Collection: episodes

{
  "_id": ObjectId,
  "date": "2025-03-14",
  "season": "spring_2025",
  "day_in_season": 3,

  // 输入快照
  "inputs": {
    "environment": { "temperature": 25.3, "humidity": 82.5, "light": 6500 },
    "yolo_metrics": { "leaf_instance_count": 4.5, ... },
    "image_path": "data/images/0314.jpg"
  },

  // 模型输出
  "predictions": {
    "tsmixer_raw": 5.2,
    "plant_response": { "trend": "better", "confidence": 0.78, ... },
    "sanity_check": { "accept": true, "risk_level": "low", ... }
  },

  // 异常检测
  "anomalies": {
    "out_of_range": false,
    "trend_conflict": false,
    "trend_conflict_severity": "none",
    "env_anomaly": true,
    "env_anomaly_type": "high_humidity"
  },

  // RAG 检索记录（仅记录 doc_id，不存内容）
  "rag_doc_ids": ["fao56_ch8_001", "fao56_ch8_002"],

  // 最终决策
  "final_decision": {
    "value": 5.0,
    "source": "tsmixer",  // tsmixer | override
    "override_reason": null
  },

  // 用户反馈
  "user_feedback": {
    "actual_irrigation": 5.0,
    "notes": "略微减少灌水",
    "rating": null  // 1-5 评分
  },

  // 元数据
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**检索场景**：

| 场景 | 检索方式 | 示例 |
|------|----------|------|
| 相似异常 | 向量检索 + 过滤 | 查找历史上同类型 trend_conflict 事件 |
| 同生育期 | 日期范围 + growth_stage | 去年同期开花期的处理方式 |
| Override 学习 | source=override 过滤 | 人工覆盖的案例及理由 |

### 4.5 L3 Recent Summary（周摘要）

**定义**：每周聚合生成的经验总结，用于动态 Prompt 注入。

**关键原则**：
- ✅ 永久落库到 `MongoDB.weekly_summaries`
- ✅ 注入时**只用 prompt_block 字段**
- ⚠️ prompt_block 有最大长度限制：**≤800 tokens（约1200字）**
- 超限处理：只保留 `key_insights`，删除 `trend_stats`、`irrigation_stats` 等细节

**数据结构**：

```
MongoDB Collection: weekly_summaries

{
  "_id": ObjectId,
  "week_start": "2025-03-10",
  "week_end": "2025-03-16",
  "season": "spring_2025",

  // 统计数据（落库但不注入）
  "trend_stats": {
    "better_days": 3,
    "same_days": 2,
    "worse_days": 2,
    "dominant_trend": "better"
  },
  "irrigation_stats": {
    "total": 42.5,
    "daily_avg": 6.07,
    "max": 8.2,
    "min": 3.1,
    "trend": "increasing"
  },
  "anomaly_events": [...],
  "override_summary": {...},

  // 关键洞察（用于生成 prompt_block）
  "key_insights": [
    "本周进入开花期，需水量上升15%",
    "3/12-3/14连续高湿，已减少灌水20%",
    "3/14出现长势-灌水矛盾，建议关注"
  ],

  // ⭐ 核心：用于注入的 Prompt 块
  "prompt_block": "## 上周经验 (3/10-3/16)\n- 开花期，需水量+15%\n- 连续高湿，灌水-20%\n- 1次长势矛盾，需关注",
  "prompt_block_tokens": 85,  // token 计数

  "created_at": ISODate
}
```

**prompt_block 生成规则**：

| 优先级 | 内容 | 说明 |
|--------|------|------|
| 1 | key_insights | 必须保留，核心经验 |
| 2 | dominant_trend + irrigation_trend | 趋势概述 |
| 3 | anomaly_events 摘要 | 关键异常事件 |
| 4 | override_summary | 人工覆盖回顾 |

**超限压缩策略**：
```
IF prompt_block_tokens > 800:
    1. 删除 override_summary
    2. 压缩 anomaly_events（只保留 severe 级别）
    3. 保留 key_insights 前3条
    4. 如仍超限，只保留 key_insights 第1条
```

### 4.6 L4 Knowledge Memory（知识库）

**定义**：外部知识存储，包括 FAO56、温室灌溉文献、历史经验片段。

**存储架构**：
- Milvus：向量索引（BGE-M3 混合检索）
- MongoDB：文档原文和元数据

**检索策略**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| TopK | 3~5 | 检索返回数量 |
| 优先级 | is_fao56=true 优先 | FAO56 内容优先返回 |
| 过滤 | 按 content_type 过滤 | 可过滤 formula/table/text |

**不复制原则**：
- cucumber-irrigation 直接访问 Greenhouse_RAG 的 `greenhouse_db.literature_chunks`
- 不复制 FAO56 内容到新库，避免数据冗余

---

## 5. Q4: 上下文注入预算控制（Rule-M1）

### 5.1 规则定义

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Rule-M1: 注入预算控制                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  每次 LLM 调用的上下文组成：                                                 │
│                                                                             │
│  Total = System(固定) + Weekly(prompt_block) + Today(输入) + Retrieval(TopK)│
│                                                                             │
│  预算分配：                                                                  │
│  ┌─────────────┬──────────────┬──────────────────────────────────────────┐ │
│  │ 组成部分    │ 预算上限     │ 说明                                     │ │
│  ├─────────────┼──────────────┼──────────────────────────────────────────┤ │
│  │ System      │ ~500 tokens  │ 固定，不可压缩                           │ │
│  │ Weekly      │ ≤800 tokens  │ prompt_block 上限                        │ │
│  │ Today       │ ~2000 tokens │ 环境+YOLO+对比结论                       │ │
│  │ Retrieval   │ ~1000 tokens │ TopK=3~5 片段                            │ │
│  ├─────────────┼──────────────┼──────────────────────────────────────────┤ │
│  │ **总计**    │ **≤4500**    │ 预留空间给模型输出                       │ │
│  └─────────────┴──────────────┴──────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 超预算处理策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           超预算处理优先级                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  当 Total > 预算上限 时，按以下优先级压缩：                                  │
│                                                                             │
│  优先级 1（最先删除）：Retrieval                                            │
│     ├─ 减少 TopK 数量：5 → 3 → 1                                           │
│     └─ 如仍超限，完全删除 Retrieval                                         │
│                                                                             │
│  优先级 2：Weekly (prompt_block)                                            │
│     ├─ 只保留 key_insights                                                  │
│     └─ 如仍超限，只保留 key_insights[0]                                     │
│                                                                             │
│  优先级 3（最后压缩）：Today                                                 │
│     ├─ 删除 evidence 详细描述，保留结构化 JSON                              │
│     ├─ 删除 comparison 详细描述                                             │
│     └─ 保留核心字段：trend, confidence, growth_stage, abnormalities        │
│                                                                             │
│  不可压缩：System Prompt                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 配置参数

```yaml
# configs/memory.yaml

context_budget:
  total_max: 4500           # 总上下文预算 (tokens)
  system_fixed: 500         # System Prompt 固定占用
  weekly_max: 800           # prompt_block 上限
  today_max: 2000           # 今日输入上限
  retrieval_max: 1000       # 检索结果上限
  retrieval_default_k: 3    # 默认 TopK

compression:
  priority:                 # 压缩优先级（数字越小越先压缩）
    retrieval: 1
    weekly: 2
    today: 3
  today_keep_fields:        # Today 压缩后保留的字段
    - trend
    - confidence
    - growth_stage
    - abnormalities
```

### 5.4 Token 计数实现

| 方法 | 说明 | 精度 |
|------|------|------|
| tiktoken | OpenAI 官方分词器 | 高 |
| 字符估算 | 中文~0.5 token/字，英文~0.25 token/字 | 中 |
| 实际返回 | API 返回的 usage.prompt_tokens | 精确 |

**建议**：使用 tiktoken 预估，API 返回值校验。

---

## 6. Q5: 数据库架构设计

### 6.1 架构选择：同实例分库方案

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据库架构                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MongoDB 实例 (localhost:27017)                                             │
│  ├── greenhouse_db              # Greenhouse_RAG 原有库（只读访问）          │
│  │   └── literature_chunks      # FAO56等文献片段                           │
│  │                                                                          │
│  └── cucumber_irrigation        # cucumber-irrigation 业务库（新建）         │
│      ├── episodes               # L2: 每日日志                              │
│      ├── weekly_summaries       # L3: 周摘要                                │
│      ├── overrides              # Override 记录                             │
│      └── learning_events        # 学习事件（偏差>20%）                       │
│                                                                             │
│  Milvus 实例 (localhost:19530 / milvus.db)                                  │
│  ├── greenhouse_bge_m3          # Greenhouse_RAG 原有集合（知识检索）        │
│  └── cucumber_episodes          # 可选：episode 向量化（相似异常检索）        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 方案优势

| 优势 | 说明 |
|------|------|
| FAO56 复用 | 直接访问 Greenhouse_RAG 已入库的文献，无需重复导入 |
| 业务隔离 | cucumber-irrigation 的 episodes 等业务数据独立存储 |
| 维护简单 | 同一个 MongoDB/Milvus 实例，无需额外部署 |
| 跨库访问 | MongoDB 支持跨 database 查询 |

### 6.3 集合设计

#### cucumber_irrigation.episodes

| 字段 | 类型 | 索引 | 说明 |
|------|------|------|------|
| date | string | unique | 日期 YYYY-MM-DD |
| season | string | index | 茬口标识 |
| day_in_season | int | - | 茬口第几天 |
| inputs | object | - | 输入快照 |
| predictions | object | - | 模型输出 |
| anomalies | object | - | 异常检测结果 |
| final_decision | object | - | 最终决策 |
| user_feedback | object | - | 用户反馈 |

#### cucumber_irrigation.weekly_summaries

| 字段 | 类型 | 索引 | 说明 |
|------|------|------|------|
| week_start | string | unique | 周起始日期 |
| week_end | string | - | 周结束日期 |
| season | string | index | 茬口标识 |
| prompt_block | string | - | 用于注入的文本 |
| prompt_block_tokens | int | - | token 计数 |
| key_insights | array | - | 关键洞察 |

#### cucumber_irrigation.overrides

| 字段 | 类型 | 索引 | 说明 |
|------|------|------|------|
| date | string | index | 日期 |
| original_value | float | - | 原预测值 |
| replaced_value | float | - | 覆盖值 |
| reason | string | text | 覆盖理由 |

### 6.4 跨库访问配置

```python
# 访问 Greenhouse_RAG 的文献库
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

# 业务库
cucumber_db = client["cucumber_irrigation"]
episodes = cucumber_db["episodes"]

# 知识库（只读访问）
greenhouse_db = client["greenhouse_db"]
literature = greenhouse_db["literature_chunks"]

# 跨库查询示例：获取 FAO56 片段
fao56_docs = literature.find({"is_fao56": True}).limit(10)
```

---

## 7. Q6: 周总结动态 Prompt 注入机制

### 7.1 波动 Prompt 机制

**定义**：每周生成的 `weekly_summary_block` 作为可变上下文注入到下一周的 LLM 调用 Prompt 中，使模型具有"近期经验记忆"。

### 7.2 注入位置

```
┌─────────────────────────────────────────────────────────────┐
│                    Prompt 结构                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. System Prompt（固定部分）                               │
│     ├─ 角色定义                                             │
│     ├─ 输出格式要求                                         │
│     └─ 评估维度说明                                         │
│                                                             │
│  2. Weekly Context（波动部分）← 动态注入                    │
│     └─ <recent_experience>                                  │
│        {prompt_block from weekly_summaries}                 │
│        </recent_experience>                                 │
│                                                             │
│  3. User Prompt（每日变化）                                 │
│     ├─ 今日环境数据                                         │
│     ├─ YOLO 指标                                            │
│     └─ 图像对比请求                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 注入内容格式

```markdown
<recent_experience>
## 上周经验总结 ({week_start} - {week_end})

### 长势趋势
- 本周主要趋势：{dominant_trend}
- 好转天数：{better_days}，持平：{same_days}，变差：{worse_days}

### 灌水量统计
- 日均灌水量：{daily_avg} L/m²
- 变化趋势：{irrigation_trend}
- 较上周变化：{week_over_week_change}

### 关键事件
{anomaly_events 列表}

### 经验提示
{key_insights 列表}

请结合上周经验，分析今日植物状态和灌水建议。
</recent_experience>
```

### 7.4 注入时机

| 时机 | 动作 |
|------|------|
| 每周日 20:00 | 运行 WeeklyPipeline，生成新的 weekly_summary |
| 每日运行 | 从 MongoDB 获取最新 weekly_summary.prompt_block |
| 每日注入 | 将 prompt_block 注入当日 SanityCheck 的 System Prompt |

### 7.5 记忆固化流程

```
┌─────────────────────────────────────────────────────────────┐
│                    记忆固化流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  每日：                                                      │
│  ├─ 用户输入 → DailyEpisode                                 │
│  ├─ 异常事件 → 标记在 episode.anomalies                     │
│  └─ Override → 记录原因到 episode.user_feedback             │
│                                                             │
│  每周：                                                      │
│  ├─ 聚合 7 天 Episodes                                      │
│  ├─ 提取统计指标和异常事件                                   │
│  ├─ LLM 生成 key_insights                                   │
│  ├─ 生成 prompt_block                                       │
│  └─ 存储到 weekly_summaries                                 │
│                                                             │
│  效果：                                                      │
│  └─ "高价值事件"通过 weekly_summary 固化为下周的动态 Prompt  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Q7: 知识增强评估机制

### 8.1 设计背景

**问题**：
- 当前 PlantResponse 长势描述缺乏客观依据
- 周度经验总结过于主观，缺少文献支撑
- 生育期判断与专业知识脱节

**解决方案**：
- GPT-5.2 预判生育期 + RAG 检索相关文献
- 将文献知识注入评估过程
- 生成有客观依据的长势描述和经验总结

### 8.2 生育期预判与知识注入 (PlantResponse 增强)

#### 8.2.1 流程设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      知识增强的 PlantResponse 生成流程                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: 生育期预判                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  输入: 今日图像                                                       │   │
│  │  模型: GPT-5.2 (视觉)                                                │   │
│  │  输出: growth_stage (vegetative/flowering/fruiting/mixed)           │   │
│  │                                                                     │   │
│  │  判断依据:                                                           │   │
│  │  ├─ vegetative: 主要可见叶片，无明显花朵/果实                          │   │
│  │  ├─ flowering: 可见黄色花朵，可能有小果                               │   │
│  │  ├─ fruiting: 可见发育中的果实（黄瓜）                                │   │
│  │  └─ mixed: 多种生育期特征并存                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Step 2: 知识库检索                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  查询构建:                                                           │   │
│  │  ├─ 基础查询: "cucumber {growth_stage} water requirement Kc"        │   │
│  │  ├─ FAO56 优先: is_fao56=true                                       │   │
│  │  └─ 补充查询: "cucumber {growth_stage} growth characteristics"      │   │
│  │                                                                     │   │
│  │  检索结果 (TopK=2-3):                                                │   │
│  │  ├─ FAO56 Table 12: 黄瓜各生育期 Kc 系数                              │   │
│  │  ├─ FAO56 Chapter 6: 作物需水规律                                    │   │
│  │  └─ 温室黄瓜栽培文献: 该生育期典型特征                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Step 3: 知识增强的长势评估                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Prompt 注入:                                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ <growth_stage_knowledge>                                    │    │   │
│  │  │ ## 当前生育期: {growth_stage}                               │    │   │
│  │  │                                                             │    │   │
│  │  │ ### FAO56 参考                                              │    │   │
│  │  │ - Kc 系数: {kc_value}                                       │    │   │
│  │  │ - 需水特征: {water_requirement_description}                 │    │   │
│  │  │                                                             │    │   │
│  │  │ ### 该生育期典型特征                                         │    │   │
│  │  │ - {retrieved_characteristics}                               │    │   │
│  │  │                                                             │    │   │
│  │  │ 请结合以上专业知识评估今日长势。                              │    │   │
│  │  │ </growth_stage_knowledge>                                   │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  输出: PlantResponse                                                │   │
│  │  ├─ comparison.evidence: 引用文献依据                               │   │
│  │  ├─ key_observations: 结合 Kc 系数分析                              │   │
│  │  └─ knowledge_references: 引用的文献 ID 列表                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 8.2.2 PlantResponse 结构扩展

```json
{
  "date": "2025-03-15",
  "growth_stage": "flowering",
  "growth_stage_confidence": 0.85,

  "comparison": {
    "trend": "better",
    "confidence": 0.82,
    "evidence": "叶片面积增长12%，符合开花期正常生长速率。根据FAO56，开花期Kc系数0.9-1.0，需水量较营养期增加，当前灌水量与需水规律一致。"
  },

  "abnormalities": {
    "wilting": false,
    "yellowing": false,
    "pest_damage": null,
    "other": null
  },

  "key_observations": [
    "进入开花期，可见多朵黄色雌花",
    "叶片面积稳定增长，符合FAO56开花期生长曲线",
    "根据文献，开花期需水量增加10-15%，建议关注灌水响应"
  ],

  "knowledge_references": [
    {
      "doc_id": "fao56_table12_cucumber",
      "snippet": "Cucumber Kc: Initial 0.6, Mid-season 1.0, Late 0.75",
      "relevance": "high"
    },
    {
      "doc_id": "greenhouse_cucumber_growth_2020",
      "snippet": "开花期黄瓜日需水量约4-6L/m²，较营养期增加15%",
      "relevance": "medium"
    }
  ]
}
```

#### 8.2.3 生育期检索查询模板

| 生育期 | 检索查询 | 预期检索内容 |
|--------|----------|--------------|
| vegetative | `cucumber vegetative stage Kc leaf growth water requirement` | Kc=0.6-0.7, 营养生长特征 |
| flowering | `cucumber flowering stage Kc flower development water stress` | Kc=0.9-1.0, 开花期需水增加 |
| fruiting | `cucumber fruiting stage Kc fruit development irrigation` | Kc=1.0-1.05, 果实膨大期需水峰值 |
| mixed | `cucumber transition growth stage Kc adjustment` | 过渡期管理要点 |

### 8.3 知识增强的周度总结 (WeeklySummary 增强)

#### 8.3.1 流程设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      知识增强的 WeeklySummary 生成流程                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: 本周数据聚合                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  统计项:                                                             │   │
│  │  ├─ 主要生育期: 本周出现最多的 growth_stage                          │   │
│  │  ├─ 趋势统计: better/same/worse 天数                                │   │
│  │  ├─ 异常事件: A1/A2/A3 触发记录                                     │   │
│  │  ├─ Override 记录: 人工覆盖及理由                                   │   │
│  │  └─ 灌水统计: 日均、最大、最小、趋势                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Step 2: 知识库检索 (根据本周特征)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  检索策略:                                                           │   │
│  │                                                                     │   │
│  │  A. 生育期相关知识                                                   │   │
│  │     查询: "cucumber {dominant_stage} weekly management irrigation"  │   │
│  │     目的: 获取该生育期的周度管理要点                                  │   │
│  │                                                                     │   │
│  │  B. 异常处理知识 (如有异常)                                          │   │
│  │     查询: "cucumber {anomaly_type} recovery management"             │   │
│  │     目的: 获取异常恢复的专业建议                                      │   │
│  │                                                                     │   │
│  │  C. 季节性知识                                                       │   │
│  │     查询: "cucumber spring greenhouse irrigation pattern"           │   │
│  │     目的: 获取当前季节的灌溉规律                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Step 3: 知识增强的经验生成                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Prompt 注入:                                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ <weekly_knowledge_context>                                  │    │   │
│  │  │ ## 本周生育期: {dominant_stage}                             │    │   │
│  │  │                                                             │    │   │
│  │  │ ### 专业文献参考                                             │    │   │
│  │  │ {retrieved_knowledge_snippets}                              │    │   │
│  │  │                                                             │    │   │
│  │  │ ### 本周数据摘要                                             │    │   │
│  │  │ {week_statistics}                                           │    │   │
│  │  │                                                             │    │   │
│  │  │ 请结合专业知识和本周数据，生成经验总结。                       │    │   │
│  │  │ 经验应有文献依据，避免纯主观判断。                            │    │   │
│  │  │ </weekly_knowledge_context>                                 │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  输出: key_insights (知识增强版)                                     │   │
│  │  ├─ 每条 insight 标注来源: [经验] / [文献] / [数据]                 │   │
│  │  └─ 包含文献引用                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 8.3.2 WeeklySummary 结构扩展

```json
{
  "week_start": "2025-03-10",
  "week_end": "2025-03-16",
  "season": "spring_2025",
  "dominant_stage": "flowering",

  "trend_stats": {
    "better_days": 3,
    "same_days": 2,
    "worse_days": 2,
    "dominant_trend": "better"
  },

  "irrigation_stats": {
    "total": 42.5,
    "daily_avg": 6.07,
    "max": 8.2,
    "min": 3.1,
    "trend": "increasing"
  },

  "anomaly_events": [...],
  "override_summary": {...},

  "key_insights": [
    {
      "content": "本周进入开花期，日均灌水量6.07L/m²，符合FAO56建议的Kc=0.9-1.0范围",
      "source": "literature",
      "reference": "fao56_table12"
    },
    {
      "content": "3/12-3/14连续高湿(>85%)，根据温室病害防控指南，已适当减少灌水20%",
      "source": "literature+data",
      "reference": "greenhouse_disease_prevention_2021"
    },
    {
      "content": "3/14出现长势-灌水矛盾(trend=worse但灌水减少)，下周需关注",
      "source": "data",
      "reference": null
    }
  ],

  "knowledge_references": [
    {
      "doc_id": "fao56_table12",
      "usage": "Kc系数参考",
      "snippet": "Cucumber flowering stage Kc: 0.9-1.0"
    },
    {
      "doc_id": "greenhouse_disease_prevention_2021",
      "usage": "高湿处理建议",
      "snippet": "连续高湿环境下，减少灌水量15-25%可降低病害风险"
    }
  ],

  "prompt_block": "## 上周经验 (3/10-3/16)\n- [文献] 开花期Kc=0.9-1.0，日均灌水6.07L/m²符合预期\n- [文献+数据] 高湿期减灌20%，参考病害防控指南\n- [数据] 1次矛盾事件，需关注",
  "prompt_block_tokens": 95
}
```

#### 8.3.3 key_insights 来源标注

| 来源标注 | 说明 | 示例 |
|----------|------|------|
| `[文献]` | 主要依据来自检索到的文献 | "根据FAO56，开花期Kc=0.9-1.0" |
| `[数据]` | 主要依据来自本周统计数据 | "本周出现2次矛盾事件" |
| `[文献+数据]` | 结合文献和数据分析 | "高湿期减灌20%（参考文献），实际执行效果良好（数据验证）" |
| `[经验]` | 基于历史 Override 或累积经验 | "该用户倾向于在阴天多灌水" |

### 8.4 知识检索优先级

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          知识检索优先级策略                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  优先级 1: FAO56 权威文献                                                    │
│  ├─ is_fao56 = true                                                        │
│  ├─ 内容类型: Kc系数、需水公式、生育期定义                                   │
│  └─ 权重: 1.5x                                                             │
│                                                                             │
│  优先级 2: 温室黄瓜专业文献                                                   │
│  ├─ crop_type = "cucumber"                                                 │
│  ├─ environment = "greenhouse"                                             │
│  └─ 权重: 1.2x                                                             │
│                                                                             │
│  优先级 3: 一般灌溉/作物文献                                                  │
│  ├─ 相关性匹配                                                              │
│  └─ 权重: 1.0x                                                             │
│                                                                             │
│  优先级 4: 历史 Episode (如有向量化)                                         │
│  ├─ 相似场景的历史处理方式                                                   │
│  └─ 权重: 0.8x                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.5 配置参数

```yaml
# configs/knowledge_enhancement.yaml

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

## 9. 验收标准补充

### 9.1 Q1 验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| Q1.1 | 滚动预测实现 | 输入96步序列，输出单一灌水量值 |
| Q1.2 | 冷启动填充 | 数据不足时自动用2023年春茬数据填充 |
| Q1.3 | 日期对齐 | 填充数据与目标日期月日对应 |

### 9.2 Q2 验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| Q2.1 | 范围异常检测 | 预测值超出 [0.1, 15.0] 时触发 |
| Q2.2 | 矛盾检测 | trend=worse 且灌水减少时判定为 severe |
| Q2.3 | 环境异常检测 | 连续3天高湿/高温/弱光时触发 |
| Q2.4 | RAG 辅助 | 异常时返回 FAO56 相关建议片段 |

### 9.3 Q3-Q4 验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| Q3.1 | 4层记忆落库 | L2/L3/L4 永久存储，L1 可选 |
| Q3.2 | 注入预算控制 | 总上下文 ≤4500 tokens |
| Q3.3 | 超限压缩 | 按优先级 Retrieval→Weekly→Today 压缩 |
| Q4.1 | prompt_block 限制 | ≤800 tokens，超限只保留 key_insights |

### 9.4 Q5-Q6 验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| Q5.1 | 同实例分库 | cucumber_irrigation 独立，跨库访问 greenhouse_db |
| Q5.2 | 知识库复用 | 直接访问 Greenhouse_RAG 的 FAO56 |
| Q6.1 | Prompt 注入 | 周总结成功注入下周 Prompt |
| Q6.2 | 记忆连贯性 | LLM 输出体现对上周经验的引用 |

### 9.5 Q7 验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| Q7.1 | 生育期预判 | GPT-5.2 根据图像判断 growth_stage，置信度 ≥0.7 |
| Q7.2 | 知识增强 PlantResponse | evidence 字段引用 FAO56/文献内容 |
| Q7.3 | 知识增强 WeeklySummary | key_insights 标注来源 [文献]/[数据]/[经验] |
| Q7.4 | 检索优先级 | FAO56 优先返回 (权重 1.5x) |
| Q7.5 | 知识引用记录 | PlantResponse/WeeklySummary 包含 knowledge_references |

---

## 10. 附录

### 10.1 阈值配置表

```yaml
# configs/thresholds.yaml

# A1: 历史范围阈值
irrigation_range:
  min: 0.1
  max: 15.0
  mean: 5.5
  std: 3.5

# A2: 长势-灌水矛盾阈值
trend_conflict:
  severe_decrease_threshold: -0.10    # 灌水减少超过10%
  moderate_increase_threshold: 0.10   # 灌水增加不足10%
  severe_abnormality_threshold: 0.20  # 有严重异常时灌水增加不足20%
  mild_increase_threshold: 0.30       # 长势好时灌水增加超过30%

# A3: 环境异常阈值
env_anomaly:
  consecutive_days: 3                 # 连续天数阈值
  high_humidity: 85                   # 高湿阈值 (%)
  high_temperature: 35                # 高温阈值 (°C)
  low_light: 2000                     # 弱光阈值 (lux)
```

### 10.2 记忆配置表

```yaml
# configs/memory.yaml

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
```

### 10.3 相关项目引用

| 项目 | 路径 | 引用内容 |
|------|------|----------|
| Irrigation | G:\Wyatt\Irrigation | TSMixer 模型结构、数据加载器 |
| Greenhouse_RAG | G:\Wyatt\Greenhouse_RAG | MongoDB/Milvus 配置、RAG 检索逻辑 |

### 10.4 数据文件引用

| 文件 | 路径 | 用途 |
|------|------|------|
| irrigation_pre.csv | cucumber-irrigation/data/csv/ | 冷启动填充数据源 |
| irrigation_final_11.17.xlsx | Irrigation/data/Irrigation/ | TSMixer 训练数据参考 |
