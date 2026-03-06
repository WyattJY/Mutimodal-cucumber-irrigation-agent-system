# 温室黄瓜灌水智能体系统 - 需求规范文档

> 版本：v1.2
> 更新日期：2024-12-25
> 文档状态：**需求已澄清，准备进入 Phase 0**

---

## 1. SPEC 需求定义

### 1.1 S — Scope（范围：做什么，不做什么）

#### ✅ 要做

| 编号 | 功能 | 说明 |
|------|------|------|
| S1 | YOLO + TSMixer 集成 | 将已有的 YOLO11n-FCHL（表型特征）与 TSMixer（灌水量预测）组织成可运行的灌水决策系统 |
| S2 | GPT-5.2 长势对比 | 输入昨日图A vs 今日图B + YOLO指标，输出结构化 PlantResponse |
| S3 | GPT-5.2 合理性复核 | 对 TSMixer 输出做 SanityCheck（ok/alert + 问种植人员的问题清单） |
| S4 | GPT-5.2 周度总结 | 每周汇总过去7天 episode，生成 weekly_summary_block，动态注入下周 prompt |
| S5 | 经验库 | MongoDB 存储 episode、人工 override、理由、检索评分 |
| S6 | 向量检索 | Milvus 存储知识向量，支持相似 episode/文献检索 |

#### ❌ 不做

| 编号 | 排除项 | 原因 |
|------|--------|------|
| X1 | 发明新灌水机理公式 | 不做 αβγ 权重融合，灌水量以 TSMixer（FAO56 训练）为准 |
| X2 | 阀门控制逻辑 | 只输出灌水量数值，RS485/STM32 是下游系统负责 |
| X3 | 实时流媒体处理 | 系统按日批量运行，不做实时视频分析 |

---

### 1.2 P — Problem（要解决的核心问题）

| 问题编号 | 问题描述 | 当前痛点 |
|----------|----------|----------|
| P1 | TSMixer 输出缺少可解释性 | 模型给出灌水量，但不知道"为什么是这个值" |
| P2 | 缺少预警机制 | 异常情况（萎蔫、黄化、极端天气）没有提前预警 |
| P3 | 人工无法介入 | 种植人员发现问题时，无法记录替代决策和理由 |
| P4 | 经验无法沉淀 | 每茬试验的处理与效果不能自动积累成可检索知识 |
| P5 | 缺少持续提升机制 | 系统无法用"记忆+反思"让下一周更稳定 |

---

### 1.3 E — Execution（怎么落地执行）

#### 每日流程

```
┌─────────────────────────────────────────────────────────────┐
│                        每日执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入：                                                      │
│  ├─ 今日图像 B (2880×1620)                                   │
│  ├─ 昨日图像 A                                               │
│  ├─ 环境序列 (window=96)                                     │
│  └─ YOLO 表型指标                                            │
│                                                             │
│  处理：                                                      │
│  ├─ YOLO 推理 → YOLOMetrics                                  │
│  ├─ TSMixer 推理 → 预测灌水量                                 │
│  ├─ GPT-5.2 长势评估 → PlantResponse.json                    │
│  └─ GPT-5.2 合理性复核 → SanityCheck.json                    │
│                                                             │
│  输出：                                                      │
│  ├─ 最终灌水量（TSMixer 预测 或 人工 Override）               │
│  ├─ 预警信息（如有）                                         │
│  └─ Episode 入库                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 每周流程

```
┌─────────────────────────────────────────────────────────────┐
│                        每周执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入：                                                      │
│  └─ 近 7 天 Episodes (从 MongoDB 拉取)                       │
│                                                             │
│  处理：                                                      │
│  └─ GPT-5.2 周度反思 → weekly_summary_block.json             │
│                                                             │
│  输出：                                                      │
│  ├─ 规律总结                                                 │
│  ├─ 风险触发条件                                             │
│  ├─ Override 回顾                                            │
│  └─ 注入下周 Prompt（"波动 Prompt"）                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 关键产物

