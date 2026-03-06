# AgriAgent 技术说明与 Docker 部署指南

## 1. 项目定位

AgriAgent 是一个面向温室黄瓜场景的多模态智能灌溉决策系统。它把图像识别、时序预测、知识检索和大模型推理串联成一条完整的日常决策链。

核心目标有三点：

1. 根据环境数据和植株图像，自动给出灌水建议。
2. 把每天的决策、证据、异常和人工干预沉淀下来，便于追溯。
3. 通过周报和知识库，让系统具备持续复盘与解释能力。

## 2. 系统演示

### 2.1 Dashboard

![Dashboard](assets/screenshots/dashboard.png)

### 2.2 灌水预测页

![Predict](assets/screenshots/predict.png)

### 2.3 视觉分析页

![Vision](assets/screenshots/vision.png)

### 2.4 智能问答页

![Knowledge](assets/screenshots/knowledge.png)

## 3. 总体架构

系统由四层组成：

1. 前端层：React + Vite，提供仪表板、预测、视觉分析、历史、知识问答和设置页面。
2. API 层：FastAPI，对外暴露预测、视觉分析、周报、知识问答、上传、设置、记忆等接口。
3. 算法与服务层：YOLO、TSMixer、LLM、RAG、本地记忆服务。
4. 数据层：本地图像、知识库 JSON、每日 episode、周报 summary、模型权重和输出结果。

典型数据流如下：

```text
环境数据 + 温室图像
        ↓
YOLO 实例分割提取植株特征
        ↓
TSMixer 基于历史窗口预测灌水量
        ↓
LLM 结合图像/指标/环境/RAG 做长势分析与合理性复核
        ↓
输出最终灌水建议
        ↓
写入 episode / weekly summary / output
```

## 4. 目录与模块说明

### 4.1 根目录

- `README.md`
  项目总览与快速说明。
- `docker-compose.yml`
  一键启动前后端服务。
- `.env.example`
  运行时环境变量模板。
- `config.ini`
  示例配置，不应存放真实密钥。

### 4.2 `frontend/`

前端采用 React + TypeScript + Vite。

关键模块：

- `frontend/src/pages/Dashboard.tsx`
  首页驾驶舱，展示当前灌溉建议、环境摘要和趋势图。
- `frontend/src/pages/Predict.tsx`
  手动输入环境数据和图像，触发一次灌水预测。
- `frontend/src/pages/Vision.tsx`
  上传图像，调用 YOLO 视觉分析接口并展示结果。
- `frontend/src/pages/Knowledge.tsx`
  基于 RAG 的农业智能问答页。
- `frontend/src/pages/History.tsx`
  查看历史 episode 与趋势统计。
- `frontend/src/pages/Settings.tsx`
  配置 LLM 参数和系统选项。
- `frontend/src/services/`
  封装 Axios 请求，连接后端 API。
- `frontend/nginx.conf`
  Docker 部署时由 Nginx 托管静态资源，并反代 `/api` 和 `/static` 到后端。

### 4.3 `backend/`

后端采用 FastAPI，负责对外 API 和运行时服务编排。

关键模块：

- `backend/app/main.py`
  FastAPI 入口，注册所有路由并挂载静态资源。
- `backend/app/api/v1/predict.py`
  每日预测相关接口。
- `backend/app/api/v1/vision.py`
  视觉分析接口。
- `backend/app/api/v1/chat.py`
  智能问答与 SSE 流式输出接口。
- `backend/app/api/v1/knowledge.py`
  知识库查询与检索接口。
- `backend/app/api/v1/episodes.py`
  历史 episode 查询接口。
- `backend/app/api/v1/memory.py`
  记忆层查询接口。
- `backend/app/services/yolo_service.py`
  加载 YOLO 模型，完成图像分割和指标提取。
- `backend/app/services/tsmixer_service.py`
  加载 TSMixer 模型并进行灌溉量预测。
- `backend/app/services/llm_service.py`
  调用大模型完成对话、视觉理解、PlantResponse 和 SanityCheck。
- `backend/app/services/prediction_service.py`
  串联 YOLO、TSMixer、LLM、RAG 和记忆层，形成完整预测流程。
- `backend/app/services/memory_service.py`
  管理 episode / weekly summary 的 JSON 存储与读取。

### 4.4 `src/`

这里是更通用的 Python 核心包，偏离后端 Web 框架，适合离线批处理和可复用逻辑。

- `src/run_daily.py`
  每日 pipeline 入口。
- `src/run_weekly.py`
  周报 pipeline 入口。
- `src/yolo_batch.py`
  批量运行 YOLO。
- `src/tsmixer_batch.py`
  批量运行 TSMixer。
- `src/cucumber_irrigation/rag/`
  本地知识库切块、索引、检索逻辑。
- `src/cucumber_irrigation/memory/`
  episode 与 weekly summary 的存储模型。

### 4.5 `data/`

- `data/images/`
  原始图像样本。
- `data/knowledge_base/fao56_chunks.json`
  已切块的农业知识库。
- `data/storage/`
  运行中产生的 episode / weekly summary JSON。
- `data/coldstart/` 和 `data/csv/`
  TSMixer 冷启动和输入数据。

### 4.6 `models/`

