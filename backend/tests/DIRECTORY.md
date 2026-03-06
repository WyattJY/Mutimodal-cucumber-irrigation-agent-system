# `backend/tests` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `test_memory.py`
- `test_predict.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Backend Tests
- 路径: `backend/tests/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `test_memory.py`
- 作用/意义: Phase 2 集成测试 - 记忆系统
- 路径: `backend/tests/test_memory.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/rag_service.py`
- `backend/app/services/weekly_summary_service.py`

**引用了谁（外部依赖）**
- `asyncio`
- `datetime`
- `os`
- `pytest`
- `sys`
- `unittest`

### `test_predict.py`
- 作用/意义: Phase 1 集成测试 - 每日预测流程
- 路径: `backend/tests/test_predict.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/app/models/schemas.py`

**引用了谁（外部依赖）**
- `asyncio`
- `datetime`
- `os`
- `pytest`
- `sys`
- `unittest`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `backend/app/models/schemas.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/rag_service.py`
- `backend/app/services/weekly_summary_service.py`
