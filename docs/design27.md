# 温室黄瓜灌水智能体系统 - 设计文档 v27

> **版本**: v1.0
> **创建日期**: 2025-12-27
> **文档状态**: 设计阶段
> **对应需求**: requirements27.md

---

## 1. 核心目标

### 1.1 系统目标

构建一个完整的温室黄瓜智能灌溉决策系统，实现：

| 目标 | 描述 | 优先级 |
|------|------|--------|
| **智能预测** | 基于 TSMixer 模型预测次日灌水量 | P0 |
| **视觉分析** | 基于 YOLOv11-seg 分析植物生长状态 | P0 |
| **知识问答** | 基于 RAG + LLM 提供农业专业问答 | P0 |
| **数据输入** | 支持用户上传图片和环境数据 | P0 |
| **可视化展示** | 直观展示预测结果、分割图像、趋势图表 | P1 |

### 1.2 技术指标

| 指标 | 目标值 |
|------|--------|
| TSMixer 预测精度 | MAE < 0.5 L/m² |
| YOLO 分割精度 | mAP@0.5 > 0.85 |
| RAG 检索准确率 | Top-5 召回率 > 0.9 |
| API 响应时间 | < 2s (预测)，< 5s (问答) |
| 前端首屏加载 | < 3s |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AgriAgent System                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         Frontend (React 19 + Vite)                     │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │  Dashboard  │  │   Predict   │  │   Vision    │  │    Chat     │  │ │
│  │  │    Page     │  │    Page     │  │    Page     │  │   Sidebar   │  │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │ │
│  │         │                │                │                │         │ │
│  │  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐  │ │
│  │  │                    TanStack Query + Zustand                     │  │ │
│  │  │                      (状态管理 + 数据缓存)                        │  │ │
│  │  └─────────────────────────────┬───────────────────────────────────┘  │ │
│  └────────────────────────────────┼───────────────────────────────────────┘ │
│                                   │ HTTP/SSE                                │
│  ┌────────────────────────────────┼───────────────────────────────────────┐ │
│  │                         Backend (FastAPI)                              │ │
│  ├────────────────────────────────┼───────────────────────────────────────┤ │
│  │                                │                                       │ │
│  │  ┌─────────────────────────────┴─────────────────────────────────────┐ │ │
│  │  │                          API Gateway                              │ │ │
│  │  │  /api/predict  /api/vision  /api/chat  /api/upload  /api/episodes │ │ │
│  │  └───────┬─────────────┬────────────┬─────────────┬──────────────────┘ │ │
│  │          │             │            │             │                    │ │
│  │  ┌───────┴───────┐ ┌───┴───┐ ┌──────┴──────┐ ┌────┴────┐              │ │
│  │  │ PredictionSvc │ │YOLOSvc│ │  RAGService │ │UploadSvc│              │ │
│  │  └───────┬───────┘ └───┬───┘ └──────┬──────┘ └────┬────┘              │ │
│  │          │             │            │             │                    │ │
│  │  ┌───────┴───────┐     │     ┌──────┴──────┐      │                   │ │
│  │  │ TSMixerService│     │     │  LLMService │      │                   │ │
│  │  └───────┬───────┘     │     └──────┬──────┘      │                   │ │
│  └──────────┼─────────────┼────────────┼─────────────┼───────────────────┘ │
│             │             │            │             │                      │
│  ┌──────────┴─────────────┴────────────┴─────────────┴───────────────────┐ │
│  │                          Storage Layer                                 │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │ │
│  │  │ PostgreSQL │  │   Milvus   │  │  MongoDB   │  │   File System  │   │ │
│  │  │  Episodes  │  │  Vectors   │  │  Chunks    │  │  Images/Models │   │ │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                           ML Models                                     │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │ │
│  │  │   TSMixer Model  │  │  YOLOv11n-seg    │  │     BGE-M3 + GPT     │ │ │
│  │  │   (model.pt)     │  │   (best.pt)      │  │   (Embedding + LLM)  │ │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流向图                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【灌水量预测流程】                                                           │
│                                                                             │
│  用户上传                                                                    │
│      │                                                                      │
│      ▼                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  图片上传   │───▶│ YOLO 分割   │───▶│ 特征提取    │───▶│ 构建11维    │  │
│  │  环境数据   │    │  推理服务   │    │ (8个视觉)   │    │  输入向量   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘  │
│                                                                  │         │
│                     ┌────────────────────────────────────────────┘         │
│                     ▼                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  结果展示   │◀───│ 逆标准化    │◀───│ TSMixer     │◀───│ 获取历史    │  │
│  │  (L/m²)    │    │  输出       │    │  预测       │    │  96天数据   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  【智能问答流程】                                                             │
│                                                                             │
│  用户提问                                                                    │
│      │                                                                      │
│      ▼                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  问题输入   │───▶│ BGE-M3      │───▶│ Milvus      │───▶│ 获取 TopK   │  │
│  │            │    │  Embedding  │    │  混合检索   │    │  相关片段   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘  │
│                                                                  │         │
│                     ┌────────────────────────────────────────────┘         │
│                     ▼                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  流式返回   │◀───│ GPT 生成    │◀───│ 构建 Prompt │                     │
│  │  (SSE)     │    │  回答       │    │  + Context  │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块划分