- `models/yolo/yolo11_seg_best.pt`
  黄瓜实例分割模型权重。
- `models/tsmixer/model_state.pt`
  灌溉预测模型权重。

## 5. Docker 部署说明

### 5.1 前置条件

请先确保本机满足以下条件：

1. 已安装 Docker Desktop。
2. Docker Desktop 处于 `running` 状态。
3. 项目目录中存在 `models/` 和 `data/knowledge_base/` 等必需资源。
4. 你已经准备好自己的 LLM API Key。

### 5.2 模型与知识库准备

公开仓库默认不会包含大模型权重文件，因此在自己的电脑上部署前，需要先把必需资源放到约定目录中：

- `models/yolo/yolo11_seg_best.pt`
  YOLO 黄瓜实例分割权重。
- `models/tsmixer/model.pt`
  TSMixer 灌溉预测权重。
- `data/knowledge_base/fao56_chunks.json`
  已切块的农业知识库。

如果你是从 GitHub 仓库直接克隆项目，这一步通常需要你把本地已有模型文件手动复制到上述位置。

### 5.3 环境变量配置

项目根目录提供了 `.env.example`。第一次部署时建议复制一份为 `.env`：

```bash
copy .env.example .env
```

或在 PowerShell 中执行：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，至少填写：

```env
LLM_API_KEY=your_real_api_key
LLM_BASE_URL=https://yunwu.ai/v1
LLM_MODEL=gpt-5.2-chat-latest
VITE_API_BASE_URL=/api
```

后端同时兼容 `LLM_API_KEY` / `OPENAI_API_KEY` 这两套命名，但建议统一使用 `.env.example` 中的 `LLM_*` 变量。

### 5.4 构建并启动

在项目根目录运行：

```bash
docker compose up -d --build
```

如果镜像已经构建过，只需要：

```bash
docker compose up -d
```

后端镜像会在容器内自动创建 `/app/output`，因此首次从 GitHub 拉取仓库时，不要求仓库内自带 `output/` 目录。

### 5.5 启动后访问地址

- 前端页面：`http://localhost:3003`
- 后端 API：`http://localhost:8000`
- 后端文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

### 5.6 常用 Docker 命令

查看服务状态：

```bash
docker compose ps
```

查看后端日志：

```bash
docker compose logs -f backend
```

查看前端日志：

```bash
docker compose logs -f frontend
```

停止服务：

```bash
docker compose down
```

重新构建后端：

```bash
docker compose build backend
```

### 5.7 Docker 服务说明

#### `backend`

- 基于 `python:3.11-slim`
- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port 8000`
- 挂载：
  - `./data:/app/data`
  - `./output:/app/output`
- 负责加载模型、知识库和对外 API

#### `frontend`

- 基于 `node:24-alpine` 构建，`nginx:alpine` 运行
- 使用 Vite 构建静态资源
- Nginx 负责：
  - 提供前端页面
  - 把 `/api/*` 反代到 `backend:8000`
  - 把 `/static/*` 反代到后端静态资源

## 6. 在自己电脑上首次部署的建议流程

推荐按下面顺序执行：

1. 克隆或下载项目到本地。
2. 确认 `models/`、`data/knowledge_base/` 等资源存在。
3. 复制 `.env.example` 为 `.env` 并填写 API Key。
4. 执行 `docker compose up -d --build`。
5. 打开 `http://localhost:3003` 验证前端。
6. 打开 `http://localhost:8000/docs` 验证后端。

## 7. 关键接口说明

常用接口包括：

- `GET /api/health`
  系统健康检查。
- `POST /api/predict/daily`
  执行一次每日预测。
- `POST /api/vision/analyze`
  上传图片并进行视觉分析。
- `GET /api/episodes`
  查询历史决策记录。
- `GET /api/knowledge/search`
  知识库检索。
- `GET /api/chat/stream`
  智能问答流式输出。

## 8. 运行时数据去向

系统运行后，典型输出会落在：

- `data/storage/`
  记忆层 JSON 数据。
- `output/segmented_images/`
  YOLO 分割后的结果图。
- `output/yolo_metrics/`
  图像指标结果。
- `output/responses/`
  LLM 生成响应与相关输出。

这些目录属于运行产物，不建议作为 Git 仓库长期跟踪。

## 9. 已知注意事项

1. 后端镜像体积较大。
   原因是 `torch`/`ultralytics` 会拉入较多依赖。
2. 当前 Docker 后端仍使用 CPU 推理。
   如需 GPU，需要进一步为本机 Docker/NVIDIA Runtime 做专项适配。
3. `config.ini` 只保留示例配置。
   真正运行时建议统一通过 `.env` 注入密钥。

## 10. 对外发布建议

如果你要把这个项目公开到 GitHub，建议保留这些文件：

- 源码：`src/`、`backend/`、`frontend/`
- 文档：`README.md`、`docs/TECHNICAL_GUIDE.md`
- 部署文件：`Dockerfile`、`docker-compose.yml`、`.env.example`
- 轻量级示例数据和截图

建议忽略这些内容：

- 本地虚拟环境
- `node_modules`
- `dist`
- `output`
- MongoDB 二进制与数据库目录
- 私密密钥文件
