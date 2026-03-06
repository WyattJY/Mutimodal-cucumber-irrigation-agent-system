# 温室黄瓜灌水智能体系统 - 开发任务清单 v27

> **版本**: v1.0
> **创建日期**: 2025-12-27
> **对应文档**: requirements27.md, design27.md
> **预估总任务数**: 45+ 个子任务

---

## 任务总览

| Phase | 阶段名称 | 任务数 | 优先级 | 说明 |
|-------|---------|--------|--------|------|
| Phase A | 环境准备与模型迁移 | 6 | P0 | 模型文件、依赖安装 |
| Phase B | 智能问答功能 (LLM) | 12 | P0 | GPT-5.2 对话、Settings 配置 |
| Phase C | YOLO 视觉分析 | 10 | P0 | 图像分割、指标展示 |
| Phase D | TSMixer 灌水预测 | 11 | P0 | 预测流水线、输入表单 |
| Phase E | 界面完善与集成 | 8 | P1 | Dashboard 更新、路由整合 |
| Phase F | 测试与优化 | 5 | P2 | 集成测试、性能优化 |

**重要说明**:
- Milvus 向量检索暂时跳过 (Windows 环境限制)
- 先实现 LLM 直接问答，后续再接入 RAG
- 支持用户自定义 API Key (Settings 页面配置)

---

## Phase A: 环境准备与模型迁移

### A1. 模型文件迁移

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| A1.1 | 创建模型目录结构 | 创建 `models/yolo/`, `models/tsmixer/` 目录 | - | 待开始 |
| A1.2 | 迁移 YOLO 权重 | 复制 `best.pt` 到 `models/yolo/yolo11_seg_best.pt` | `v11_4seg/.../best.pt` | 待开始 |
| A1.3 | 迁移 TSMixer 权重 | 复制 `model.pt` 到 `models/tsmixer/model.pt` | `Irrigation/model.pt` | 待开始 |
| A1.4 | 导出 Scaler 参数 | 从训练代码导出 `scaler.pkl` | `models/tsmixer/scaler.pkl` | 待开始 |

**详细步骤**:

```bash
# A1.1 创建目录
mkdir -p cucumber-irrigation/models/yolo
mkdir -p cucumber-irrigation/models/tsmixer

# A1.2 复制 YOLO 权重
cp "G:\Wyatt\v11_4seg\runs\segment\jy_data_precoco_delive\exp21\weights\best.pt" \
   "cucumber-irrigation/models/yolo/yolo11_seg_best.pt"

# A1.3 复制 TSMixer 权重
cp "G:\Wyatt\Irrigation\model.pt" \
   "cucumber-irrigation/models/tsmixer/model.pt"
```

---

### A2. 后端依赖安装

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| A2.1 | 更新 pyproject.toml | 添加新依赖 (openai, ultralytics, sse-starlette) | `backend/pyproject.toml` | 待开始 |
| A2.2 | 安装依赖 | 运行 `uv sync` 安装所有依赖 | - | 待开始 |

**需要添加的依赖**:

```toml
# 新增依赖
"openai>=1.50.0",           # LLM 调用
"sse-starlette>=2.0.0",     # SSE 流式响应
"ultralytics>=8.3.0",       # YOLO
"torch>=2.5.0",             # PyTorch
"opencv-python>=4.10.0",    # 图像处理
"pillow>=10.4.0",           # 图像处理
"python-multipart>=0.0.18", # 文件上传
```

---

## Phase B: 智能问答功能 (LLM)

> **说明**: 优先实现 LLM 直接问答，暂不接入 Milvus RAG

### B1. 后端 - LLM 服务

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| B1.1 | 创建配置管理模块 | 管理 API Key、Base URL 等配置 | `backend/app/core/config.py` | 待开始 |
| B1.2 | 实现 LLMService | OpenAI 客户端封装，支持流式输出 | `backend/app/services/llm_service.py` | 待开始 |
| B1.3 | 实现 Chat API 路由 | POST `/chat`, GET `/chat/stream` | `backend/app/api/v1/chat.py` | 待开始 |
| B1.4 | 实现 Settings API | GET/PUT `/settings` 配置管理 | `backend/app/api/v1/settings.py` | 待开始 |
| B1.5 | 注册路由 | 在 main.py 中注册新路由 | `backend/app/main.py` | 待开始 |