### 3.1 模块总览

```
cucumber-irrigation/
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   ├── pages/              # 页面组件
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── services/           # API 服务
│   │   ├── stores/             # 状态管理
│   │   └── types/              # TypeScript 类型
│   └── ...
│
├── backend/                     # 后端应用
│   ├── app/
│   │   ├── api/v1/             # API 路由
│   │   ├── services/           # 业务服务
│   │   ├── models/             # 数据模型
│   │   ├── ml/                 # ML 模型封装
│   │   └── utils/              # 工具函数
│   └── ...
│
├── models/                      # 模型权重
│   ├── yolo/                   # YOLO 权重
│   └── tsmixer/                # TSMixer 权重
│
├── data/                        # 数据目录
│   ├── images/                 # 温室图片
│   ├── csv/                    # CSV 数据
│   └── uploads/                # 用户上传
│
└── output/                      # 输出目录
    ├── segmented_images/       # 分割结果
    └── predictions/            # 预测记录
```

### 3.2 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| **Frontend** | 用户界面、交互逻辑 | React 组件 |
| **API Layer** | HTTP 路由、请求处理 | FastAPI routers |
| **Services** | 业务逻辑封装 | *_service.py |
| **ML Layer** | 模型加载与推理 | TSMixer, YOLO |
| **Storage** | 数据持久化 | PostgreSQL, Files |

---

## 4. 前端组件设计

### 4.1 组件层次结构

```
src/
├── components/
│   ├── layout/                      # 布局组件
│   │   ├── Layout.tsx              # 主布局
│   │   ├── Sidebar/                # 侧边栏
│   │   │   ├── Sidebar.tsx
│   │   │   └── ChatPanel.tsx       # [NEW] AGRI-COPILOT 聊天面板
│   │   └── AuroraBackground/       # 背景动画
│   │
│   ├── common/                      # 通用组件
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── LoadingSkeleton.tsx     # [NEW] 骨架屏
│   │   └── Toast.tsx
│   │
│   ├── prediction/                  # [NEW] 预测相关组件
│   │   ├── ImageUpload.tsx         # 图片上传
│   │   ├── EnvDataForm.tsx         # 环境数据表单
│   │   ├── PredictionPanel.tsx     # 预测结果展示
│   │   └── DateSelector.tsx        # 日期选择器
│   │
│   ├── vision/                      # [NEW] 视觉分析组件
│   │   ├── ImageViewer.tsx         # 图片查看器
│   │   ├── SegmentedImage.tsx      # 分割图像展示
│   │   ├── ImageComparison.tsx     # 今日/昨日对比
│   │   ├── MetricsDisplay.tsx      # 指标展示
│   │   └── ClassLegend.tsx         # 类别图例
│   │
│   ├── chat/                        # [NEW] 聊天组件
│   │   ├── ChatInput.tsx           # 输入框
│   │   ├── ChatMessage.tsx         # 消息气泡
│   │   ├── StreamingText.tsx       # 流式文本
│   │   └── SourceCitation.tsx      # 引用来源
│   │
│   └── charts/                      # 图表组件
│       ├── TrendChart.tsx          # 趋势图
│       ├── MetricsChart.tsx        # [NEW] 指标图表
│       └── GrowthChart.tsx         # [NEW] 生长曲线
│
└── pages/
    ├── Dashboard.tsx               # 仪表盘 (更新)
    ├── Predict.tsx                 # [NEW] 预测页面
    ├── Vision.tsx                  # [NEW] 视觉分析页面
    ├── History.tsx                 # 历史记录
    ├── Weekly.tsx                  # 周度报告
    ├── Knowledge.tsx               # 知识库 (更新)
    └── Settings.tsx                # 设置
```

