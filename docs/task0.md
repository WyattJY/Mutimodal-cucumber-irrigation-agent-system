# Phase 0 任务文档 - PlantResponse 生成与调优

> 版本：v1.0
> 更新日期：2024-12-25
> 对应设计：design0.md v1.0

---

## 1. 任务总览

### 1.1 Phase 0 目标

```
用历史数据批量生成长势评估 PlantResponse，人工审核后迭代优化 Prompt
```

### 1.2 数据现状

| 数据项 | 数量 | 说明 |
|--------|------|------|
| 图片总数 | 85 张 | 0314-0614，部分日期缺失 |
| CSV 行数 | 93 行 | 含 YOLO 指标 + 环境数据 |
| 可构建配对 | ~77 对 | 需连续两天都有图片 |

**缺失图片日期**：0421, 0428, 0531, 0602, 0606, 0610, 0611

**配对规则**：以图片日期为准，若某天无图片则跳过

### 1.3 任务依赖图

```
T1.1 项目初始化
  │
  ├──▶ T1.2 配置文件
  │
  └──▶ T2.1 数据模型
         │
         ├──▶ T2.2 图像服务
         │
         ├──▶ T2.3 配对构建器
         │      │
         │      └──▶ T3.1 构建配对索引（脚本）
         │             │
         ├──▶ T2.4 统计计算器
         │      │
         │      └──▶ T3.2 计算增长率统计（脚本）
         │
         ├──▶ T2.5 Prompt 构建器
         │      │
         │      └──▶ T3.3 设计 Prompt 模板
         │
         └──▶ T2.6 LLM 服务
                │
                └──▶ T3.4 批量生成（脚本）
                       │
                       └──▶ T4.1 人工审核标注
                              │
                              └──▶ T4.2 一致率评估（脚本）
                                     │
                                     └──▶ T4.3 Few-shot 优化
                                            │
                                            └──▶ T4.4 回归测试
```

---

## 2. 阶段一：项目搭建 (T1.x)

### T1.1 项目初始化

**目标**：使用 uv 初始化项目结构

**前置条件**：无

**具体步骤**：

```bash
# 1. 进入项目目录
cd G:\Wyatt\cucumber-irrigation

# 2. 初始化 uv 项目（如果 pyproject.toml 不存在）
uv init

# 3. 设置 Python 版本
uv python pin 3.11

# 4. 创建目录结构
mkdir -p src/cucumber_irrigation/{models,services,processors,utils}
mkdir -p scripts
mkdir -p outputs/plant_responses
mkdir -p annotations
mkdir -p reports
mkdir -p logs

# 5. 创建 __init__.py 文件
touch src/cucumber_irrigation/__init__.py
touch src/cucumber_irrigation/models/__init__.py
touch src/cucumber_irrigation/services/__init__.py
touch src/cucumber_irrigation/processors/__init__.py
touch src/cucumber_irrigation/utils/__init__.py
```

**交付物**：
- [ ] `pyproject.toml` 存在
- [ ] 目录结构完整
- [ ] `__init__.py` 文件存在

**验收标准**：
- [ ] `uv sync` 可正常执行

---

### T1.2 配置文件

**目标**：创建配置文件和环境变量

**前置条件**：T1.1

**具体步骤**：

1. 创建 `pyproject.toml`（依赖配置）
2. 创建 `configs/settings.yaml`（全局配置）
3. 创建 `.env`（API Key）
4. 创建 `.gitignore`
5. 创建 `configs/schema/plant_response.schema.json`

**交付物**：
- [ ] `pyproject.toml`
- [ ] `configs/settings.yaml`
- [ ] `.env`（含 API Key）
- [ ] `.gitignore`
- [ ] `configs/schema/plant_response.schema.json`

**验收标准**：
- [ ] `uv sync` 安装依赖成功
- [ ] 配置文件可正常加载

---

## 3. 阶段二：核心模块开发 (T2.x)

### T2.1 数据模型

**目标**：实现 PlantResponse 数据模型

**前置条件**：T1.2

**文件**：`src/cucumber_irrigation/models/plant_response.py`

**实现内容**：