| 产物 | 格式 | 说明 |
|------|------|------|
| PlantResponse | JSON | 长势对比评估（trend: better/same/worse） |
| SanityCheck | JSON | 合理性复核（accept + risk_level + questions） |
| Episode | MongoDB Doc | 每日完整决策记录 |
| WeeklySummaryBlock | JSON | 周度总结，注入 Prompt |

---

### 1.4 C — Criteria（验收标准）

#### MVP（第一阶段）验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| C1 | 历史数据离线跑通 | 2024/03/14–2024/06/14 至少 80% 天数成功产出 JSON |
| C2 | 结构化输出 | PlantResponse / SanityCheck 字段齐全，缺失填 null |
| C3 | 预警机制可用 | 不合理时输出"要问种植人员的具体问题" |
| C4 | Override 入库 | 人工替代水量+理由能入库，周总结中被提及 |
| C5 | 动态 Prompt | 次周 prompt 能自动注入上周总结块 |

#### 增强版（第二阶段）验收

| 编号 | 验收项 | 标准 |
|------|--------|------|
| C6 | 相似检索 | Milvus 检索可用，输出能引用片段 ID |
| C7 | 检索评分 | 用户可对检索语录评分（无评分存 null） |
| C8 | 一致率 | PlantResponse trend 与人工标注一致率 > 80% |

---

## 2. 目标用户

### 2.1 主要用户（Primary Users）

#### 👨‍🌾 温室种植/生产管理人员（操作者）

| 需求 | 说明 |
|------|------|
| 每日查看 | 今天灌水量、是否预警、为什么、需要我确认什么 |
| Override | 可以覆盖系统建议，输入替代值和理由 |
| 简单交互 | 不需要技术背景，看懂中文输出即可 |

#### 👩‍🔬 实验室研究人员（建模与实验负责人）

| 需求 | 说明 |
|------|------|
| 批量离线 | 跑历史数据，生成可分析的 episode 数据集 |
| 周报分析 | 每周总结报告、处理差异对比 |
| 经验检索 | 可检索历史相似案例 |
| Prompt 调优 | 根据输出质量迭代优化 Prompt |

### 2.2 次要用户（Secondary Users）

#### 🛠️ 灌溉控制系统同学

| 需求 | 说明 |
|------|------|
| 获取灌水量 | 只需拿到"最终灌水量数值 + 时间" |
| 接口简单 | 不关心内部推理细节 |

#### 📊 论文/项目评审方

| 需求 | 说明 |
|------|------|
| 系统闭环 | 看到完整的输入→推理→输出→反馈链条 |
| 可解释 | 理解"为什么给这个灌水量" |
| 可追溯 | 历史决策可查询 |
| 持续改进 | 记忆+反思机制可演示 |

---

## 3. 当前阶段重点（Phase 0）