### 4.2 新增组件详细设计

#### 4.2.1 ImageUpload 组件

```typescript
// components/prediction/ImageUpload.tsx

interface ImageUploadProps {
  onUpload: (file: File, preview: string) => void
  accept?: string
  maxSize?: number  // MB
  isLoading?: boolean
}

// 功能:
// - 拖拽上传
// - 点击选择
// - 图片预览
// - 大小校验
// - 格式校验 (JPG, PNG)
```

#### 4.2.2 EnvDataForm 组件

```typescript
// components/prediction/EnvDataForm.tsx

interface EnvData {
  temperature: number      // 日均温度 (°C)
  humidity: number         // 日均湿度 (%)
  light: number            // 日均光照 (lux) 或太阳辐射 (W/m²)
  date: string             // 预测日期
}

interface EnvDataFormProps {
  onSubmit: (data: EnvData) => void
  defaultValues?: Partial<EnvData>
  isLoading?: boolean
}

// 功能:
// - 温度输入 (范围: 15-35°C)
// - 湿度输入 (范围: 40-95%)
// - 光照输入 (范围: 0-100000 lux)
// - 日期选择
// - 表单验证
```

#### 4.2.3 PredictionPanel 组件

```typescript
// components/prediction/PredictionPanel.tsx

interface PredictionResult {
  irrigation_amount: number    // 预测灌水量 (L/m²)
  confidence: number           // 置信度 (0-1)
  model_version: string        // 模型版本
  predicted_at: string         // 预测时间
  yolo_metrics: YOLOMetrics    // YOLO 分析指标
  segmented_image_url: string  // 分割后图像 URL
}

interface PredictionPanelProps {
  result: PredictionResult | null
  isLoading?: boolean
  onOverride?: (value: number) => void
}

// 功能:
// - 显示预测灌水量 (大数字)
// - 显示置信度指示器
// - 显示 YOLO 检测指标
// - 显示分割后图像
// - 支持人工覆盖
```

#### 4.2.4 ImageViewer 组件

```typescript
// components/vision/ImageViewer.tsx

interface ImageViewerProps {
  originalImage: string        // 原始图像 URL
  segmentedImage?: string      // 分割图像 URL
  showMask?: boolean           // 是否显示掩码
  showBbox?: boolean           // 是否显示边界框
  zoomEnabled?: boolean        // 是否支持缩放
}

// 功能:
// - 原图/分割图切换
// - 缩放和平移
// - 掩码/边界框开关
// - 全屏查看
```

#### 4.2.5 ChatPanel 组件

```typescript
// components/layout/Sidebar/ChatPanel.tsx

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Citation[]         // 引用来源
  timestamp: string
}

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
}

// 功能:
// - 消息列表
// - 流式打字效果
// - 引用来源展示
// - 历史对话
```

### 4.3 页面组件设计

#### 4.3.1 Predict 页面

