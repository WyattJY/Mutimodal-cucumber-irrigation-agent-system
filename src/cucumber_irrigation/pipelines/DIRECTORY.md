# `src/cucumber_irrigation/pipelines` 目录说明

## 目录定位
流程管道层：DailyPipeline（每日决策）与 WeeklyPipeline（周度总结/注入）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `daily_pipeline.py`
- `weekly_pipeline.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 流程管道
- 路径: `src/cucumber_irrigation/pipelines/__init__.py`

**被谁引用/调用（代码级）**
- `scripts/demo_weekly_llm.py`
- `scripts/run_weekly_real.py`
- `tests/test_integration.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

### `daily_pipeline.py`
- 作用/意义: 每日决策管道
- 路径: `src/cucumber_irrigation/pipelines/daily_pipeline.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/core/__init__.py`
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`

**引用了谁（外部依赖）**
- `dataclasses`
- `datetime`
- `loguru`
- `os`
- `pandas`
- `typing`

### `weekly_pipeline.py`
- 作用/意义: 每周总结管道
- 路径: `src/cucumber_irrigation/pipelines/weekly_pipeline.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`

**引用了谁（外部依赖）**
- `dataclasses`
- `datetime`
- `loguru`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `scripts/demo_weekly_llm.py`
- `scripts/run_weekly_real.py`
- `tests/test_integration.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
- `src/cucumber_irrigation/core/__init__.py`
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`
