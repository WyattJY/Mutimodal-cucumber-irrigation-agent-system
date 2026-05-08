# `scripts` 目录说明

## 目录定位
脚本目录：数据处理、批量生成、周报演示、索引重建、数据库测试等（多为离线/运维工具）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `build_pairs.py`
- `calc_growth_stats.py`
- `demo_weekly_llm.py`
- `download_mongodb.bat`
- `download_mongodb.ps1`
- `generate_responses.py`
- `load_real_data.py`
- `rebuild_milvus_index.py`
- `run_weekly_real.py`
- `start_mongo.ps1`
- `start_mongodb.bat`
- `start_mongodb.cmd`
- `test_databases.py`

## 脚本/模块说明（本目录内）
### `build_pairs.py`
- 作用/意义: 构建日期配对索引脚本
- 路径: `scripts/build_pairs.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/config.py`
- `src/cucumber_irrigation/processors/pairs_builder.py`

**引用了谁（外部依赖）**
- `loguru`
- `pathlib`
- `sys`
- `typer`

### `calc_growth_stats.py`
- 作用/意义: 计算增长率统计脚本
- 路径: `scripts/calc_growth_stats.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/config.py`
- `src/cucumber_irrigation/processors/stats_calculator.py`

**引用了谁（外部依赖）**
- `loguru`
- `pathlib`
- `sys`
- `typer`

### `demo_weekly_llm.py`
- 作用/意义: Demo WeeklyPipeline calling LLM to generate key_insights
- 路径: `scripts/demo_weekly_llm.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/pipelines/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`

**引用了谁（外部依赖）**
- `datetime`
- `dotenv`
- `os`
- `pathlib`
- `sys`

### `download_mongodb.bat`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `scripts/download_mongodb.bat`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `scripts/start_mongodb.bat`

### `download_mongodb.ps1`
- 作用/意义: MongoDB Windows 下载脚本 PowerShell 版本
- 路径: `scripts/download_mongodb.ps1`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `generate_responses.py`
- 作用/意义: 批量生成 PlantResponse 脚本
- 路径: `scripts/generate_responses.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/config.py`
- `src/cucumber_irrigation/models/plant_response.py`
- `src/cucumber_irrigation/services/image_service.py`
- `src/cucumber_irrigation/services/llm_service.py`
- `src/cucumber_irrigation/utils/prompt_builder.py`

**引用了谁（外部依赖）**
- `concurrent`
- `datetime`
- `json`
- `loguru`
- `pathlib`
- `sys`
- `threading`
- `tqdm`
- `typer`
- `typing`

### `load_real_data.py`
- 作用/意义: 从真实数据加载 Episodes
- 路径: `scripts/load_real_data.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`

**引用了谁（外部依赖）**
- `datetime`
- `json`
- `os`
- `pathlib`
- `sys`

### `rebuild_milvus_index.py`
- 作用/意义: 重建 Milvus 向量索引
- 路径: `scripts/rebuild_milvus_index.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `pathlib`
- `pymilvus`
- `pymongo`
- `sys`

### `run_weekly_real.py`
- 作用/意义: 使用真实数据运行 WeeklyPipeline
- 路径: `scripts/run_weekly_real.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/memory/knowledge_retriever.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/pipelines/__init__.py`
- `src/cucumber_irrigation/rag/json_store.py`
- `src/cucumber_irrigation/services/__init__.py`

**引用了谁（外部依赖）**
- `datetime`
- `dotenv`
- `json`
- `os`
- `pathlib`
- `sys`
- `traceback`

### `start_mongo.ps1`
- 作用/意义: Start MongoDB
- 路径: `scripts/start_mongo.ps1`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `start_mongodb.bat`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `scripts/start_mongodb.bat`

**被谁引用/调用（代码级）**
- `scripts/download_mongodb.bat`

**引用了谁（内部依赖）**
（无）

### `start_mongodb.cmd`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `scripts/start_mongodb.cmd`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `test_databases.py`
- 作用/意义: 测试 MongoDB 和 Milvus 连接
- 路径: `scripts/test_databases.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `pathlib`
- `pymilvus`
- `pymongo`
- `sys`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/config.py`
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/memory/knowledge_retriever.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/models/plant_response.py`
- `src/cucumber_irrigation/pipelines/__init__.py`
- `src/cucumber_irrigation/processors/pairs_builder.py`
- `src/cucumber_irrigation/processors/stats_calculator.py`
- `src/cucumber_irrigation/rag/json_store.py`
- `src/cucumber_irrigation/services/__init__.py`
- `src/cucumber_irrigation/services/image_service.py`
- `src/cucumber_irrigation/services/llm_service.py`
- （还有 1 项未展开）