```typescript
// pages/Predict.tsx

/**
 * 预测页面布局:
 *
 * ┌────────────────────────────────────────────────────────────────┐
 * │  灌水量预测                                                     │
 * ├────────────────────────────────────────────────────────────────┤
 * │                                                                │
 * │  ┌──────────────────────┐  ┌────────────────────────────────┐ │
 * │  │                      │  │                                │ │
 * │  │    ImageUpload       │  │       EnvDataForm              │ │
 * │  │    (温室图片上传)     │  │    (环境数据输入)               │ │
 * │  │                      │  │                                │ │
 * │  │  [拖拽或点击上传]     │  │  温度: [____] °C               │ │
 * │  │                      │  │  湿度: [____] %                │ │
 * │  │                      │  │  光照: [____] lux              │ │
 * │  │                      │  │  日期: [____]                  │ │
 * │  │                      │  │                                │ │
 * │  │                      │  │  [  开始预测  ]                │ │
 * │  └──────────────────────┘  └────────────────────────────────┘ │
 * │                                                                │
 * │  ┌──────────────────────────────────────────────────────────┐ │
 * │  │                   PredictionPanel                         │ │
 * │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │ │
 * │  │  │ 预测灌水量    │  │ YOLO 指标    │  │ 分割图像       │  │ │
 * │  │  │    5.23      │  │ 叶片: 12     │  │ [图像展示]     │  │ │
 * │  │  │   L/m²      │  │ 花朵: 5      │  │               │  │ │
 * │  │  │             │  │ 果实: 3      │  │               │  │ │
 * │  │  └──────────────┘  └──────────────┘  └────────────────┘  │ │
 * │  └──────────────────────────────────────────────────────────┘ │
 * │                                                                │
 * └────────────────────────────────────────────────────────────────┘
 */
```

#### 4.3.2 Vision 页面

```typescript
// pages/Vision.tsx

/**
 * 视觉分析页面布局:
 *
 * ┌────────────────────────────────────────────────────────────────┐
 * │  视觉生长分析                              [日期选择器]         │
 * ├────────────────────────────────────────────────────────────────┤
 * │                                                                │
 * │  ┌──────────────────────────────────────────────────────────┐ │
 * │  │                    ImageComparison                        │ │
 * │  │  ┌────────────────────┐  ┌────────────────────┐          │ │
 * │  │  │      今日           │  │      昨日           │          │ │
 * │  │  │   原图/分割图       │  │   原图/分割图       │          │ │
 * │  │  │                    │  │                    │          │ │
 * │  │  │    [2024-06-14]    │  │    [2024-06-13]    │          │ │
 * │  │  └────────────────────┘  └────────────────────┘          │ │
 * │  │           [原图] [分割] [掩码] [边界框]                    │ │
 * │  └──────────────────────────────────────────────────────────┘ │
 * │                                                                │
 * │  ┌──────────────────────────────────────────────────────────┐ │
 * │  │                   MetricsDisplay                          │ │
 * │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
 * │  │  │ 叶片     │  │ 花朵     │  │ 顶芽     │  │ 果实     │  │ │
 * │  │  │ 12 片    │  │ 5 朵     │  │ 2 个     │  │ 3 个     │  │ │
 * │  │  │ ↑ +2    │  │ ↓ -1    │  │ → 0     │  │ ↑ +1    │  │ │
 * │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
 * │  └──────────────────────────────────────────────────────────┘ │
 * │                                                                │
 * │  ┌──────────────────────────────────────────────────────────┐ │
 * │  │  ClassLegend                                              │ │
 * │  │  ● 叶片 (绿)  ● 花朵 (黄)  ● 顶芽 (红)  ● 果实 (蓝)       │ │
 * │  └──────────────────────────────────────────────────────────┘ │
 * │                                                                │
 * └────────────────────────────────────────────────────────────────┘
 */
```

### 4.4 状态管理设计

```typescript
// stores/predictionStore.ts (Zustand)

interface PredictionState {
  // 输入状态
  uploadedImage: File | null
  imagePreview: string | null
  envData: EnvData | null

  // 预测状态
  isLoading: boolean
  result: PredictionResult | null
  error: string | null

  // Actions
  setUploadedImage: (file: File, preview: string) => void
  setEnvData: (data: EnvData) => void
  runPrediction: () => Promise<void>
  clearResult: () => void
}

// stores/chatStore.ts (Zustand)

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  currentStreamContent: string

  // Actions
  sendMessage: (content: string) => Promise<void>
  clearHistory: () => void
}
```

---

## 5. 后端服务设计

### 5.1 服务层次结构