```python
# 需要实现的类和方法
class Trend(str, Enum): ...
class GrowthStage(str, Enum): ...

@dataclass
class Comparison:
    trend: Trend
    confidence: float
    evidence: str

@dataclass
class Abnormalities:
    wilting: Optional[bool]
    yellowing: Optional[bool]
    pest_damage: Optional[bool]
    other: Optional[str]

@dataclass
class PlantResponse:
    date: str
    comparison: Comparison
    abnormalities: Abnormalities
    growth_stage: GrowthStage
    key_observations: List[str]

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "PlantResponse": ...
    @classmethod
    def from_llm_response(cls, response: str) -> "PlantResponse": ...
```

**交付物**：
- [ ] `src/cucumber_irrigation/models/plant_response.py`
- [ ] `src/cucumber_irrigation/models/__init__.py`（导出）

**验收标准**：
- [ ] 可正常实例化 PlantResponse
- [ ] `to_dict()` / `from_dict()` 互转正确
- [ ] 符合 JSON Schema 验证

---

### T2.2 图像服务

**目标**：实现图像 Base64 编码服务

**前置条件**：T1.2

**文件**：`src/cucumber_irrigation/services/image_service.py`

**实现内容**：

```python
class ImageService:
    @staticmethod
    def encode_image(image_path: str) -> str:
        """图像转 Base64"""
        ...

    @staticmethod
    def get_image_url(b64_data: str, mime_type: str = "image/jpeg") -> str:
        """生成 data URL"""
        ...
```

**交付物**：
- [ ] `src/cucumber_irrigation/services/image_service.py`

**验收标准**：
- [ ] 能正确编码 JPG 图像
- [ ] 编码结果可用于 LLM API

---

### T2.3 配对构建器

**目标**：实现日期配对逻辑（以图片为准）

**前置条件**：T1.2

**文件**：`src/cucumber_irrigation/processors/pairs_builder.py`

**实现内容**：

```python
@dataclass
class DayPair:
    date: str                    # 今日日期 YYYY-MM-DD
    image_today: str             # 今日图像路径
    image_yesterday: str         # 昨日图像路径
    yolo_today: dict             # 今日 YOLO 指标（可能为 None）
    yolo_yesterday: dict         # 昨日 YOLO 指标（可能为 None）
    env_today: dict              # 今日环境数据（可能为 None）


class PairsBuilder:
    def __init__(self, images_dir: str, csv_path: str): ...
    def _scan_images(self) -> List[str]:
        """扫描图片目录，获取所有图片日期"""
        ...
    def _load_csv(self) -> pd.DataFrame:
        """加载 CSV，建立日期索引"""
        ...
    def _parse_image_date(self, filename: str) -> str:
        """解析图片文件名为日期 YYYY-MM-DD"""
        # 0315.JPG -> 2024-03-15
        ...
    def build_pairs(self) -> List[DayPair]:
        """
        构建配对（以图片为准）
        规则：
        1. 扫描所有图片，获取日期列表
        2. 对于每个日期，检查前一天是否也有图片
        3. 如果有，构建配对
        4. 从 CSV 中查找对应日期的 YOLO/环境数据（可能缺失）
        """
        ...
    def save_pairs_index(self, output_path: str): ...
```

**关键逻辑**：

```
图片日期列表: [0314, 0315, 0316, ..., 0420, 0422, ...]
                                        ↑
                                    0421 缺失

配对构建:
- 0315: today=0315, yesterday=0314 ✓
- 0316: today=0316, yesterday=0315 ✓
- ...
- 0421: 无图片，跳过
- 0422: today=0422, yesterday=0420 ✗ (不连续，跳过)
- 0423: today=0423, yesterday=0422 ✓
```

**交付物**：
- [ ] `src/cucumber_irrigation/processors/pairs_builder.py`

**验收标准**：
- [ ] 正确扫描图片目录
- [ ] 正确处理日期缺失情况
- [ ] 生成的配对索引格式正确

---

### T2.4 统计计算器

**目标**：计算全生育期增长率统计

**前置条件**：T1.2

**文件**：`src/cucumber_irrigation/processors/stats_calculator.py`

**实现内容**：

