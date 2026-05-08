# `src/cucumber_irrigation/core` 目录说明

## 目录定位
核心业务逻辑组件：环境输入处理、冷启动填充、时序窗口构建、异常检测、生育期判定等。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `anomaly_detector.py`
- `cold_start.py`
- `env_input_handler.py`
- `growth_stage_detector.py`
- `window_builder.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 核心业务组件
- 路径: `src/cucumber_irrigation/core/__init__.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `tests/test_acceptance.py`
- `tests/test_core.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

### `anomaly_detector.py`
- 作用/意义: 异常检测器
- 路径: `src/cucumber_irrigation/core/anomaly_detector.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/__init__.py`

**引用了谁（外部依赖）**
- `dataclasses`
- `typing`

### `cold_start.py`
- 作用/意义: 冷启动数据填充器
- 路径: `src/cucumber_irrigation/core/cold_start.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/core/window_builder.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `datetime`
- `numpy`
- `pandas`
- `pathlib`
- `typing`

### `env_input_handler.py`
- 作用/意义: 环境数据输入处理器
- 路径: `src/cucumber_irrigation/core/env_input_handler.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/__init__.py`

**引用了谁（外部依赖）**
- `datetime`
- `pandas`
- `pathlib`
- `typing`

### `growth_stage_detector.py`
- 作用/意义: 生育期检测器
- 路径: `src/cucumber_irrigation/core/growth_stage_detector.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `base64`
- `json`
- `pathlib`
- `typing`

### `window_builder.py`
- 作用/意义: 时序窗口构建器
- 路径: `src/cucumber_irrigation/core/window_builder.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/services/tsmixer_service.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/core/cold_start.py`

**引用了谁（外部依赖）**
- `__future__`
- `numpy`
- `pandas`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `src/cucumber_irrigation/pipelines/daily_pipeline.py`
- `src/cucumber_irrigation/services/tsmixer_service.py`
- `tests/test_acceptance.py`
- `tests/test_core.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