```
backend/app/
├── api/v1/                          # API 路由层
│   ├── __init__.py
│   ├── episodes.py                 # 决策记录 API
│   ├── stats.py                    # 统计 API
│   ├── weekly.py                   # 周报 API
│   ├── knowledge.py                # 知识库 API (更新)
│   ├── override.py                 # 覆盖 API
│   ├── upload.py                   # 上传 API (更新)
│   ├── predict.py                  # [NEW] 预测 API
│   ├── vision.py                   # [NEW] 视觉分析 API
│   └── chat.py                     # [NEW] 聊天 API
│
├── services/                        # 业务服务层
│   ├── __init__.py
│   ├── episode_service.py
│   ├── yolo_service.py             # YOLO 服务 (更新)
│   ├── tsmixer_service.py          # [NEW] TSMixer 服务
│   ├── prediction_service.py       # [NEW] 预测流水线
│   ├── rag_service.py              # [NEW] RAG 服务
│   └── llm_service.py              # [NEW] LLM 服务
│
├── ml/                              # [NEW] ML 模型层
│   ├── __init__.py
│   ├── tsmixer/
│   │   ├── model.py               # TSMixer 模型定义
│   │   ├── predictor.py           # 预测器
│   │   └── scaler.py              # 标准化器
│   └── yolo/
│       ├── inference.py           # 推理逻辑
│       └── postprocess.py         # 后处理
│
├── models/                          # 数据模型层
│   ├── __init__.py
│   ├── schemas.py                  # Pydantic 模型
│   └── database.py                 # 数据库模型
│
└── utils/                           # 工具层
    ├── __init__.py
    ├── cold_start.py               # [NEW] 冷启动填充
    └── image_utils.py              # [NEW] 图像处理
```

### 5.2 核心服务设计

#### 5.2.1 TSMixerService

```python
# services/tsmixer_service.py

class TSMixerService:
    """TSMixer 灌水量预测服务"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.seq_length = 96  # 96 天历史窗口
        self.n_features = 11   # 11 维特征

    def load_model(self, model_path: str):
        """加载 PyTorch 模型"""
        pass

    def load_scaler(self, scaler_path: str):
        """加载 StandardScaler"""
        pass

    def predict(self, features: np.ndarray) -> float:
        """
        执行预测

        Args:
            features: shape (96, 11) 的输入数组

        Returns:
            预测的灌水量 (L/m²)
        """
        pass

    def build_input_sequence(
        self,
        env_data: dict,
        yolo_metrics: dict,
        historical_data: pd.DataFrame
    ) -> np.ndarray:
        """
        构建 96×11 输入序列

        11 个特征:
        1. temperature
        2. humidity
        3. light
        4. leaf Instance Count
        5. leaf average mask
        6. flower Instance Count
        7. flower Mask Pixel Count
        8. terminal average Mask Pixel Count
        9. fruit Mask average
        10. all leaf mask
        11. Target (历史灌水量)
        """
        pass
```

#### 5.2.2 PredictionService

```python
# services/prediction_service.py

class PredictionService:
    """预测流水线服务 - 整合 YOLO + TSMixer"""

    def __init__(
        self,
        yolo_service: YOLOService,
        tsmixer_service: TSMixerService,
        cold_start_data: pd.DataFrame
    ):
        self.yolo = yolo_service
        self.tsmixer = tsmixer_service
        self.cold_start_data = cold_start_data

    async def predict(
        self,
        image: UploadFile,
        env_data: EnvDataSchema
    ) -> PredictionResult:
        """
        完整预测流程:

        1. YOLO 分割 → 获取视觉指标
        2. 获取历史数据 (或冷启动填充)
        3. 构建 11 维特征向量
        4. TSMixer 预测
        5. 返回结果
        """
        pass

    def _fill_missing_days(
        self,
        historical_data: pd.DataFrame,
        target_date: str
    ) -> pd.DataFrame:
        """冷启动时用历史数据填充"""
        pass
```

#### 5.2.3 RAGService

```python
# services/rag_service.py

from pymilvus import Collection
from src.retriever.milvus_retriever import MilvusRetriever

class RAGService:
    """RAG 检索服务"""

    def __init__(self):
        self.retriever = MilvusRetriever(docs=None, retrieve=True)
        self.collection_name = "greenhouse_bge_m3"

    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """
        混合检索相关文档片段

        Args:
            query: 用户问题
            top_k: 返回数量

        Returns:
            相关文档列表
        """
        return self.retriever.retrieve_topk(query, top_k)

    def format_context(self, documents: List[Document]) -> str:
        """格式化检索结果为上下文"""
        pass
```

