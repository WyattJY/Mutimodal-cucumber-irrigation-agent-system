# `src/cucumber_irrigation/utils` 目录说明

## 目录定位
工具函数：token 计数、prompt 组装等通用工具。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `prompt_builder.py`
- `token_counter.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 工具函数
- 路径: `src/cucumber_irrigation/utils/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

### `prompt_builder.py`
- 作用/意义: Prompt 构建器
- 路径: `src/cucumber_irrigation/utils/prompt_builder.py`

**被谁引用/调用（代码级）**
- `scripts/generate_responses.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `json`
- `pathlib`
- `typing`

### `token_counter.py`
- 作用/意义: Token 计数器
- 路径: `src/cucumber_irrigation/utils/token_counter.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/memory/weekly_summary_store.py`
- `tests/test_memory.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `json`
- `tiktoken`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `scripts/generate_responses.py`
- `src/cucumber_irrigation/memory/budget_controller.py`
- `src/cucumber_irrigation/memory/weekly_summary_store.py`
- `tests/test_memory.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
