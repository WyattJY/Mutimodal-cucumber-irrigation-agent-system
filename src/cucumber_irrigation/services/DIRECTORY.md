# `src/cucumber_irrigation/services` 目录说明

## 目录定位
服务封装层：TSMixer 推理、LLM 调用、RAG 检索、DB 连接、图像处理等。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `db_service.py`
- `image_service.py`
- `llm_service.py`
- `local_rag_service.py`
- `rag_service.py`
- `tsmixer_service.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 服务层
- 路径: `src/cucumber_irrigation/services/__init__.py`

**被谁引用/调用（代码级）**
- `scripts/demo_weekly_llm.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `src/cucumber_irrigation/pipelines/weekly_pipeline.py`
- `tests/test_acceptance.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

### `db_service.py`
- 作用/意义: 数据库服务
- 路径: `src/cucumber_irrigation/services/db_service.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `loguru`
- `pymongo`
- `typing`

### `image_service.py`
- 作用/意义: 图像处理服务
- 路径: `src/cucumber_irrigation/services/image_service.py`

**被谁引用/调用（代码级）**
- `scripts/generate_responses.py`
- `src/cucumber_irrigation/services/llm_service.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `base64`
- `pathlib`

### `llm_service.py`
- 作用/意义: LLM 调用服务
- 路径: `src/cucumber_irrigation/services/llm_service.py`

**被谁引用/调用（代码级）**
- `backend/app/services/weekly_summary_service.py`
- `scripts/generate_responses.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/services/image_service.py`

**引用了谁（外部依赖）**
- `__future__`
- `json`
- `loguru`
- `openai`
- `time`
- `typing`

### `local_rag_service.py`
- 作用/意义: 本地 RAG 服务
- 路径: `src/cucumber_irrigation/services/local_rag_service.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/services/prediction_service.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/anomaly.py`
- `src/cucumber_irrigation/rag/json_store.py`

**引用了谁（外部依赖）**
- `dataclasses`
- `loguru`
- `typing`

### `rag_service.py`
- 作用/意义: RAG 检索服务
- 路径: `src/cucumber_irrigation/services/rag_service.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/knowledge_retriever.py`
- `src/cucumber_irrigation/models/anomaly.py`

**引用了谁（外部依赖）**
- `typing`

### `tsmixer_service.py`
- 作用/意义: TSMixer 预测服务
- 路径: `src/cucumber_irrigation/services/tsmixer_service.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/core/window_builder.py`

**引用了谁（外部依赖）**
- `loguru`
- `numpy`
- `os`
- `pandas`
- `pathlib`
- `pickle`
- `sklearn`
- `torch`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/weekly_summary_service.py`
- `scripts/demo_weekly_llm.py`
- `scripts/generate_responses.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `src/cucumber_irrigation/pipelines/weekly_pipeline.py`
- `tests/test_acceptance.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
- `src/cucumber_irrigation/core/window_builder.py`
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/memory/knowledge_retriever.py`
- `src/cucumber_irrigation/models/anomaly.py`
- `src/cucumber_irrigation/rag/json_store.py`
