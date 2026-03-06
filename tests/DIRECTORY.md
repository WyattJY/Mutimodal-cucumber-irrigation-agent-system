# `tests` 目录说明

## 目录定位
测试目录：核心组件/流程的单元测试与回归测试。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `conftest.py`
- `test_acceptance.py`
- `test_core.py`
- `test_integration.py`
- `test_memory.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: cucumber-irrigation tests
- 路径: `tests/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `conftest.py`
- 作用/意义: Pytest fixtures for cucumber-irrigation tests
- 路径: `tests/conftest.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/models/__init__.py`

**引用了谁（外部依赖）**
- `json`
- `numpy`
- `pandas`
- `pathlib`
- `pytest`
- `tempfile`

### `test_acceptance.py`
- 作用/意义: Requirements acceptance tests
- 路径: `tests/test_acceptance.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/core/__init__.py`
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`

**引用了谁（外部依赖）**
- `numpy`
- `os`
- `pandas`
- `pytest`

### `test_core.py`
- 作用/意义: Unit tests for core components
- 路径: `tests/test_core.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/core/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`

**引用了谁（外部依赖）**
- `datetime`
- `numpy`
- `pandas`
- `pytest`

### `test_integration.py`
- 作用/意义: Integration tests for pipelines
- 路径: `tests/test_integration.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/pipelines/__init__.py`

**引用了谁（外部依赖）**
- `numpy`
- `os`
- `pandas`
- `pytest`

### `test_memory.py`
- 作用/意义: Unit tests for memory architecture
- 路径: `tests/test_memory.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/utils/token_counter.py`

**引用了谁（外部依赖）**
- `json`
- `os`
- `pytest`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/core/__init__.py`
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/pipelines/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`
- `src/cucumber_irrigation/utils/token_counter.py`