#### 5.2.4 LLMService

```python
# services/llm_service.py

from openai import AsyncOpenAI

class LLMService:
    """LLM 对话服务"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = """你是一个专业的温室农业专家助手。
        你擅长温室黄瓜种植、灌溉管理、病虫害防治等领域。
        请基于提供的知识库内容回答用户问题，并引用相关来源。
        如果知识库中没有相关信息，请诚实说明。"""

    async def generate(
        self,
        query: str,
        context: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        生成回答 (支持流式)

        Args:
            query: 用户问题
            context: RAG 检索的上下文
            stream: 是否流式返回
        """
        pass

    async def chat_stream(
        self,
        query: str,
        rag_service: RAGService
    ) -> AsyncGenerator[dict, None]:
        """
        完整问答流程 (RAG + LLM)

        Yields:
            {"type": "content", "data": "文本片段"}
            {"type": "sources", "data": [引用列表]}
            {"type": "done"}
        """
        pass
```

---

## 6. API 端点设计

### 6.1 API 端点总览

```
/api/v1/
├── /predict
│   └── POST /                      # 灌水量预测
│
├── /vision
│   ├── GET  /image/{date}          # 获取指定日期图像
│   ├── GET  /segmented/{date}      # 获取分割后图像
│   ├── GET  /metrics/{date}        # 获取 YOLO 指标
│   └── POST /segment               # 实时分割 (上传图片)
│
├── /chat
│   ├── POST /                      # 发送消息 (非流式)
│   ├── GET  /stream                # 流式对话 (SSE)
│   └── GET  /history               # 获取对话历史
│
├── /upload
│   ├── POST /image                 # 上传图片
│   └── POST /env                   # 上传环境数据 (CSV)
│
├── /episodes
│   ├── GET  /                      # 获取决策列表
│   ├── GET  /latest                # 获取最新决策
│   └── GET  /{episode_id}          # 获取决策详情
│
├── /override
│   └── POST /{episode_id}          # 覆盖决策
│
├── /stats
│   └── GET  /dashboard             # 仪表盘统计
│
├── /weekly
│   └── GET  /                      # 周报数据
│
└── /knowledge
    └── GET  /search                # 知识检索
```

### 6.2 核心 API 详细设计

#### 6.2.1 预测 API

```python
# POST /api/v1/predict

# Request (multipart/form-data)
{
    "image": File,              # 温室图片
    "temperature": 25.5,        # 日均温度 (°C)
    "humidity": 75.0,           # 日均湿度 (%)
    "light": 45000,             # 日均光照 (lux)
    "date": "2024-06-15"        # 预测日期
}

# Response
{
    "success": true,
    "data": {
        "irrigation_amount": 5.23,          # 预测灌水量 (L/m²)
        "confidence": 0.92,                 # 置信度
        "model_version": "tsmixer_v1.0",
        "predicted_at": "2024-06-14T15:30:00Z",
        "yolo_metrics": {
            "leaf_count": 12,
            "leaf_avg_mask": 1250.5,
            "flower_count": 5,
            "flower_avg_mask": 320.2,
            "fruit_count": 3,
            "fruit_avg_mask": 580.8,
            "terminal_avg_mask": 450.0
        },
        "segmented_image_url": "/api/v1/vision/segmented/0614",
        "input_features": {
            "env_data": { ... },
            "historical_days_used": 96,
            "cold_start_filled": 45
        }
    }
}
```

#### 6.2.2 视觉分析 API

```python
# GET /api/v1/vision/metrics/{date}

# Response
{
    "success": true,
    "data": {
        "date": "2024-06-14",
        "metrics": {
            "leaf_instance_count": 12,
            "leaf_average_mask": 1250.5,
            "flower_instance_count": 5,
            "flower_average_mask": 320.2,
            "fruit_instance_count": 3,
            "fruit_average_mask": 580.8,
            "terminal_average_mask": 450.0,
            "all_leaf_mask": 15006.0
        },
        "comparison": {
            "yesterday": {
                "date": "2024-06-13",
                "leaf_change": +2,
                "flower_change": -1,
                "fruit_change": +1
            }
        },
        "original_image_url": "/api/v1/vision/image/0614",
        "segmented_image_url": "/api/v1/vision/segmented/0614"
    }
}
```

