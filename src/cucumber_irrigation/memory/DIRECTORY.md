# `src/cucumber_irrigation/memory` 目录说明

## 目录定位
4层记忆架构实现：L1 WorkingContext + Rule-M1 预算控制、L2 EpisodeStore、L3 WeeklySummaryStore、L4 KnowledgeRetriever。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `budget_controller.py`
- `episode_store.py`
- `knowledge_retriever.py`
- `weekly_summary_store.py`
- `working_context.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 记忆架构组件
- 路径: `src/cucumber_irrigation/memory/__init__.py`

**被谁引用/调用（代码级）**
- `scripts/demo_weekly_llm.py`
- `scripts/load_real_data.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `src/cucumber_irrigation/pipelines/weekly_pipeline.py`
- `tests/test_acceptance.py`
- `tests/test_integration.py`
- `tests/test_memory.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

**引用了谁（外部依赖）**
- `__future__`

### `budget_controller.py`
- 作用/意义: Rule-M1 上下文预算控制器
- 路径: `src/cucumber_irrigation/memory/budget_controller.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/memory/working_context.py`
- `src/cucumber_irrigation/services/llm_service.py`
- `tests/test_acceptance.py`
- `tests/test_memory.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/utils/token_counter.py`

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `json`
- `typing`

### `episode_store.py`
- 作用/意义: L2 Episodic Log 存储
- 路径: `src/cucumber_irrigation/memory/episode_store.py`

**被谁引用/调用（代码级）**
- `backend/app/services/memory_service.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/episode.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `json`
- `os`
- `typing`

### `knowledge_retriever.py`
- 作用/意义: L4 知识检索器
- 路径: `src/cucumber_irrigation/memory/knowledge_retriever.py`

**被谁引用/调用（代码级）**
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/services/rag_service.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/anomaly.py`

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `os`
- `pymilvus`
- `typing`

### `weekly_summary_store.py`
- 作用/意义: L3 周摘要存储
- 路径: `src/cucumber_irrigation/memory/weekly_summary_store.py`

**被谁引用/调用（代码级）**
- `backend/app/services/memory_service.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/weekly_summary.py`
- `src/cucumber_irrigation/utils/token_counter.py`

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `json`
- `os`
- `typing`

### `working_context.py`
- 作用/意义: L1 工作上下文构建器
- 路径: `src/cucumber_irrigation/memory/working_context.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/budget_controller.py`

**引用了谁（外部依赖）**
- `__future__`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/services/memory_service.py`
- `scripts/demo_weekly_llm.py`
- `scripts/load_real_data.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `src/cucumber_irrigation/pipelines/weekly_pipeline.py`
- `src/cucumber_irrigation/services/llm_service.py`
- `src/cucumber_irrigation/services/rag_service.py`
- `tests/test_acceptance.py`
- `tests/test_integration.py`
- `tests/test_memory.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
- `src/cucumber_irrigation/models/anomaly.py`
- `src/cucumber_irrigation/models/episode.py`
- `src/cucumber_irrigation/models/weekly_summary.py`
- `src/cucumber_irrigation/utils/token_counter.py`
