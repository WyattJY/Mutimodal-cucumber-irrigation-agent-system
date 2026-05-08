# `backend/app/api/v1` 目录说明

## 目录定位
后端 v1 API：Episodes/预测/周报/对话/上传/知识库/记忆等端点。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `chat.py`
- `episodes.py`
- `knowledge.py`
- `memory.py`
- `override.py`
- `predict.py`
- `settings.py`
- `stats.py`
- `upload.py`
- `vision.py`
- `weekly.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `backend/app/api/v1/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/app/api/__init__.py`

**引用了谁（外部依赖）**
- `__future__`

### `chat.py`
- 作用/意义: 智能问答 API
- 路径: `backend/app/api/v1/chat.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/core/config.py`
- `backend/app/services/episode_service.py`
- `backend/app/services/llm_service.py`
- `src/cucumber_irrigation/services/local_rag_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `fastapi`
- `json`
- `openai`
- `pathlib`
- `pydantic`
- `sse_starlette`
- `sys`
- `typing`

### `episodes.py`
- 作用/意义: 创建统一响应格式
- 路径: `backend/app/api/v1/episodes.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/services/episode_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `fastapi`
- `typing`

### `knowledge.py`
- 作用/意义: 知识库 API
- 路径: `backend/app/api/v1/knowledge.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`
- `src/cucumber_irrigation/rag/json_store.py`
- `src/cucumber_irrigation/services/local_rag_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `fastapi`
- `pathlib`
- `pydantic`
- `sys`
- `typing`

### `memory.py`
- 作用/意义: 记忆系统 API
- 路径: `backend/app/api/v1/memory.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/services/episode_service.py`
- `backend/app/services/memory_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `fastapi`
- `json`
- `pathlib`
- `typing`

### `override.py`
- 作用/意义: 创建统一响应格式
- 路径: `backend/app/api/v1/override.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/services/episode_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### `predict.py`
- 作用/意义: 预测 API
- 路径: `backend/app/api/v1/predict.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/tsmixer_service.py`
- `backend/app/services/yolo_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `base64`
- `datetime`
- `fastapi`
- `json`
- `pydantic`
- `typing`

### `settings.py`
- 作用/意义: 配置管理 API
- 路径: `backend/app/api/v1/settings.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/core/config.py`
- `backend/app/services/llm_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `fastapi`
- `pydantic`
- `typing`

### `stats.py`
- 作用/意义: 创建统一响应格式
- 路径: `backend/app/api/v1/stats.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/services/episode_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `fastapi`

### `upload.py`
- 作用/意义: 数据上传 API - 环境数据上传 (CSV) - 图像上传 - YOLO 处理触发
- 路径: `backend/app/api/v1/upload.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/services/yolo_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `csv`
- `datetime`
- `fastapi`
- `json`
- `os`
- `pathlib`
- `shutil`
- `typing`

### `vision.py`
- 作用/意义: 视觉分析 API - 图像上传与分割 - 指标提取 - 可视化结果获取
- 路径: `backend/app/api/v1/vision.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/services/yolo_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `base64`
- `datetime`
- `fastapi`
- `io`
- `pathlib`
- `typing`

### `weekly.py`
- 作用/意义: 周报 API
- 路径: `backend/app/api/v1/weekly.py`

**被谁引用/调用（代码级）**
- `backend/app/main.py`

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/weekly_summary_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `fastapi`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/main.py`

**本目录引用了谁（跨目录）**
- `backend/app/api/__init__.py`
- `backend/app/core/config.py`
- `backend/app/models/schemas.py`
- `backend/app/services/episode_service.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/tsmixer_service.py`
- `backend/app/services/weekly_summary_service.py`
- `backend/app/services/yolo_service.py`
- `src/cucumber_irrigation/rag/json_store.py`
- `src/cucumber_irrigation/services/local_rag_service.py`