**B1.1 配置管理模块设计**:

```python
# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "settings.json"

class Settings(BaseSettings):
    # 默认 LLM 配置 (你的 API Key)
    default_openai_api_key: str = "your_api_key_here"  # 你的默认 API Key
    default_openai_base_url: str = "https://api.openai.com/v1"
    default_openai_model: str = "gpt-5.2"

    # 用户自定义配置 (可选)
    user_openai_api_key: Optional[str] = None
    user_openai_base_url: Optional[str] = None
    user_openai_model: Optional[str] = None

    @property
    def active_api_key(self) -> str:
        return self.user_openai_api_key or self.default_openai_api_key

    @property
    def active_base_url(self) -> str:
        return self.user_openai_base_url or self.default_openai_base_url

    @property
    def active_model(self) -> str:
        return self.user_openai_model or self.default_openai_model

    def save_user_config(self, api_key: str = None, base_url: str = None, model: str = None):
        """保存用户配置到文件"""
        pass

    def load_user_config(self):
        """从文件加载用户配置"""
        pass
```

**B1.2 LLMService 设计**:

```python
# backend/app/services/llm_service.py

from openai import AsyncOpenAI
from typing import AsyncGenerator
from app.core.config import settings

class LLMService:
    """LLM 对话服务 - 支持 GPT-5.2"""

    def __init__(self):
        self._client = None
        self.system_prompt = """你是 AGRI-COPILOT，一个专业的温室农业专家助手。
你擅长：
- 温室黄瓜种植技术
- 灌溉管理与水分调控
- 病虫害识别与防治
- 环境调控 (温度、湿度、光照)
- FAO56 作物需水量计算

请用专业但易懂的语言回答用户问题。如果不确定，请诚实说明。"""

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.active_api_key,
                base_url=settings.active_base_url
            )
        return self._client

    def refresh_client(self):
        """当配置更新时刷新客户端"""
        self._client = None

    async def chat(self, message: str, history: list = None) -> str:
        """非流式对话"""
        pass

    async def chat_stream(self, message: str, history: list = None) -> AsyncGenerator[str, None]:
        """流式对话 (SSE)"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = await self.client.chat.completions.create(
            model=settings.active_model,
            messages=messages,
            stream=True
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

llm_service = LLMService()
```

**B1.3 Chat API 路由**:

```python
# backend/app/api/v1/chat.py

from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse
from app.services.llm_service import llm_service
import json

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(request: ChatRequest):
    """非流式对话"""
    response = await llm_service.chat(request.message, request.history)
    return {"success": True, "data": {"content": response}}

@router.get("/stream")
async def chat_stream(query: str = Query(...)):
    """SSE 流式对话"""
    async def generate():
        async for chunk in llm_service.chat_stream(query):
            yield {
                "event": "content",
                "data": json.dumps({"text": chunk})
            }
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(generate())
```

---

### B2. 前端 - 聊天组件

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| B2.1 | 创建 chatStore | Zustand 状态管理 (消息列表、流式状态) | `frontend/src/stores/chatStore.ts` | 待开始 |
| B2.2 | 创建 ChatInput 组件 | 输入框 + 发送按钮 | `frontend/src/components/chat/ChatInput.tsx` | 待开始 |
| B2.3 | 创建 ChatMessage 组件 | 消息气泡 (用户/AI) | `frontend/src/components/chat/ChatMessage.tsx` | 待开始 |
| B2.4 | 创建 StreamingText 组件 | 打字机效果展示 | `frontend/src/components/chat/StreamingText.tsx` | 待开始 |
| B2.5 | 创建 ChatPanel 组件 | 完整聊天面板 (集成上述组件) | `frontend/src/components/chat/ChatPanel.tsx` | 待开始 |
| B2.6 | 集成到 Sidebar | 在侧边栏添加 AGRI-COPILOT 入口 | `frontend/src/components/layout/Sidebar/Sidebar.tsx` | 待开始 |