```python
@dataclass
class GrowthStats:
    all_leaf_mask_start: float       # 起始值
    all_leaf_mask_end: float         # 结束值
    all_leaf_mask_daily_avg: float   # 日均增长
    all_leaf_mask_daily_std: float   # 日增长标准差
    date_start: str
    date_end: str
    total_days: int

    def to_dict(self) -> dict: ...


class StatsCalculator:
    def __init__(self, csv_path: str): ...
    def calc_growth_stats(self) -> GrowthStats:
        """
        计算全生育期增长率统计
        - 使用 all leaf mask 列
        - 计算日增长 = diff()
        - 计算均值和标准差
        """
        ...
    def save_stats(self, output_path: str): ...
```

**交付物**：
- [ ] `src/cucumber_irrigation/processors/stats_calculator.py`

**验收标准**：
- [ ] 计算结果符合预期
- [ ] 输出 JSON 格式正确

---

### T2.5 Prompt 构建器

**目标**：实现 Prompt 加载和构建

**前置条件**：T1.2

**文件**：`src/cucumber_irrigation/utils/prompt_builder.py`

**实现内容**：

```python
class PromptBuilder:
    def __init__(self, prompts_dir: str = "prompts/plant_response"): ...

    def load_system_prompt(self, version: str = "v1") -> str:
        """加载 System Prompt"""
        ...

    def load_user_template(self, version: str = "v1") -> str:
        """加载 User Prompt 模板"""
        ...

    def load_examples(self, version: str = "v1") -> List[dict]:
        """加载 Few-shot 示例"""
        ...

    def build_user_prompt(
        self,
        template: str,
        date: str,
        yolo_today: dict,
        yolo_yesterday: dict,
        env_today: dict,
        growth_stats: dict
    ) -> str:
        """构建完整的 User Prompt"""
        ...
```

**交付物**：
- [ ] `src/cucumber_irrigation/utils/prompt_builder.py`
- [ ] `prompts/plant_response/system_v1.md`
- [ ] `prompts/plant_response/user_v1.md`
- [ ] `prompts/plant_response/examples_v1.jsonl`（初始为空或少量示例）

**验收标准**：
- [ ] 能正确加载 Prompt 文件
- [ ] 模板填充正确

---

### T2.6 LLM 服务

**目标**：实现 LLM API 调用

**前置条件**：T2.2, T2.5

**文件**：`src/cucumber_irrigation/services/llm_service.py`

**实现内容**：

```python
class LLMService:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://yunwu.ai/v1",
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ): ...

    def generate_plant_response(
        self,
        system_prompt: str,
        user_prompt: str,
        image_today_b64: str,
        image_yesterday_b64: str,
        examples: Optional[List[dict]] = None
    ) -> str:
        """
        调用 LLM 生成 PlantResponse

        消息结构：
        1. system: System Prompt
        2. [可选] few-shot examples
        3. user: User Prompt + 两张图像
        """
        ...

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        image_today_b64: str,
        image_yesterday_b64: str,
        examples: Optional[List[dict]] = None
    ) -> List[dict]:
        """构建 messages 列表"""
        ...
```

**交付物**：
- [ ] `src/cucumber_irrigation/services/llm_service.py`

**验收标准**：
- [ ] 能成功调用 yunwu.ai API
- [ ] 返回有效的 JSON 字符串
- [ ] 支持多模态（图像）输入

---

### T2.7 配置加载模块

**目标**：实现统一的配置加载

**前置条件**：T1.2

**文件**：`src/cucumber_irrigation/config.py`

**实现内容**：

```python
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


def load_settings(config_path: str = "configs/settings.yaml") -> dict:
    """加载 YAML 配置"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_api_key() -> str:
    """从环境变量加载 API Key"""
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY not found in environment")
    return api_key
```

**交付物**：
- [ ] `src/cucumber_irrigation/config.py`

**验收标准**：
- [ ] 能正确加载 settings.yaml
- [ ] 能正确加载 .env 中的 API Key

---

## 4. 阶段三：脚本开发 (T3.x)

### T3.1 构建配对索引脚本

**目标**：扫描图片，构建配对索引

**前置条件**：T2.3

**文件**：`scripts/build_pairs.py`

**输入**：
- `data/images/*.jpg`
- `data/csv/irrigation.csv`

**输出**：
- `outputs/pairs_index.json`

**命令**：
```bash
uv run python scripts/build_pairs.py
```

**输出格式**：

