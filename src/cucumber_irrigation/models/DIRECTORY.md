# `src/cucumber_irrigation/models` 目录说明

## 目录定位
数据模型层：Episode/WeeklySummary/PlantResponse/EnvInput/Anomaly 等结构化对象。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `anomaly.py`
- `env_input.py`
- `episode.py`
- `plant_response.py`
- `weekly_summary.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 数据模型
- 路径: `src/cucumber_irrigation/models/__init__.py`

**被谁引用/调用（代码级）**
- `scripts/demo_weekly_llm.py`
- `scripts/load_real_data.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/core/anomaly_detector.py`
- `src/cucumber_irrigation/core/env_input_handler.py`
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `src/cucumber_irrigation/pipelines/weekly_pipeline.py`
- `tests/conftest.py`
- `tests/test_acceptance.py`
- `tests/test_core.py`
- （还有 2 项未展开）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

**引用了谁（外部依赖）**
- `__future__`

### `anomaly.py`
- 作用/意义: 异常检测和RAG结果数据模型
- 路径: `src/cucumber_irrigation/models/anomaly.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/memory/knowledge_retriever.py`
- `src/cucumber_irrigation/services/local_rag_service.py`
- `src/cucumber_irrigation/services/rag_service.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `enum`
- `json`
- `typing`

### `env_input.py`
- 作用/意义: 环境输入数据模型
- 路径: `src/cucumber_irrigation/models/env_input.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `datetime`
- `json`
- `typing`

### `episode.py`
- 作用/意义: Episode 数据模型
- 路径: `src/cucumber_irrigation/models/episode.py`

**被谁引用/调用（代码级）**
- `backend/app/services/memory_service.py`
- `backend/app/services/prediction_service.py`
- `src/cucumber_irrigation/memory/episode_store.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `datetime`
- `json`
- `typing`

### `plant_response.py`
- 作用/意义: PlantResponse 数据模型
- 路径: `src/cucumber_irrigation/models/plant_response.py`

**被谁引用/调用（代码级）**
- `scripts/generate_responses.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `enum`
- `json`
- `re`
- `typing`

### `weekly_summary.py`
- 作用/意义: WeeklySummary 数据模型
- 路径: `src/cucumber_irrigation/models/weekly_summary.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/memory/weekly_summary_store.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `datetime`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/services/memory_service.py`
- `backend/app/services/prediction_service.py`
- `scripts/demo_weekly_llm.py`
- `scripts/generate_responses.py`
- `scripts/load_real_data.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/core/anomaly_detector.py`
- `src/cucumber_irrigation/core/env_input_handler.py`
- `src/cucumber_irrigation/memory/episode_store.py`
- `src/cucumber_irrigation/memory/knowledge_retriever.py`
- `src/cucumber_irrigation/memory/weekly_summary_store.py`
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- （还有 8 项未展开）

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
