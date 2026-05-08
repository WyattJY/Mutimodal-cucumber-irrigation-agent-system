# `backend/app/models` 目录说明

## 目录定位
后端 Pydantic 数据模型：定义请求/响应结构与枚举（用于 API 契约与前后端对齐）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `schemas.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `backend/app/models/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`

### `schemas.py`
- 作用/意义: 数据模型定义
- 路径: `backend/app/models/schemas.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/predict.py`
- `backend/app/api/v1/weekly.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/weekly_summary_service.py`
- `backend/tests/test_memory.py`
- `backend/tests/test_predict.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `datetime`
- `enum`
- `pydantic`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/predict.py`
- `backend/app/api/v1/weekly.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/weekly_summary_service.py`
- `backend/tests/test_memory.py`
- `backend/tests/test_predict.py`

**本目录引用了谁（跨目录）**
（无）