**B2.1 chatStore 设计**:

```typescript
// frontend/src/stores/chatStore.ts

import { create } from 'zustand'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  currentStreamContent: string

  sendMessage: (content: string) => Promise<void>
  clearHistory: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  currentStreamContent: '',

  sendMessage: async (content: string) => {
    // 1. 添加用户消息
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    set(state => ({ messages: [...state.messages, userMessage] }))

    // 2. 开始流式接收
    set({ isStreaming: true, currentStreamContent: '' })

    const eventSource = new EventSource(
      `/api/v1/chat/stream?query=${encodeURIComponent(content)}`
    )

    eventSource.addEventListener('content', (e) => {
      const { text } = JSON.parse(e.data)
      set(state => ({ currentStreamContent: state.currentStreamContent + text }))
    })

    eventSource.addEventListener('done', () => {
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: get().currentStreamContent,
        timestamp: new Date()
      }
      set(state => ({
        messages: [...state.messages, assistantMessage],
        isStreaming: false,
        currentStreamContent: ''
      }))
      eventSource.close()
    })
  },

  clearHistory: () => set({ messages: [] })
}))
```

---

### B3. 前端 - Settings 页面

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| B3.1 | 创建 settingsStore | 管理 API 配置状态 | `frontend/src/stores/settingsStore.ts` | 待开始 |
| B3.2 | 更新 Settings 页面 | 添加 API Key 配置表单 | `frontend/src/pages/Settings.tsx` | 待开始 |

**B3.2 Settings 页面 API 配置区域**:

```typescript
// Settings.tsx 中新增的 API 配置区域

/**
 * ┌─────────────────────────────────────────────────────────────────┐
 * │  设置                                                           │
 * ├─────────────────────────────────────────────────────────────────┤
 * │                                                                 │
 * │  ┌───────────────────────────────────────────────────────────┐ │
 * │  │  LLM API 配置                                              │ │
 * │  ├───────────────────────────────────────────────────────────┤ │
 * │  │                                                           │ │
 * │  │  ○ 使用默认配置 (GPT-5.2)                                  │ │
 * │  │  ● 使用自定义配置                                          │ │
 * │  │                                                           │ │
 * │  │  API Key:    [your_api_key_here          ]                │ │
 * │  │  Base URL:   [https://api.openai.com/v1  ]                │ │
 * │  │  Model:      [gpt-4-turbo            ▼]                   │ │
 * │  │                                                           │ │
 * │  │  [  测试连接  ]  [  保存配置  ]                            │ │
 * │  │                                                           │ │
 * │  │  状态: ✓ 连接成功                                         │ │
 * │  └───────────────────────────────────────────────────────────┘ │
 * │                                                                 │
 * │  ┌───────────────────────────────────────────────────────────┐ │
 * │  │  其他设置...                                               │ │
 * │  └───────────────────────────────────────────────────────────┘ │
 * │                                                                 │
 * └─────────────────────────────────────────────────────────────────┘
 */
```

---

## Phase C: YOLO 视觉分析

### C1. 后端 - YOLO 服务完善

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| C1.1 | 更新模型路径配置 | 指向新的模型目录 | `backend/app/services/yolo_service.py` | 待开始 |
| C1.2 | 实现分块推理逻辑 | 参考 tuili.py 实现 15 块推理 | `backend/app/services/yolo_service.py` | 待开始 |
| C1.3 | 完善指标提取 | 提取 11 维特征中的 8 个视觉指标 | `backend/app/services/yolo_service.py` | 待开始 |
| C1.4 | 实现 Vision API | GET `/vision/image/{date}`, `/vision/metrics/{date}` | `backend/app/api/v1/vision.py` | 待开始 |