```json
{
  "created_at": "2024-12-25T10:00:00",
  "images_dir": "data/images",
  "csv_path": "data/csv/irrigation.csv",
  "total_images": 85,
  "total_pairs": 77,
  "missing_dates": ["2024-04-21", "2024-04-28", ...],
  "skipped_pairs": [
    {"date": "2024-04-22", "reason": "前一天无图片"}
  ],
  "pairs": [
    {
      "date": "2024-03-15",
      "image_today": "data/images/0315.JPG",
      "image_yesterday": "data/images/0314.JPG",
      "yolo_today": {...},
      "yolo_yesterday": {...},
      "env_today": {...},
      "csv_matched": true
    }
  ]
}
```

**交付物**：
- [ ] `scripts/build_pairs.py`
- [ ] `outputs/pairs_index.json`

**验收标准**：
- [ ] 正确识别缺失日期
- [ ] 正确跳过不连续配对
- [ ] 配对数量合理（约 77 对）

---

### T3.2 计算增长率统计脚本

**目标**：计算全生育期增长率统计

**前置条件**：T2.4

**文件**：`scripts/calc_growth_stats.py`

**输入**：
- `data/csv/irrigation.csv`

**输出**：
- `outputs/growth_stats.json`

**命令**：
```bash
uv run python scripts/calc_growth_stats.py
```

**输出格式**：

```json
{
  "created_at": "2024-12-25T10:00:00",
  "all_leaf_mask": {
    "start_value": 19537,
    "end_value": 469720.5,
    "total_growth": 450183.5,
    "daily_avg": 4903.08,
    "daily_std": 8234.56,
    "growth_rate_percent": 2303.9
  },
  "date_range": {
    "start": "2024-03-14",
    "end": "2024-06-14",
    "total_days": 93
  },
  "thresholds": {
    "better": 9120.36,
    "worse": 685.80,
    "description": "better: > avg + 0.5*std, worse: < avg - 0.5*std"
  }
}
```

**交付物**：
- [ ] `scripts/calc_growth_stats.py`
- [ ] `outputs/growth_stats.json`

**验收标准**：
- [ ] 统计值计算正确
- [ ] 阈值计算正确

---

### T3.3 设计 Prompt 模板

**目标**：编写 PlantResponse 的 Prompt 模板

**前置条件**：T2.5

**文件**：
- `prompts/plant_response/system_v1.md`
- `prompts/plant_response/user_v1.md`
- `prompts/plant_response/examples_v1.jsonl`

**System Prompt 要点**：
1. 角色定义：温室作物长势评估专家
2. 任务说明：对比多株黄瓜的昨日与今日图像
3. 输出格式：严格 JSON
4. trend 判定规则：
   - 优先级1：异常检测（萎蔫/黄化/病害 → worse）
   - 优先级2：增长率对比（用全生育期平均作为基准）
5. 注意事项：多株评估、光照差异、中文输出

**User Prompt 模板**：
```markdown
请对比以下两张监控图像（昨日 vs 今日），评估黄瓜整体长势变化。

## 日期
{date}

## 昨日 YOLO 指标
{yolo_yesterday}

## 今日 YOLO 指标
{yolo_today}

## 今日环境数据
{env_today}

## 全生育期增长率参考
{growth_stats}

请根据图像和数据，输出 JSON 格式的长势评估报告。
```

**交付物**：
- [ ] `prompts/plant_response/system_v1.md`
- [ ] `prompts/plant_response/user_v1.md`
- [ ] `prompts/plant_response/examples_v1.jsonl`

**验收标准**：
- [ ] Prompt 逻辑清晰
- [ ] 判定规则明确
- [ ] 模板变量正确

---

### T3.4 批量生成脚本

**目标**：批量调用 LLM 生成 PlantResponse

**前置条件**：T2.6, T3.1, T3.2, T3.3

**文件**：`scripts/generate_responses.py`

**输入**：
- `outputs/pairs_index.json`
- `outputs/growth_stats.json`
- `prompts/plant_response/*`

**输出**：
- `outputs/plant_responses/{date}.json`

**命令**：
```bash
# 全量生成
uv run python scripts/generate_responses.py

# 指定范围
uv run python scripts/generate_responses.py --start 0 --end 10

# 跳过已存在
uv run python scripts/generate_responses.py --skip-existing
```

**功能要求**：
1. 读取配对索引
2. 逐个处理配对
3. 编码图像为 Base64
4. 构建 Prompt
5. 调用 LLM
6. 解析并保存结果
7. 错误处理与重试
8. 进度显示

