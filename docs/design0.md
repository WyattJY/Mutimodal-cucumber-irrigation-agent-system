# Phase 0 设计文档 - PlantResponse 生成与调优

> 版本：v1.0
> 更新日期：2024-12-25
> 对应需求：requirements.md v1.2 Phase 0

---

## 1. 核心目标

### 1.1 Phase 0 目标

```
用历史数据（85张图像 + CSV）批量生成长势评估 PlantResponse，
通过人工审核迭代优化 Prompt，达到 trend 判定一致率 > 80%
```

### 1.2 成功标准

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 生成成功率 | ≥ 80% | 84 对配对中至少 67 对成功生成 JSON |
| JSON 格式合规 | 100% | 所有输出符合 PlantResponse Schema |
| trend 一致率 | ≥ 80% | 与人工标注对比 |
| 批量处理时间 | < 30 分钟 | 84 对全量处理 |

### 1.3 不在 Phase 0 范围

- ❌ SanityCheck（灌水量复核）
- ❌ Episode 入库（MongoDB）
- ❌ Weekly Summary（周度总结）
- ❌ RAG 检索

---

## 2. 系统架构

### 2.1 Phase 0 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Phase 0: PlantResponse 生成系统                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           输入层 (Input Layer)                       │   │
│  │                                                                     │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │   │
│  │   │   Images    │    │    CSV      │    │   Growth Stats      │    │   │
│  │   │  (85 张)    │    │ (93 行)     │    │   (计算得出)         │    │   │
│  │   │             │    │             │    │                     │    │   │
│  │   │ data/images │    │ irrigation  │    │ 全生育期平均增长率   │    │   │
│  │   └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘    │   │
│  │          │                  │                      │               │   │
│  └──────────┼──────────────────┼──────────────────────┼───────────────┘   │
│             │                  │                      │                   │
│             ▼                  ▼                      ▼                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        预处理层 (Preprocessing)                      │   │
│  │                                                                     │   │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐  │   │
│  │   │  build_pairs    │    │  stats_calc     │    │  image_encode │  │   │
│  │   │                 │    │                 │    │               │  │   │
│  │   │ 构建日期配对     │    │ 计算增长率统计  │    │ Base64 编码   │  │   │
│  │   │ pairs_index.json│    │ growth_stats    │    │               │  │   │
│  │   └────────┬────────┘    └────────┬────────┘    └───────┬───────┘  │   │
│  │            │                      │                     │          │   │
│  └────────────┼──────────────────────┼─────────────────────┼──────────┘   │
│               │                      │                     │              │
│               ▼                      ▼                     ▼              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         核心层 (Core Layer)                          │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │                    LLM Service                              │  │   │
│  │   │                                                             │  │   │
│  │   │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │  │   │
│  │   │  │   Prompt    │   │   OpenAI    │   │    Response     │   │  │   │
│  │   │  │   Builder   │──▶│   Client    │──▶│    Parser       │   │  │   │
│  │   │  │             │   │ (yunwu.ai)  │   │                 │   │  │   │
│  │   │  └─────────────┘   └─────────────┘   └─────────────────┘   │  │   │
│  │   │                                                             │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                          │                                 │
│                                          ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         输出层 (Output Layer)                        │   │
│  │                                                                     │   │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐  │   │
│  │   │ PlantResponse   │    │  ground_truth   │    │  consistency  │  │   │
│  │   │ JSON 文件       │    │  人工标注        │    │  评估报告     │  │   │
│  │   │                 │    │                 │    │               │  │   │
│  │   │ outputs/*.json  │    │ annotations/    │    │ reports/      │  │   │
│  │   └─────────────────┘    └─────────────────┘    └───────────────┘  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  images  │────▶│  pairs   │────▶│  prompt  │────▶│   LLM    │────▶│  output  │
│  + csv   │     │  index   │     │  build   │     │  call    │     │  parse   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │                │
     ▼                ▼                ▼                ▼                ▼
 85 images      84 pairs         system +         API call        PlantResponse
 93 csv rows    (today,          user prompt      with images     JSON × 84
                 yesterday)      + context
```

---

## 3. 目录结构

```
cucumber-irrigation/
├── pyproject.toml                 # uv 项目配置
├── uv.lock                        # uv 锁文件
├── .python-version                # Python 版本
├── .env                           # 环境变量（API Key）
│
├── configs/                       # 配置文件
│   ├── settings.yaml              # 全局配置
│   └── schema/                    # JSON Schema
│       └── plant_response.schema.json
│
├── data/                          # 数据（已有）
│   ├── images/                    # 原始图像
│   │   └── *.jpg
│   └── csv/
│       └── irrigation.csv
│
├── prompts/                       # Prompt 模板
│   └── plant_response/
│       ├── system_v1.md           # System Prompt
│       ├── user_v1.md             # User Prompt 模板
│       └── examples_v1.jsonl      # Few-shot 示例
│
├── src/                           # 源代码
│   └── cucumber_irrigation/       # 主包
│       ├── __init__.py
│       ├── config.py              # 配置加载
│       ├── models/                # 数据模型
│       │   ├── __init__.py
│       │   └── plant_response.py  # PlantResponse 模型
│       ├── services/              # 服务层
│       │   ├── __init__.py
│       │   ├── llm_service.py     # LLM 调用服务
│       │   └── image_service.py   # 图像处理服务
│       ├── processors/            # 数据处理
│       │   ├── __init__.py
│       │   ├── pairs_builder.py   # 构建配对
│       │   └── stats_calculator.py # 统计计算
│       └── utils/                 # 工具函数
│           ├── __init__.py
│           └── prompt_builder.py  # Prompt 构建
│
├── scripts/                       # 独立脚本
│   ├── build_pairs.py             # P0.1: 构建配对索引
│   ├── calc_growth_stats.py       # 计算增长率统计
│   ├── generate_responses.py      # P0.2: 批量生成
│   └── eval_consistency.py        # P0.4: 一致率评估
│
├── outputs/                       # 输出目录
│   ├── pairs_index.json           # 配对索引
│   ├── growth_stats.json          # 增长率统计
│   └── plant_responses/           # 生成的 PlantResponse
│       └── {date}.json
│
├── annotations/                   # 人工标注
│   └── ground_truth.jsonl         # 人工标注结果
│
├── reports/                       # 评估报告
│   └── consistency_report.md      # 一致率报告
│
├── docs/                          # 文档
│   ├── requirements.md
│   ├── design0.md                 # 本文档
│   └── task0.md                   # 任务文档
│
└── tests/                         # 测试
    ├── __init__.py
    ├── test_llm_service.py
    └── test_pairs_builder.py
```

---

## 4. 模块设计

### 4.1 模块划分

```
┌─────────────────────────────────────────────────────────────────┐
│                         模块依赖关系                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      ┌─────────────────┐                        │
│                      │     scripts     │                        │
│                      │  (入口脚本)      │                        │
│                      └────────┬────────┘                        │
│                               │                                 │
│              ┌────────────────┼────────────────┐                │
│              ▼                ▼                ▼                │
│     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│     │ processors  │   │  services   │   │   utils     │        │
│     │             │   │             │   │             │        │
│     │ pairs_builder│  │ llm_service │   │prompt_builder│       │
│     │ stats_calc  │   │ image_service│  │             │        │
│     └──────┬──────┘   └──────┬──────┘   └──────┬──────┘        │
│            │                 │                 │                │
│            └────────────────┬┴─────────────────┘                │
│                             ▼                                   │
│                      ┌─────────────┐                            │
│                      │   models    │                            │
│                      │             │                            │
│                      │ PlantResponse│                           │
│                      └──────┬──────┘                            │
│                             │                                   │
│                             ▼                                   │
│                      ┌─────────────┐                            │
│                      │   config    │                            │
│                      │             │                            │
│                      │ settings    │                            │
│                      └─────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 核心模块说明

#### 4.2.1 models/plant_response.py

```python
"""PlantResponse 数据模型"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from enum import Enum


class Trend(str, Enum):
    BETTER = "better"
    SAME = "same"
    WORSE = "worse"


class GrowthStage(str, Enum):
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MIXED = "mixed"


@dataclass
class Comparison:
    trend: Trend
    confidence: float
    evidence: str


@dataclass
class Abnormalities:
    wilting: Optional[bool] = None
    yellowing: Optional[bool] = None
    pest_damage: Optional[bool] = None
    other: Optional[str] = None


@dataclass
class PlantResponse:
    date: str
    comparison: Comparison
    abnormalities: Abnormalities
    growth_stage: GrowthStage
    key_observations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        ...

    @classmethod
    def from_dict(cls, data: dict) -> "PlantResponse":
        """从字典创建"""
        ...

    @classmethod
    def from_llm_response(cls, response: str) -> "PlantResponse":
        """从 LLM 响应解析"""
        ...
```

#### 4.2.2 services/llm_service.py

```python
"""LLM 调用服务"""

from openai import OpenAI
from typing import Optional
import base64


class LLMService:
    """OpenAI 兼容 API 调用服务"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://yunwu.ai/v1",
        model: str = "gpt-4o",
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
        examples: Optional[list] = None
    ) -> str:
        """
        生成 PlantResponse

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词（含 YOLO 指标）
            image_today_b64: 今日图像 Base64
            image_yesterday_b64: 昨日图像 Base64
            examples: Few-shot 示例

        Returns:
            LLM 响应的 JSON 字符串
        """
        messages = self._build_messages(
            system_prompt, user_prompt,
            image_today_b64, image_yesterday_b64,
            examples
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content

    def _build_messages(self, ...) -> list:
        """构建消息列表"""
        ...
```

#### 4.2.3 services/image_service.py

```python
"""图像处理服务"""

import base64
from pathlib import Path


class ImageService:
    """图像处理服务"""

    @staticmethod
    def encode_image(image_path: str) -> str:
        """图像转 Base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def get_image_url(b64_data: str, mime_type: str = "image/jpeg") -> str:
        """生成 data URL"""
        return f"data:{mime_type};base64,{b64_data}"
```

#### 4.2.4 processors/pairs_builder.py

```python
"""构建日期配对"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import pandas as pd


@dataclass
class DayPair:
    """日期配对"""
    date: str                    # 今日日期 YYYY-MM-DD
    image_today: str             # 今日图像路径
    image_yesterday: str         # 昨日图像路径
    yolo_today: dict             # 今日 YOLO 指标
    yolo_yesterday: dict         # 昨日 YOLO 指标
    env_today: dict              # 今日环境数据


class PairsBuilder:
    """配对构建器"""

    def __init__(
        self,
        images_dir: str,
        csv_path: str
    ):
        self.images_dir = Path(images_dir)
        self.csv_path = csv_path
        self.df = self._load_csv()

    def _load_csv(self) -> pd.DataFrame:
        """加载 CSV"""
        ...

    def build_pairs(self) -> List[DayPair]:
        """构建所有配对"""
        ...

    def save_pairs_index(self, output_path: str):
        """保存配对索引"""
        ...
```

#### 4.2.5 processors/stats_calculator.py

```python
"""增长率统计计算"""

from dataclasses import dataclass
import pandas as pd


@dataclass
class GrowthStats:
    """全生育期增长率统计"""
    all_leaf_mask_daily_avg: float    # 日均增长率
    all_leaf_mask_std: float          # 标准差
    date_range: tuple                  # (start, end)
    total_days: int                    # 总天数


class StatsCalculator:
    """统计计算器"""

    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path, sep='\t')

    def calc_growth_stats(self) -> GrowthStats:
        """计算全生育期增长率统计"""
        leaf_mask = self.df['all leaf mask']

        # 日增长率
        daily_growth = leaf_mask.diff()

        return GrowthStats(
            all_leaf_mask_daily_avg=daily_growth.mean(),
            all_leaf_mask_std=daily_growth.std(),
            date_range=(
                self.df['date'].iloc[0],
                self.df['date'].iloc[-1]
            ),
            total_days=len(self.df)
        )
```

#### 4.2.6 utils/prompt_builder.py

```python
"""Prompt 构建器"""

from pathlib import Path
from typing import Optional, List
import json


class PromptBuilder:
    """Prompt 构建器"""

    def __init__(self, prompts_dir: str = "prompts/plant_response"):
        self.prompts_dir = Path(prompts_dir)

    def load_system_prompt(self, version: str = "v1") -> str:
        """加载 System Prompt"""
        path = self.prompts_dir / f"system_{version}.md"
        return path.read_text(encoding="utf-8")

    def load_user_template(self, version: str = "v1") -> str:
        """加载 User Prompt 模板"""
        path = self.prompts_dir / f"user_{version}.md"
        return path.read_text(encoding="utf-8")

    def load_examples(self, version: str = "v1") -> List[dict]:
        """加载 Few-shot 示例"""
        path = self.prompts_dir / f"examples_{version}.jsonl"
        if not path.exists():
            return []
        examples = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))
        return examples

    def build_user_prompt(
        self,
        template: str,
        date: str,
        yolo_today: dict,
        yolo_yesterday: dict,
        env_today: dict,
        growth_stats: dict
    ) -> str:
        """构建 User Prompt"""
        return template.format(
            date=date,
            yolo_today=json.dumps(yolo_today, indent=2, ensure_ascii=False),
            yolo_yesterday=json.dumps(yolo_yesterday, indent=2, ensure_ascii=False),
            env_today=json.dumps(env_today, indent=2, ensure_ascii=False),
            growth_stats=json.dumps(growth_stats, indent=2, ensure_ascii=False)
        )
```

---

## 5. 组件详细设计

### 5.1 配置组件

#### 5.1.1 configs/settings.yaml

```yaml
# Phase 0 配置

# LLM 配置
llm:
  base_url: "https://yunwu.ai/v1"
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 2000
  timeout: 60

# 数据路径
data:
  images_dir: "data/images"
  csv_path: "data/csv/irrigation.csv"

# 输出路径
output:
  pairs_index: "outputs/pairs_index.json"
  growth_stats: "outputs/growth_stats.json"
  plant_responses_dir: "outputs/plant_responses"

# Prompt 配置
prompts:
  dir: "prompts/plant_response"
  version: "v1"

# 处理配置
processing:
  batch_size: 10          # 批次大小
  retry_times: 3          # 重试次数
  retry_delay: 2          # 重试延迟（秒）
```

#### 5.1.2 .env

```bash
# API 密钥（不提交到 Git）
LLM_API_KEY=your_api_key_here
```

#### 5.1.3 configs/schema/plant_response.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PlantResponse",
  "type": "object",
  "required": ["date", "comparison", "abnormalities", "growth_stage", "key_observations"],
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
    },
    "comparison": {
      "type": "object",
      "required": ["trend", "confidence", "evidence"],
      "properties": {
        "trend": {
          "type": "string",
          "enum": ["better", "same", "worse"]
        },
        "confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "evidence": {
          "type": "string"
        }
      }
    },
    "abnormalities": {
      "type": "object",
      "properties": {
        "wilting": { "type": ["boolean", "null"] },
        "yellowing": { "type": ["boolean", "null"] },
        "pest_damage": { "type": ["boolean", "null"] },
        "other": { "type": ["string", "null"] }
      }
    },
    "growth_stage": {
      "type": "string",
      "enum": ["vegetative", "flowering", "fruiting", "mixed"]
    },
    "key_observations": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

### 5.2 Prompt 组件

#### 5.2.1 prompts/plant_response/system_v1.md

```markdown
# 角色

你是一位专业的温室作物长势评估专家。你的任务是对比监控摄像头拍摄的多株黄瓜的昨日与今日图像，结合 YOLO 实例分割指标，输出结构化的长势评估报告。

# 任务

对比两张图像（昨日 vs 今日），评估黄瓜整体长势变化。

# 输出格式

你必须输出严格的 JSON 格式，包含以下字段：

```json
{
  "date": "YYYY-MM-DD",
  "comparison": {
    "trend": "better | same | worse",
    "confidence": 0.0-1.0,
    "evidence": "具体证据描述"
  },
  "abnormalities": {
    "wilting": true/false/null,
    "yellowing": true/false/null,
    "pest_damage": true/false/null,
    "other": "其他异常描述或null"
  },
  "growth_stage": "vegetative | flowering | fruiting | mixed",
  "key_observations": ["观察1", "观察2", "观察3"]
}
```

# trend 判定规则

**优先级1：异常检测**
- 如果观察到明显萎蔫（叶片下垂、边缘卷曲）→ trend = "worse"
- 如果观察到明显黄化（叶片黄化、叶脉间失绿）→ trend = "worse"
- 如果观察到明显病害（虫孔、斑点、粉状物）→ trend = "worse"

**优先级2：增长率对比**
- 无异常时，对比 all_leaf_mask 的日增长率与全生育期平均增长率
- 明显高于平均（增长率 > 平均 + 0.5×标准差）→ trend = "better"
- 接近平均（在 ±0.5×标准差范围内）→ trend = "same"
- 明显低于平均（增长率 < 平均 - 0.5×标准差）→ trend = "worse"

**轻微萎蔫处理**
- 如果只是轻微萎蔫，但增长率正常 → trend = "same"（需在 evidence 中说明）

# 注意事项

1. 这是多株黄瓜的整体评估，不针对单株
2. 优先使用 YOLO 指标作为客观依据
3. 图像对比时注意光照差异可能导致的视觉偏差
4. confidence 应反映你的判断确定程度
5. evidence 要具体，引用 YOLO 指标的数值变化
6. 所有描述使用中文
```

#### 5.2.2 prompts/plant_response/user_v1.md

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

---

## 6. 依赖管理

### 6.1 使用 uv 初始化项目

```bash
# 安装 uv（如未安装）
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip:
pip install uv

# 初始化项目
cd cucumber-irrigation
uv init

# 设置 Python 版本
uv python pin 3.11
```

### 6.2 pyproject.toml

```toml
[project]
name = "cucumber-irrigation"
version = "0.1.0"
description = "温室黄瓜灌水智能体系统"
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    # LLM 调用
    "openai>=1.40.0",

    # 数据处理
    "pandas>=2.2.0",
    "numpy>=1.26.0",

    # 配置管理
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",

    # 数据验证
    "pydantic>=2.5.0",
    "jsonschema>=4.20.0",

    # 日志
    "loguru>=0.7.2",

    # CLI
    "typer>=0.12.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cucumber_irrigation"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### 6.3 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| openai | >=1.40.0 | OpenAI 兼容 API 调用 |
| pandas | >=2.2.0 | CSV 数据处理 |
| numpy | >=1.26.0 | 数值计算 |
| pyyaml | >=6.0 | YAML 配置解析 |
| python-dotenv | >=1.0.0 | 环境变量管理 |
| pydantic | >=2.5.0 | 数据模型验证 |
| jsonschema | >=4.20.0 | JSON Schema 验证 |
| loguru | >=0.7.2 | 日志记录 |
| typer | >=0.12.0 | CLI 命令行 |
| rich | >=13.7.0 | 终端美化输出 |

### 6.4 安装依赖

```bash
# 创建虚拟环境并安装依赖
uv sync

# 安装开发依赖
uv sync --dev

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

---

## 7. 脚本设计

### 7.1 scripts/build_pairs.py

```python
#!/usr/bin/env python
"""P0.1: 构建日期配对索引"""

import typer
from pathlib import Path
from loguru import logger

from cucumber_irrigation.processors.pairs_builder import PairsBuilder
from cucumber_irrigation.config import load_settings

app = typer.Typer()


@app.command()
def main(
    images_dir: str = typer.Option(None, help="图像目录"),
    csv_path: str = typer.Option(None, help="CSV 文件路径"),
    output: str = typer.Option(None, help="输出路径")
):
    """构建日期配对索引"""
    settings = load_settings()

    images_dir = images_dir or settings["data"]["images_dir"]
    csv_path = csv_path or settings["data"]["csv_path"]
    output = output or settings["output"]["pairs_index"]

    logger.info(f"Images dir: {images_dir}")
    logger.info(f"CSV path: {csv_path}")

    builder = PairsBuilder(images_dir, csv_path)
    pairs = builder.build_pairs()

    logger.info(f"Built {len(pairs)} pairs")

    builder.save_pairs_index(output)
    logger.success(f"Saved to {output}")


if __name__ == "__main__":
    app()
```

### 7.2 scripts/generate_responses.py

```python
#!/usr/bin/env python
"""P0.2: 批量生成 PlantResponse"""

import typer
from pathlib import Path
from loguru import logger
import json
import time

from cucumber_irrigation.services.llm_service import LLMService
from cucumber_irrigation.services.image_service import ImageService
from cucumber_irrigation.utils.prompt_builder import PromptBuilder
from cucumber_irrigation.config import load_settings, load_api_key

app = typer.Typer()


@app.command()
def main(
    pairs_index: str = typer.Option(None, help="配对索引路径"),
    output_dir: str = typer.Option(None, help="输出目录"),
    start: int = typer.Option(0, help="起始索引"),
    end: int = typer.Option(None, help="结束索引")
):
    """批量生成 PlantResponse"""
    settings = load_settings()
    api_key = load_api_key()

    pairs_index = pairs_index or settings["output"]["pairs_index"]
    output_dir = output_dir or settings["output"]["plant_responses_dir"]

    # 加载配对
    with open(pairs_index) as f:
        data = json.load(f)
    pairs = data["pairs"][start:end]

    logger.info(f"Processing {len(pairs)} pairs")

    # 初始化服务
    llm = LLMService(
        api_key=api_key,
        base_url=settings["llm"]["base_url"],
        model=settings["llm"]["model"]
    )
    prompt_builder = PromptBuilder(settings["prompts"]["dir"])

    # 加载 prompt
    system_prompt = prompt_builder.load_system_prompt()
    user_template = prompt_builder.load_user_template()
    examples = prompt_builder.load_examples()

    # 加载增长率统计
    with open(settings["output"]["growth_stats"]) as f:
        growth_stats = json.load(f)

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 批量处理
    success = 0
    failed = 0

    for pair in pairs:
        date = pair["date"]
        output_path = Path(output_dir) / f"{date}.json"

        if output_path.exists():
            logger.info(f"Skip {date} (exists)")
            continue

        try:
            # 编码图像
            img_today = ImageService.encode_image(pair["image_today"])
            img_yesterday = ImageService.encode_image(pair["image_yesterday"])

            # 构建 prompt
            user_prompt = prompt_builder.build_user_prompt(
                user_template,
                date=date,
                yolo_today=pair["yolo_today"],
                yolo_yesterday=pair["yolo_yesterday"],
                env_today=pair["env_today"],
                growth_stats=growth_stats
            )

            # 调用 LLM
            response = llm.generate_plant_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_today_b64=img_today,
                image_yesterday_b64=img_yesterday,
                examples=examples
            )

            # 解析并保存
            result = json.loads(response)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.success(f"Generated {date}")
            success += 1

        except Exception as e:
            logger.error(f"Failed {date}: {e}")
            failed += 1

        # 避免 API 限流
        time.sleep(1)

    logger.info(f"Done: {success} success, {failed} failed")


if __name__ == "__main__":
    app()
```

### 7.3 scripts/eval_consistency.py

```python
#!/usr/bin/env python
"""P0.4: 一致率评估"""

import typer
from pathlib import Path
from loguru import logger
import json
from collections import Counter

app = typer.Typer()


@app.command()
def main(
    predictions_dir: str = typer.Option(
        "outputs/plant_responses", help="预测结果目录"
    ),
    ground_truth: str = typer.Option(
        "annotations/ground_truth.jsonl", help="人工标注文件"
    ),
    output: str = typer.Option(
        "reports/consistency_report.md", help="输出报告路径"
    )
):
    """评估一致率"""
    # 加载预测
    predictions = {}
    for f in Path(predictions_dir).glob("*.json"):
        date = f.stem
        with open(f) as fp:
            data = json.load(fp)
            predictions[date] = data["comparison"]["trend"]

    # 加载标注
    ground_truth_data = {}
    with open(ground_truth) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                ground_truth_data[data["date"]] = data["human_trend"]

    # 统计
    total = 0
    correct = 0
    confusion = Counter()

    for date, gt in ground_truth_data.items():
        if date not in predictions:
            continue

        pred = predictions[date]
        total += 1

        if pred == gt:
            correct += 1
        else:
            confusion[(pred, gt)] += 1

    accuracy = correct / total if total > 0 else 0

    # 生成报告
    report = f"""# 一致率评估报告

## 总体指标

| 指标 | 值 |
|------|-----|
| 总样本数 | {total} |
| 正确数 | {correct} |
| 一致率 | {accuracy:.2%} |

## 混淆分析

| 预测 → 实际 | 次数 |
|-------------|------|
"""
    for (pred, gt), count in sorted(confusion.items()):
        report += f"| {pred} → {gt} | {count} |\n"

    report += f"""
## 结论

{'✅ 一致率达标 (≥80%)' if accuracy >= 0.8 else '❌ 一致率未达标，需要优化 Prompt'}
"""

    # 保存报告
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"Accuracy: {accuracy:.2%}")
    logger.info(f"Report saved to {output}")


if __name__ == "__main__":
    app()
```

---

## 8. 接口设计

### 8.1 LLM API 调用

```python
# 请求格式
{
    "model": "gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": "System Prompt..."
        },
        # Few-shot 示例（可选）
        {
            "role": "user",
            "content": "示例输入..."
        },
        {
            "role": "assistant",
            "content": "{...示例输出 JSON...}"
        },
        # 当前请求
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "User Prompt..."},
                {"type": "text", "text": "昨日图像:"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
                {"type": "text", "text": "今日图像:"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ]
        }
    ],
    "temperature": 0.3,
    "max_tokens": 2000,
    "response_format": {"type": "json_object"}
}
```

### 8.2 pairs_index.json 格式

```json
{
  "created_at": "2024-12-25T10:00:00",
  "total_pairs": 84,
  "pairs": [
    {
      "date": "2024-03-15",
      "image_today": "data/images/0315.jpg",
      "image_yesterday": "data/images/0314.jpg",
      "yolo_today": {
        "leaf_instance_count": 3.31,
        "leaf_average_mask": 819.85,
        "flower_instance_count": 0,
        "flower_mask_pixel_count": 0,
        "terminal_average_mask": 0,
        "fruit_mask_average": 0,
        "all_leaf_mask": 21726
      },
      "yolo_yesterday": {
        "leaf_instance_count": 3.44,
        "leaf_average_mask": 710.44,
        "all_leaf_mask": 19537
      },
      "env_today": {
        "temperature": 20.53,
        "humidity": 65.88,
        "light": 7632.46
      }
    }
  ]
}
```

---

## 9. 错误处理

### 9.1 错误类型

| 错误类型 | 处理方式 |
|----------|----------|
| API 超时 | 重试 3 次，每次间隔 2 秒 |
| API 限流 (429) | 等待 60 秒后重试 |
| JSON 解析失败 | 记录原始响应，跳过该样本 |
| 图像文件不存在 | 跳过该配对，记录日志 |
| Schema 验证失败 | 记录错误，继续处理 |

### 9.2 日志配置

```python
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>"
)
logger.add(
    "logs/phase0_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days"
)
```

---

## 10. 附录

### 10.1 命令速查

```bash
# 初始化项目
uv sync

# 构建配对索引
uv run python scripts/build_pairs.py

# 计算增长率统计
uv run python scripts/calc_growth_stats.py

# 批量生成（全量）
uv run python scripts/generate_responses.py

# 批量生成（指定范围）
uv run python scripts/generate_responses.py --start 0 --end 10

# 评估一致率
uv run python scripts/eval_consistency.py

# 运行测试
uv run pytest tests/
```

### 10.2 输出示例

```json
// outputs/plant_responses/2024-03-15.json
{
  "date": "2024-03-15",
  "comparison": {
    "trend": "better",
    "confidence": 0.85,
    "evidence": "叶片总掩码面积从 19537 增至 21726，增长 11.2%，高于全生育期平均增长率 4903/天"
  },
  "abnormalities": {
    "wilting": false,
    "yellowing": false,
    "pest_damage": null,
    "other": null
  },
  "growth_stage": "vegetative",
  "key_observations": [
    "叶片总掩码面积增长 11.2%，高于平均水平",
    "多株黄瓜整体长势良好，叶色浓绿",
    "未观察到萎蔫或病害迹象"
  ]
}
```