**C1.2 分块推理逻辑 (参考 tuili.py)**:

```python
# 分块推理核心逻辑

def tile_inference(self, image: np.ndarray) -> dict:
    """
    分块推理 - 处理高分辨率图像

    1. 原始分辨率: 2880×1620
    2. 缩放至: 3200×1920
    3. 分割为 15 块 (3行×5列, 每块 640×640)
    4. 每块单独推理
    5. 合并结果
    6. 缩放回原尺寸
    """
    # 缩放
    h, w = image.shape[:2]
    target_h, target_w = 1920, 3200
    scaled = cv2.resize(image, (target_w, target_h))

    # 分块
    tile_h, tile_w = 640, 640
    rows, cols = 3, 5

    all_masks = []
    all_boxes = []
    all_classes = []

    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * tile_h, (r + 1) * tile_h
            x1, x2 = c * tile_w, (c + 1) * tile_w
            tile = scaled[y1:y2, x1:x2]

            # 推理
            results = self.model(tile, verbose=False)[0]

            # 收集结果 (需要转换坐标)
            # ...

    # 合并和去重
    # ...

    return metrics
```

---

### C2. 前端 - 视觉分析组件

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| C2.1 | 创建 ImageViewer 组件 | 图片查看 (原图/分割图切换) | `frontend/src/components/vision/ImageViewer.tsx` | 待开始 |
| C2.2 | 创建 SegmentedImage 组件 | 显示带掩码的分割图 | `frontend/src/components/vision/SegmentedImage.tsx` | 待开始 |
| C2.3 | 创建 MetricsDisplay 组件 | 显示叶片/花朵/果实指标 | `frontend/src/components/vision/MetricsDisplay.tsx` | 待开始 |
| C2.4 | 创建 ImageComparison 组件 | 今日 vs 昨日对比 | `frontend/src/components/vision/ImageComparison.tsx` | 待开始 |
| C2.5 | 创建 ClassLegend 组件 | 类别颜色图例 | `frontend/src/components/vision/ClassLegend.tsx` | 待开始 |
| C2.6 | 创建 Vision 页面 | 组合上述组件 | `frontend/src/pages/Vision.tsx` | 待开始 |

**C2.3 MetricsDisplay 组件设计**:

```typescript
// components/vision/MetricsDisplay.tsx

interface MetricCard {
  label: string           // 叶片、花朵、顶芽、果实
  count: number           // 当前数量
  change: number          // 与昨日变化 (+2, -1, 0)
  avgMask: number         // 平均掩码面积
  color: string           // 对应颜色
  icon: string            // 图标
}

interface MetricsDisplayProps {
  metrics: {
    leaf: MetricCard
    flower: MetricCard
    terminal: MetricCard
    fruit: MetricCard
  }
}

/**
 * 布局:
 * ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 * │  🌿 叶片  │ │  🌸 花朵  │ │  🌱 顶芽  │ │  🥒 果实  │
 * │   12 片  │ │   5 朵   │ │   2 个   │ │   3 个   │
 * │   ↑ +2   │ │   ↓ -1   │ │   → 0   │ │   ↑ +1   │
 * └──────────┘ └──────────┘ └──────────┘ └──────────┘
 */
```

---

## Phase D: TSMixer 灌水预测

### D1. 后端 - TSMixer 服务

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| D1.1 | 创建 TSMixer 模型定义 | PyTorch 模型类 (与训练时一致) | `backend/app/ml/tsmixer/model.py` | 待开始 |
| D1.2 | 实现 TSMixerService | 模型加载、预测、标准化 | `backend/app/services/tsmixer_service.py` | 待开始 |
| D1.3 | 实现冷启动填充逻辑 | 使用 irrigation_pre.csv 填充缺失数据 | `backend/app/utils/cold_start.py` | 待开始 |
| D1.4 | 实现 PredictionService | 整合 YOLO + TSMixer 流水线 | `backend/app/services/prediction_service.py` | 待开始 |
| D1.5 | 实现 Predict API | POST `/predict` | `backend/app/api/v1/predict.py` | 待开始 |