#### 6.2.3 聊天 API (SSE 流式)

```python
# GET /api/v1/chat/stream?query=xxx

# SSE Events
event: content
data: {"text": "根据"}

event: content
data: {"text": "FAO56文献"}

event: content
data: {"text": "的记载..."}

event: sources
data: {"sources": [
    {"title": "FAO56 Chapter 8", "page": 123},
    {"title": "温室黄瓜栽培技术", "page": 45}
]}

event: done
data: {}
```

### 6.3 数据模型 (Pydantic Schemas)

```python
# models/schemas.py

class EnvDataInput(BaseModel):
    temperature: float = Field(..., ge=10, le=45, description="日均温度 (°C)")
    humidity: float = Field(..., ge=20, le=100, description="日均湿度 (%)")
    light: float = Field(..., ge=0, le=150000, description="日均光照 (lux)")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")

class YOLOMetrics(BaseModel):
    leaf_instance_count: int
    leaf_average_mask: float
    flower_instance_count: int
    flower_average_mask: float
    fruit_instance_count: int
    fruit_average_mask: float
    terminal_average_mask: float
    all_leaf_mask: float
    processed_at: datetime

class PredictionResult(BaseModel):
    irrigation_amount: float
    confidence: float
    model_version: str
    predicted_at: datetime
    yolo_metrics: YOLOMetrics
    segmented_image_url: str

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    sources: Optional[List[Citation]] = None
    timestamp: datetime

class Citation(BaseModel):
    title: str
    page: Optional[int]
    chunk_id: str
    relevance_score: float
```

---

## 7. 依赖管理

### 7.1 前端依赖

```json
// package.json

{
  "dependencies": {
    // 核心框架
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",

    // 状态管理
    "@tanstack/react-query": "^5.60.0",
    "zustand": "^5.0.0",

    // UI 组件
    "tailwindcss": "^3.4.0",
    "@phosphor-icons/react": "^2.1.0",
    "react-hot-toast": "^2.4.0",
    "react-dropzone": "^14.2.0",      // [NEW] 文件上传

    // 图表
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",

    // HTTP 客户端
    "axios": "^1.7.0",

    // 工具
    "date-fns": "^3.6.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    // 构建工具
    "vite": "^7.3.0",
    "typescript": "^5.7.0",

    // 代码规范
    "eslint": "^9.17.0",
    "prettier": "^3.4.0",
    "@typescript-eslint/parser": "^8.0.0"
  }
}
```

### 7.2 后端依赖

```toml
# pyproject.toml

[project]
dependencies = [
    # Web 框架
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "python-multipart>=0.0.18",       # 文件上传
    "sse-starlette>=2.0.0",           # SSE 流式

    # 数据处理
    "pandas>=2.2.0",
    "numpy>=1.26.0",

    # ML 模型
    "torch>=2.5.0",
    "ultralytics>=8.3.0",             # YOLO

    # 向量检索 (RAG)
    "pymilvus>=2.4.0",
    "langchain-core>=0.3.0",

    # LLM
    "openai>=1.50.0",

    # 数据库
    "pymongo>=4.9.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.30.0",

    # 嵌入模型
    "FlagEmbedding>=1.2.0",           # BGE-M3

    # 工具
    "pydantic>=2.10.0",
    "python-dotenv>=1.0.0",
    "pillow>=10.4.0",
    "opencv-python>=4.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]
```

### 7.3 模型文件管理

```
models/
├── yolo/
│   └── yolo11_seg_best.pt          # 复制自 v11_4seg 项目
│
├── tsmixer/
│   ├── model.pt                    # 复制自 Irrigation 项目
│   └── scaler.pkl                  # StandardScaler 参数
│
└── embeddings/
    └── bge-m3/                     # BGE-M3 本地模型 (可选)
```

### 7.4 环境变量配置

```bash
# .env

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 模型路径
YOLO_MODEL_PATH=./models/yolo/yolo11_seg_best.pt
TSMIXER_MODEL_PATH=./models/tsmixer/model.pt

# 数据库
POSTGRES_URL=postgresql://user:pass@localhost:5432/agriagent
MONGODB_URI=mongodb://localhost:27017/greenhouse_db
MILVUS_URI=./milvus_lite.db

# OpenAI
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo

# 路径
IMAGES_DIR=./data/images
OUTPUT_DIR=./output
COLD_START_CSV=./data/csv/irrigation_pre.csv
```