**交付物**：
- [ ] `scripts/generate_responses.py`
- [ ] `outputs/plant_responses/*.json`（≥60 个）

**验收标准**：
- [ ] 成功率 ≥ 80%
- [ ] JSON 格式正确
- [ ] 有进度显示和日志

---

## 5. 阶段四：评估与优化 (T4.x)

### T4.1 人工审核标注

**目标**：人工审核生成结果，标注 ground truth

**前置条件**：T3.4 完成（生成足够多的 PlantResponse）

**输入**：
- `outputs/plant_responses/*.json`
- `data/images/*.jpg`

**输出**：
- `annotations/ground_truth.jsonl`

**标注格式**：

```jsonl
{"date": "2024-03-15", "human_trend": "better", "human_confidence": 0.9, "agree_with_llm": true, "notes": ""}
{"date": "2024-03-16", "human_trend": "same", "human_confidence": 0.7, "agree_with_llm": false, "notes": "LLM判定better，但实际增长不明显"}
```

**标注流程**：

1. 打开 `outputs/plant_responses/{date}.json`
2. 查看对应的两张图片
3. 判断 trend（better/same/worse）
4. 记录是否同意 LLM 判断
5. 如不同意，记录原因

**标注数量目标**：
- 第一轮：至少 30 对
- 覆盖：better/same/worse 各至少 10 个

**交付物**：
- [ ] `annotations/ground_truth.jsonl`（≥30 条）

**验收标准**：
- [ ] 格式正确
- [ ] 三类 trend 均有覆盖

---

### T4.2 一致率评估脚本

**目标**：计算 LLM 输出与人工标注的一致率

**前置条件**：T4.1

**文件**：`scripts/eval_consistency.py`

**输入**：
- `outputs/plant_responses/*.json`
- `annotations/ground_truth.jsonl`

**输出**：
- `reports/consistency_report.md`

**命令**：
```bash
uv run python scripts/eval_consistency.py
```

**报告内容**：

```markdown
# 一致率评估报告

## 总体指标
| 指标 | 值 |
|------|-----|
| 总样本数 | 30 |
| 正确数 | 24 |
| 一致率 | 80.0% |

## 分类统计
| 类别 | 样本数 | 正确数 | 正确率 |
|------|--------|--------|--------|
| better | 10 | 8 | 80% |
| same | 12 | 10 | 83% |
| worse | 8 | 6 | 75% |

## 混淆矩阵
|  | 实际 better | 实际 same | 实际 worse |
|--|-------------|-----------|------------|
| 预测 better | 8 | 1 | 0 |
| 预测 same | 1 | 10 | 1 |
| 预测 worse | 1 | 1 | 6 |

## 典型错误案例
1. **2024-03-20**: 预测 better，实际 same
   - 原因：...

## 结论
✅/❌ 一致率达标/未达标
```

**交付物**：
- [ ] `scripts/eval_consistency.py`
- [ ] `reports/consistency_report.md`

**验收标准**：
- [ ] 报告格式正确
- [ ] 包含错误分析

---

### T4.3 Few-shot 优化

**目标**：根据错误案例优化 Prompt

**前置条件**：T4.2（一致率未达标时执行）

**输入**：
- `reports/consistency_report.md`（错误案例）
- `annotations/ground_truth.jsonl`

**输出**：
- `prompts/plant_response/examples_v2.jsonl`
- `prompts/plant_response/system_v2.md`（如需修改）

**优化策略**：

1. **分析错误模式**
   - better 误判为 same：可能是阈值偏高
   - worse 误判为 same：可能是异常检测不敏感
   - same 误判为 better：可能是增长率基准偏低

2. **添加 Few-shot 示例**
   - 选择典型错例
   - 补充正确答案作为示例
   - 每类 trend 至少 2 个示例

3. **调整 Prompt**
   - 细化判定规则
   - 增加边界情况说明

**交付物**：
- [ ] `prompts/plant_response/examples_v2.jsonl`
- [ ] 优化后的 Prompt（如需）

**验收标准**：
- [ ] 新增 ≥6 个 few-shot 示例
- [ ] 覆盖主要错误类型

---

### T4.4 回归测试

**目标**：使用优化后的 Prompt 重新生成并评估

**前置条件**：T4.3