**D1.2 TSMixerService 设计**:

```python
# backend/app/services/tsmixer_service.py

import torch
import numpy as np
import joblib
from pathlib import Path

class TSMixerService:
    """TSMixer 灌水量预测服务"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.seq_length = 96
        self.n_features = 11
        self.model_path = Path("models/tsmixer/model.pt")
        self.scaler_path = Path("models/tsmixer/scaler.pkl")

    def load(self):
        """加载模型和 Scaler"""
        # 加载模型
        self.model = torch.load(self.model_path, map_location="cpu")
        self.model.eval()

        # 加载 Scaler
        self.scaler = joblib.load(self.scaler_path)

    def predict(self, features: np.ndarray) -> float:
        """
        执行预测

        Args:
            features: shape (96, 11) 的输入数组

        Returns:
            灌水量预测值 (L/m²)
        """
        # 标准化
        features_scaled = self.scaler.transform(features)

        # 转换为 Tensor
        x = torch.FloatTensor(features_scaled).unsqueeze(0)  # (1, 96, 11)

        # 推理
        with torch.no_grad():
            pred = self.model(x)

        # 逆标准化 (只对 target 列)
        pred_value = self.scaler.inverse_transform_target(pred.item())

        return pred_value

    def build_features(
        self,
        env_data: dict,
        yolo_metrics: dict,
        historical_data: list
    ) -> np.ndarray:
        """
        构建 96×11 特征矩阵

        11 个特征:
        0. temperature
        1. humidity
        2. light
        3. leaf Instance Count
        4. leaf average mask
        5. flower Instance Count
        6. flower Mask Pixel Count
        7. terminal average Mask Pixel Count
        8. fruit Mask average
        9. all leaf mask
        10. Target (历史灌水量)
        """
        features = np.zeros((self.seq_length, self.n_features))

        # 填充历史数据 (前 95 天)
        for i, day_data in enumerate(historical_data[-95:]):
            features[i] = [
                day_data['temperature'],
                day_data['humidity'],
                day_data['light'],
                day_data['leaf_count'],
                day_data['leaf_avg_mask'],
                day_data['flower_count'],
                day_data['flower_mask'],
                day_data['terminal_mask'],
                day_data['fruit_mask'],
                day_data['all_leaf_mask'],
                day_data['irrigation']
            ]

        # 填充当天数据 (第 96 天)
        features[95] = [
            env_data['temperature'],
            env_data['humidity'],
            env_data['light'],
            yolo_metrics['leaf_instance_count'],
            yolo_metrics['leaf_average_mask'],
            yolo_metrics['flower_instance_count'],
            yolo_metrics['flower_mask_pixel_count'],
            yolo_metrics['terminal_average_mask'],
            yolo_metrics['fruit_mask_average'],
            yolo_metrics['all_leaf_mask'],
            0  # Target 待预测
        ]

        return features

tsmixer_service = TSMixerService()
```

**D1.3 冷启动填充逻辑**:

```python
# backend/app/utils/cold_start.py

import pandas as pd
from datetime import datetime, timedelta

def fill_cold_start(
    available_data: list,
    cold_start_csv: str,
    target_date: str,
    required_days: int = 96
) -> list:
    """
    冷启动数据填充

    当历史数据不足 96 天时，使用 irrigation_pre.csv 填充

    填充规则:
    1. 优先使用已有的真实数据
    2. 缺失日期按月日匹配 (如 6月14日 匹配去年 6月14日)
    3. 如果月日也没有，使用相邻日期平均值
    """
    # 加载历史填充数据
    cold_start_df = pd.read_csv(cold_start_csv)
    cold_start_df['date'] = pd.to_datetime(cold_start_df['date'])
    cold_start_df['month_day'] = cold_start_df['date'].dt.strftime('%m-%d')

    # 构建日期范围
    target = datetime.strptime(target_date, '%Y-%m-%d')
    date_range = [(target - timedelta(days=i)).strftime('%Y-%m-%d')
                  for i in range(required_days - 1, -1, -1)]

    # 创建已有数据的索引
    available_dict = {d['date']: d for d in available_data}

    # 填充数据
    filled_data = []
    for date_str in date_range:
        if date_str in available_dict:
            # 使用真实数据
            filled_data.append(available_dict[date_str])
        else:
            # 使用冷启动数据
            month_day = date_str[5:]  # "06-14"
            match = cold_start_df[cold_start_df['month_day'] == month_day]

            if not match.empty:
                row = match.iloc[0]
                filled_data.append({
                    'date': date_str,
                    'temperature': row['temperature'],
                    'humidity': row['humidity'],
                    'light': row['light'],
                    'leaf_count': row['leaf_count'],
                    'leaf_avg_mask': row['leaf_avg_mask'],
                    # ... 其他字段
                    'is_filled': True
                })
            else:
                # 使用相邻日期平均值
                filled_data.append(get_neighbor_average(cold_start_df, month_day))

    return filled_data
```

---

### D2. 前端 - 预测组件

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| D2.1 | 安装 react-dropzone | 文件拖拽上传库 | `frontend/package.json` | 待开始 |
| D2.2 | 创建 predictionStore | 预测状态管理 | `frontend/src/stores/predictionStore.ts` | 待开始 |
| D2.3 | 创建 ImageUpload 组件 | 拖拽/点击上传图片 | `frontend/src/components/prediction/ImageUpload.tsx` | 待开始 |
| D2.4 | 创建 EnvDataForm 组件 | 温度/湿度/光照输入表单 | `frontend/src/components/prediction/EnvDataForm.tsx` | 待开始 |
| D2.5 | 创建 PredictionPanel 组件 | 预测结果展示 | `frontend/src/components/prediction/PredictionPanel.tsx` | 待开始 |
| D2.6 | 创建 Predict 页面 | 组合上述组件 | `frontend/src/pages/Predict.tsx` | 待开始 |

**D2.3 ImageUpload 组件设计**:

```typescript
// components/prediction/ImageUpload.tsx

import { useDropzone } from 'react-dropzone'

interface ImageUploadProps {
  onUpload: (file: File, preview: string) => void
  currentPreview?: string
  isLoading?: boolean
  maxSize?: number  // MB, 默认 10
}

/**
 * 布局:
 * ┌─────────────────────────────────────┐
 * │                                     │
 * │    [图片预览区域 / 占位符]           │
 * │                                     │
 * │    ┌─────────────────────────┐     │
 * │    │  📷 拖拽或点击上传图片   │     │
 * │    │  支持 JPG, PNG          │     │
 * │    │  最大 10MB              │     │
 * │    └─────────────────────────┘     │
 * │                                     │
 * └─────────────────────────────────────┘
 */
```

**D2.4 EnvDataForm 组件设计**:

```typescript
// components/prediction/EnvDataForm.tsx

interface EnvData {
  temperature: number  // 15-35°C
  humidity: number     // 40-95%
  light: number        // 0-100000 lux
  date: string         // YYYY-MM-DD
}

interface EnvDataFormProps {
  onSubmit: (data: EnvData) => void
  isLoading?: boolean
  defaultValues?: Partial<EnvData>
}

/**
 * 布局:
 * ┌─────────────────────────────────────┐
 * │  环境数据                            │
 * ├─────────────────────────────────────┤
 * │                                     │
 * │  🌡️ 日均温度 (°C)                   │
 * │  [=====|=====] 25.5                 │
 * │  15          35                     │
 * │                                     │
 * │  💧 日均湿度 (%)                     │
 * │  [=====|=====] 75                   │
 * │  40          95                     │
 * │                                     │
 * │  ☀️ 日均光照 (lux)                  │
 * │  [__________45000__________]        │
 * │                                     │
 * │  📅 预测日期                         │
 * │  [2024-06-15      📅]               │
 * │                                     │
 * │  [     🚀 开始预测     ]            │
 * │                                     │
 * └─────────────────────────────────────┘
 */
```