### 3.1 最优先任务：PlantResponse 生成与调优

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 0: Prompt 调优                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  目标：用历史数据跑通长势评估，人工审核后迭代优化 Prompt        │
│                                                             │
│  步骤：                                                      │
│  ┌─────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ 历史 │───▶│ 生成    │───▶│ 人工    │───▶│ 优化    │      │
│  │ 数据 │    │ 长势评估 │    │ 审核    │    │ Prompt  │      │
│  └─────┘    └─────────┘    └─────────┘    └─────────┘      │
│                                                             │
│  输入：                                                      │
│  ├─ data/images/*.jpg (85张图像)                             │
│  └─ data/csv/irrigation.csv (93行数据)                       │
│                                                             │
│  输出：                                                      │
│  ├─ plant_response_{date}.json × N                          │
│  └─ 人工标注的 ground_truth.jsonl                            │
│                                                             │
│  迭代：                                                      │
│  ├─ 第1轮：零样本 Prompt，生成全量，人工标注 50 对            │
│  ├─ 第2轮：加入典型错例作为 few-shot，重跑                   │
│  └─ 第3轮：一致率 > 80% 后进入下一阶段                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 0 具体任务

| 任务编号 | 任务名称 | 输入 | 输出 | 验收标准 |
|----------|----------|------|------|----------|
| P0.1 | 构建日期配对 | images/*.jpg | pairs_index.json | 每个日期有 today/yesterday 配对 |
| P0.2 | 批量生成 PlantResponse | pairs + prompt | plant_responses/*.json | 80%+ 日期成功生成 |
| P0.3 | 人工审核标注 | plant_responses/*.json | ground_truth.jsonl | 50 对人工标注 |
| P0.4 | 计算一致率 | predictions vs ground_truth | consistency_report.md | 输出一致率 + 错误分析 |
| P0.5 | Few-shot 优化 | 错例分析 | examples_v2.jsonl | 加入典型错例 |
| P0.6 | 回归测试 | 优化后 prompt | 全量重跑 | 一致率 > 80% |

### 3.3 PlantResponse 输出结构定义

```json
{
  "date": "2024-03-15",
  "comparison": {
    "trend": "better | same | worse",
    "confidence": 0.85,
    "evidence": "叶片平均掩码从 710 增至 820，增幅 15%，高于全生育期平均增长率"
  },
  "abnormalities": {
    "wilting": false,
    "yellowing": false,
    "pest_damage": null,
    "other": null
  },
  "growth_stage": "vegetative | flowering | fruiting | mixed",
  "key_observations": [
    "叶片总掩码面积增长 15%，高于平均水平",
    "多株黄瓜整体长势良好",
    "未观察到萎蔫或病害迹象"
  ]
}
```

**trend 判定逻辑：**

```
IF 有明显病害 OR 有明显萎蔫:
    trend = "worse"
ELIF 叶片mask增长率 > 全生育期平均增长率 (明显高):
    trend = "better"
ELIF 叶片mask增长率 ≈ 全生育期平均增长率:
    trend = "same"  # 可接受轻微萎蔫
ELSE:  # 增长率明显低于平均
    trend = "worse"
```

**全生育期平均增长率参考**（基于 irrigation.csv 计算）：

| 指标 | 计算方式 | 用途 |
|------|----------|------|
| all_leaf_mask 日均增长率 | (末值 - 初值) / 天数 | 作为判定 better/same/worse 的基准 |

### 3.4 人工标注格式

```jsonl
{"date": "2024-03-15", "human_trend": "better", "human_confidence": 0.9, "notes": "叶片明显增多，颜色更绿"}
{"date": "2024-03-16", "human_trend": "same", "human_confidence": 0.7, "notes": "变化不明显，阴天光照差"}
{"date": "2024-03-17", "human_trend": "worse", "human_confidence": 0.85, "notes": "温度骤降，叶片略微下垂"}
```

---

## 4. 数据资产

### 4.1 可用数据

| 数据类型 | 路径 | 规模 | 格式 |
|----------|------|------|------|
| 监控图像 | data/images/*.jpg | 85 张 | 2880×1620 JPG |
| 环境+灌水量 | data/csv/irrigation.csv | 93 行 | TSV |
| YOLO 权重 | v11_4seg/.../best.pt | 1 个 | PyTorch |
| TSMixer 权重 | Irrigation/model.pt | 1 个 | PyTorch |

### 4.2 irrigation.csv 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| date | string | 日期 YYYY/M/D |
| temperature | float | 日均温度 °C |
| humidity | float | 日均湿度 % |
| light | float | 日均光照 lux |
| leaf Instance Count | float | 叶片实例数量 |
| leaf average mask | float | 叶片平均掩码面积 |
| flower Instance Count | float | 花朵实例数量 |
| flower Mask Pixel Count | float | 花朵掩码像素总数 |
| terminal average Mask Pixel Count | float | 顶芽平均掩码面积 |
| fruit Mask average | float | 果实平均掩码面积 |
| all leaf mask | float | 全部叶片掩码总面积 |
| Target | float | 当日实际灌水量 L/m² |

### 4.3 图像命名规则

```
格式：MMDD.jpg 或 MMDD.JPG
示例：0314.jpg → 2024年3月14日
范围：0314 (3/14) ~ 0614 (6/14)
```

---

## 5. 技术约束

### 5.1 模型约束

| 模型 | 定位 | 约束 |
|------|------|------|
| YOLO11n-FCHL | 工具服务 | 不作为 Agent，只做推理 |
| TSMixer | 工具服务 | 灌水量以其输出为准，LLM 不计算 |
| GPT-5.2 | 决策支持 | 评估、解释、预警，不发明公式 |

### 5.2 输出约束

| 约束项 | 说明 |
|--------|------|
| 结构化 JSON | 所有 LLM 输出必须是严格 JSON |
| 缺失填 null | 字段不确定时填 null，不报错 |
| 中文输出 | 面向种植人员，输出用中文 |

### 5.3 性能约束

| 指标 | 目标值 |
|------|--------|
| 单日推理 | < 60s（含 LLM 调用） |
| 批量处理 | 93 天数据 < 2 小时 |

---

## 6. 问题澄清（已确认）

### Q1: LLM API 配置

```yaml
provider: OpenAI 兼容接口
base_url: https://yunwu.ai/v1
endpoint: https://yunwu.ai/v1/chat/completions
api_key: your_api_key_here
```

### Q2: better/same/worse 判断标准

| 判定 | 叶片 Mask 增长 | 病害/萎蔫 | 说明 |
|------|----------------|-----------|------|
| **better** | 明显增长（高于平均速率） | 无 | 健康快速生长 |
| **same** | 平均增长（接近平均速率） | 无，可接受轻微萎蔫 | 正常生长 |
| **worse** | 低于平均速率（明显低） | 有明显病害或萎蔫即判 worse | 生长受阻或异常 |

**关键逻辑：**
- 有明显病害/萎蔫 → 直接判 worse（不论增长率）
- 无异常时，按 mask 增长率对比全生育期平均来判定

### Q3: 图像内容

- **拍摄对象**：监控摄像头拍摄的多株黄瓜（非单株）
- **视角**：固定机位，每日同一角度
- **评估方式**：整体长势评估，不针对单株

### Q4: Override 交互方式

- **最终形式**：前端 Web 用户界面输入
- **当前阶段**：先用 JSON 文件 + 命令行方式过渡

### Q5: 异常预警条件

| 预警类型 | 触发条件 | 说明 |
|----------|----------|------|
| 持续阴暗 | 连续 ≥3 天，日间（8:00-17:00）光照偏低 | 阴天无晴天 |
| 持续高湿 | 连续 ≥3 天，空气湿度 ≥80% | 易发病害 |
| 萎蔫 | 图像中观察到叶片下垂、边缘卷曲 | 需人工确认 |
| 黄化 | 图像中观察到叶片黄化、叶脉间失绿 | 需人工确认 |
| 其他 | 随使用过程人工输入并入库 | 经验积累 |

**预警机制说明**：
- 初期预警条件有限，后续通过人工 Override + 理由入库逐步扩展
- 预警条件会被纳入 WeeklySummaryBlock，动态注入 Prompt

---

## 7. 下一步行动

### 7.1 立即开始（Phase 0）

1. **P0.1** 构建日期配对索引
2. **P0.2** 设计 PlantResponse Prompt 模板
3. **P0.2** 批量调用 GPT-5.2 生成长势评估
4. **P0.3** 你人工审核，标注 ground_truth

### 7.2 待 Phase 0 完成后

- Phase 1: SanityCheck 实现
- Phase 2: Episode 入库 + Override 机制
- Phase 3: Weekly Summary + 动态 Prompt
- Phase 4: RAG 检索 + 评分

---

## 附录：术语表

| 术语 | 定义 |
|------|------|
| PlantResponse | GPT-5.2 输出的植物长势评估结构（trend + evidence + abnormalities） |
| SanityCheck | GPT-5.2 对 TSMixer 预测的合理性复核（accept + risk_level + questions） |
| Episode | 单日完整决策记录（输入→输出→结果→反馈） |
| WeeklySummaryBlock | 每周生成的总结块，包含规律、风险、建议，用于动态注入 Prompt |
| Override | 人工否决系统预测，输入替代灌水量与理由 |
| 波动 Prompt | 每周更新的 Prompt 上下文块，反映近期规律 |
