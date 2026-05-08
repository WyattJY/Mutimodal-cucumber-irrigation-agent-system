# `backend/app/services` 目录说明

## 目录定位
后端服务层：编排每日预测（YOLO+TSMixer+LLM）、读写记忆、生成周报、提供数据查询与反馈。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `episode_service.py`
- `llm_service.py`
- `memory_service.py`
- `prediction_service.py`
- `rag_service.py`
- `tsmixer_service.py`
- `weekly_summary_service.py`
- `yolo_service.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `backend/app/services/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/app/__init__.py`

**引用了谁（外部依赖）**
- `__future__`

### `episode_service.py`
- 作用/意义: Episode 数据服务
- 路径: `backend/app/services/episode_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/episodes.py`
- `backend/app/api/v1/memory.py`
- `backend/app/api/v1/override.py`
- `backend/app/api/v1/stats.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `json`
- `loguru`
- `os`
- `pathlib`
- `typing`

### `llm_service.py`
- 作用/意义: LLM 对话服务 - 支持 GPT-4/GPT-5.2 等模型
- 路径: `backend/app/services/llm_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/settings.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/weekly_summary_service.py`

**引用了谁（内部依赖）**
- `backend/app/core/config.py`
- `backend/app/models/schemas.py`

**引用了谁（外部依赖）**
- `__future__`
- `base64`
- `json`
- `openai`
- `typing`

### `memory_service.py`
- 作用/意义: 记忆层统一封装
- 路径: `backend/app/services/memory_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/memory.py`
- `backend/app/api/v1/predict.py`
- `backend/app/api/v1/weekly.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/weekly_summary_service.py`
- `backend/tests/test_memory.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/episode_store.py`
- `src/cucumber_irrigation/memory/weekly_summary_store.py`
- `src/cucumber_irrigation/models/episode.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `json`
- `loguru`
- `os`
- `pathlib`
- `pymongo`
- `sys`
- `typing`

### `prediction_service.py`
- 作用/意义: 每日预测编排服务
- 路径: `backend/app/services/prediction_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/predict.py`

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/tsmixer_service.py`
- `backend/app/services/yolo_service.py`
- `src/cucumber_irrigation/models/episode.py`
- `src/cucumber_irrigation/services/local_rag_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `base64`
- `datetime`
- `json`
- `loguru`
- `os`
- `pathlib`
- `sys`
- `typing`

### `rag_service.py`
- 作用/意义: RAG (Retrieval-Augmented Generation) 知识检索服务 封装向量检索和知识增强功能
- 路径: `backend/app/services/rag_service.py`

**被谁引用/调用（代码级）**
- `backend/tests/test_memory.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `json`
- `logging`
- `os`
- `pathlib`
- `typing`

### `tsmixer_service.py`
- 作用/意义: TSMixer 时序预测服务 - 加载训练好的 TSMixer 模型 - 接收 96 天 × 11 特征的输入 - 预测下一天的灌水量
- 路径: `backend/app/services/tsmixer_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/predict.py`
- `backend/app/services/prediction_service.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `datetime`
- `numpy`
- `pandas`
- `pathlib`
- `random`
- `sys`
- `torch`
- `typing`

### `weekly_summary_service.py`
- 作用/意义: 周报生成服务
- 路径: `backend/app/services/weekly_summary_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/weekly.py`
- `backend/tests/test_memory.py`

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/memory_service.py`
- `src/cucumber_irrigation/services/llm_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `json`
- `loguru`
- `os`
- `pathlib`
- `typing`

### `yolo_service.py`
- 作用/意义: 分块推理: 缩放到3200x1920，切成15块，分别推理，拼接结果
- 路径: `backend/app/services/yolo_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/predict.py`
- `backend/app/api/v1/upload.py`
- `backend/app/api/v1/vision.py`
- `backend/app/services/prediction_service.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`

**引用了谁（外部依赖）**
- `__future__`
- `base64`
- `cv2`
- `datetime`
- `io`
- `json`
- `numpy`
- `os`
- `pathlib`
- `random`
- `sys`
- `torch`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/episodes.py`
- `backend/app/api/v1/memory.py`
- `backend/app/api/v1/override.py`
- `backend/app/api/v1/predict.py`
- `backend/app/api/v1/settings.py`
- `backend/app/api/v1/stats.py`
- `backend/app/api/v1/upload.py`
- `backend/app/api/v1/vision.py`
- `backend/app/api/v1/weekly.py`
- `backend/tests/test_memory.py`

**本目录引用了谁（跨目录）**
- `backend/app/__init__.py`
- `backend/app/core/config.py`
- `backend/app/models/schemas.py`
- `backend/ultralytics/__init__.py`
- `src/cucumber_irrigation/memory/episode_store.py`
- `src/cucumber_irrigation/memory/weekly_summary_store.py`
- `src/cucumber_irrigation/models/episode.py`
- `src/cucumber_irrigation/services/llm_service.py`
- `src/cucumber_irrigation/services/local_rag_service.py`