---

## Phase E: 界面完善与集成

### E1. 路由与导航

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| E1.1 | 添加新路由 | `/predict`, `/vision` | `frontend/src/routes/index.tsx` | 待开始 |
| E1.2 | 更新 Sidebar 导航 | 添加预测、视觉分析入口 | `frontend/src/components/layout/Sidebar/Sidebar.tsx` | 待开始 |

---

### E2. Dashboard 更新

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| E2.1 | 添加快捷预测入口 | Dashboard 添加"今日预测"卡片 | `frontend/src/pages/Dashboard.tsx` | 待开始 |
| E2.2 | 添加视觉分析预览 | Dashboard 添加今日分割图预览 | `frontend/src/pages/Dashboard.tsx` | 待开始 |
| E2.3 | 接入真实数据 | 从 API 获取真实统计数据 | `frontend/src/pages/Dashboard.tsx` | 待开始 |

---

### E3. API 服务层

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| E3.1 | 创建 predictionService | 预测 API 调用 | `frontend/src/services/predictionService.ts` | 待开始 |
| E3.2 | 创建 visionService | 视觉分析 API 调用 | `frontend/src/services/visionService.ts` | 待开始 |
| E3.3 | 创建 chatService | 聊天 API 调用 | `frontend/src/services/chatService.ts` | 待开始 |

---

## Phase F: 测试与优化

### F1. 集成测试

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| F1.1 | 后端 API 测试 | 测试所有新 API 端点 | `backend/tests/` | 待开始 |
| F1.2 | 前后端联调测试 | 完整流程测试 | - | 待开始 |

---

### F2. 性能优化

| 任务ID | 任务名称 | 描述 | 涉及文件 | 状态 |
|--------|---------|------|----------|------|
| F2.1 | YOLO 推理优化 | GPU 加速、批处理 | `backend/app/services/yolo_service.py` | 待开始 |
| F2.2 | 前端骨架屏 | 添加加载状态骨架屏 | `frontend/src/components/common/Skeleton.tsx` | 待开始 |
| F2.3 | 图片懒加载 | 优化图片加载性能 | - | 待开始 |

---

## 任务依赖关系

```
Phase A (环境准备)
    │
    ├──→ Phase B (LLM 问答)
    │        │
    │        └──→ B1 后端 ──→ B2 前端 ──→ B3 Settings
    │
    ├──→ Phase C (YOLO 视觉)
    │        │
    │        └──→ C1 后端 ──→ C2 前端
    │
    └──→ Phase D (TSMixer 预测)
             │
             └──→ D1 后端 ──→ D2 前端
                     │
                     └── 依赖 C1 (YOLO 指标)

Phase E (界面集成) ← 依赖 B, C, D 完成
Phase F (测试优化) ← 依赖 E 完成
```

---

## 开发顺序建议

### 第一批 (可并行)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [A1] 模型迁移  ───→  [B1] LLM 后端  ───→  [B2] 聊天前端        │
│                                     ↘                          │
│                                       [B3] Settings 页面       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 第二批 (可并行)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [C1] YOLO 后端  ───→  [C2] 视觉前端                            │
│                                                                 │
│  [D1] TSMixer 后端 (依赖 C1)  ───→  [D2] 预测前端               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 第三批

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [E1-E3] 界面集成  ───→  [F1-F2] 测试优化                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 后续扩展 (暂不实现)

| 功能 | 说明 | 优先级 |
|------|------|--------|
| Milvus RAG 集成 | Windows 环境需要 Docker 或使用 Milvus Lite | 待定 |
| 数据导出功能 | 导出历史记录为 CSV/Excel | P2 |
| 移动端适配 | 响应式布局优化 | P2 |
| Docker 部署 | 容器化部署 | P2 |

---

<div align="center">

**文档版本**: v1.0
**创建日期**: 2025-12-27
**任务总数**: 52 个子任务
**维护者**: AgriAgent Development Team

</div>