---

## 8. 实现优先级

### 8.1 Phase 1: 核心功能 (P0)

| 任务 | 涉及文件 | 依赖 |
|------|----------|------|
| TSMixerService 实现 | `services/tsmixer_service.py` | torch, model.pt |
| YOLOService 完善 | `services/yolo_service.py` | ultralytics, best.pt |
| PredictionService 实现 | `services/prediction_service.py` | TSMixer, YOLO |
| 预测 API | `api/v1/predict.py` | PredictionService |
| ImageUpload 组件 | `components/prediction/ImageUpload.tsx` | react-dropzone |
| EnvDataForm 组件 | `components/prediction/EnvDataForm.tsx` | - |
| PredictionPanel 组件 | `components/prediction/PredictionPanel.tsx` | - |
| Predict 页面 | `pages/Predict.tsx` | 上述组件 |

### 8.2 Phase 2: RAG 问答 (P0)

| 任务 | 涉及文件 | 依赖 |
|------|----------|------|
| RAGService 实现 | `services/rag_service.py` | pymilvus, Greenhouse_RAG |
| LLMService 实现 | `services/llm_service.py` | openai |
| Chat API (SSE) | `api/v1/chat.py` | sse-starlette |
| ChatPanel 组件 | `components/layout/Sidebar/ChatPanel.tsx` | - |
| ChatMessage 组件 | `components/chat/ChatMessage.tsx` | - |
| StreamingText 组件 | `components/chat/StreamingText.tsx` | - |

### 8.3 Phase 3: 视觉展示 (P1)

| 任务 | 涉及文件 | 依赖 |
|------|----------|------|
| Vision API | `api/v1/vision.py` | YOLOService |
| ImageViewer 组件 | `components/vision/ImageViewer.tsx` | - |
| ImageComparison 组件 | `components/vision/ImageComparison.tsx` | - |
| MetricsDisplay 组件 | `components/vision/MetricsDisplay.tsx` | - |
| Vision 页面 | `pages/Vision.tsx` | 上述组件 |

---

## 9. 附录

### 9.1 TSMixer 输入特征说明

| 序号 | 特征名 | 来源 | 单位/说明 |
|------|--------|------|----------|
| 1 | temperature | 用户输入 | °C |
| 2 | humidity | 用户输入 | % |
| 3 | light | 用户输入 | lux |
| 4 | leaf Instance Count | YOLO | 整数 |
| 5 | leaf average mask | YOLO | 像素数 |
| 6 | flower Instance Count | YOLO | 整数 |
| 7 | flower Mask Pixel Count | YOLO | 像素数 |
| 8 | terminal average Mask Pixel Count | YOLO | 像素数 |
| 9 | fruit Mask average | YOLO | 像素数 |
| 10 | all leaf mask | YOLO | 像素数 (总面积) |
| 11 | Target | 历史数据 | L/m² (历史灌水量) |

### 9.2 YOLO 类别映射

| 类别 ID | 类别名 | 颜色 (BGR) | 说明 |
|---------|--------|------------|------|
| 0 | leaf | (0, 255, 0) 绿 | 叶片 |
| 1 | flower | (0, 255, 255) 黄 | 花朵 |
| 2 | fruit | (0, 0, 255) 红 | 果实 |
| 3 | terminal | (255, 0, 255) 紫 | 顶芽 |

### 9.3 冷启动填充逻辑

```python
def fill_cold_start(
    historical_data: pd.DataFrame,
    cold_start_csv: str,
    target_date: str
) -> pd.DataFrame:
    """
    当历史数据不足 96 天时，使用 irrigation_pre.csv 填充

    填充规则:
    1. 优先使用已有的真实数据
    2. 缺失日期按月日匹配 (如 6月14日 匹配去年 6月14日)
    3. 如果月日也没有，使用相邻日期平均值
    """
    pass
```

---

<div align="center">

**文档版本**: v1.0
**创建日期**: 2025-12-27
**维护者**: AgriAgent Development Team

</div>