**步骤**：

```bash
# 1. 使用 v2 Prompt 重新生成
uv run python scripts/generate_responses.py \
    --prompt-version v2 \
    --output-dir outputs/plant_responses_v2

# 2. 评估一致率
uv run python scripts/eval_consistency.py \
    --predictions-dir outputs/plant_responses_v2 \
    --output reports/consistency_report_v2.md
```

**交付物**：
- [ ] `outputs/plant_responses_v2/*.json`
- [ ] `reports/consistency_report_v2.md`

**验收标准**：
- [ ] 一致率 ≥ 80%
- [ ] 相比 v1 有明显提升

---

## 6. 任务检查清单

### 阶段一：项目搭建 ✓

| 任务 | 状态 | 交付物 |
|------|------|--------|
| T1.1 项目初始化 | ⬜ | 目录结构 |
| T1.2 配置文件 | ⬜ | pyproject.toml, settings.yaml, .env |

### 阶段二：核心模块 ✓

| 任务 | 状态 | 交付物 |
|------|------|--------|
| T2.1 数据模型 | ⬜ | models/plant_response.py |
| T2.2 图像服务 | ⬜ | services/image_service.py |
| T2.3 配对构建器 | ⬜ | processors/pairs_builder.py |
| T2.4 统计计算器 | ⬜ | processors/stats_calculator.py |
| T2.5 Prompt 构建器 | ⬜ | utils/prompt_builder.py |
| T2.6 LLM 服务 | ⬜ | services/llm_service.py |
| T2.7 配置加载 | ⬜ | config.py |

### 阶段三：脚本开发 ✓

| 任务 | 状态 | 交付物 |
|------|------|--------|
| T3.1 构建配对索引 | ⬜ | scripts/build_pairs.py |
| T3.2 计算增长率统计 | ⬜ | scripts/calc_growth_stats.py |
| T3.3 设计 Prompt | ⬜ | prompts/plant_response/* |
| T3.4 批量生成 | ⬜ | scripts/generate_responses.py |

### 阶段四：评估优化 ✓

| 任务 | 状态 | 交付物 |
|------|------|--------|
| T4.1 人工审核 | ⬜ | annotations/ground_truth.jsonl |
| T4.2 一致率评估 | ⬜ | scripts/eval_consistency.py |
| T4.3 Few-shot 优化 | ⬜ | prompts/*_v2.* |
| T4.4 回归测试 | ⬜ | reports/consistency_report_v2.md |

---

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| API 调用失败/限流 | 中 | 中 | 重试机制 + 延时 + 断点续传 |
| 图片-CSV 日期不匹配 | 高 | 低 | 以图片为准，缺失数据填 null |
| LLM 输出格式不合规 | 中 | 中 | JSON Schema 验证 + 降级处理 |
| 一致率不达标 | 中 | 高 | 多轮迭代优化 Prompt |
| API 费用超预算 | 低 | 中 | 限制批量大小，优先测试小样本 |

---

## 8. 快速命令参考

```bash
# 环境设置
cd G:\Wyatt\cucumber-irrigation
uv sync

# 阶段三：数据处理
uv run python scripts/build_pairs.py
uv run python scripts/calc_growth_stats.py

# 阶段三：生成（先测试 10 个）
uv run python scripts/generate_responses.py --end 10

# 阶段三：全量生成
uv run python scripts/generate_responses.py

# 阶段四：评估
uv run python scripts/eval_consistency.py

# 查看日志
cat logs/phase0_*.log
```

---

## 9. 附录：数据缺失情况

### 9.1 图片缺失日期（共 7 天）

| 月份 | 缺失日期 |
|------|----------|
| 4月 | 21日, 28日 |
| 5月 | 31日 |
| 6月 | 2日, 6日, 10日, 11日 |

### 9.2 配对影响

| 日期 | 影响 |
|------|------|
| 0421 缺失 | 0422 无法配对（前一天无图） |
| 0428 缺失 | 0429 无法配对 |
| 0531 缺失 | 0601 无法配对 |
| 0602 缺失 | 0603 无法配对 |
| 0606 缺失 | 0607 无法配对 |
| 0610 缺失 | 无后续影响（0611也缺失） |
| 0611 缺失 | 0612 无法配对 |

**预计可用配对数**：85 - 1 - 7 = 77 对
