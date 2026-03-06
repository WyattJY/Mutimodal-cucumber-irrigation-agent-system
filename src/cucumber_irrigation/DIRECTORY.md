# `src/cucumber_irrigation` 目录说明

## 目录定位
核心 Python 包 `cucumber_irrigation`：包含管道、模型、记忆、RAG、服务封装等。

[上级目录](../DIRECTORY.md)

## 子目录
- `core/` → [`core/DIRECTORY.md`](core/DIRECTORY.md)
- `memory/` → [`memory/DIRECTORY.md`](memory/DIRECTORY.md)
- `models/` → [`models/DIRECTORY.md`](models/DIRECTORY.md)
- `pipelines/` → [`pipelines/DIRECTORY.md`](pipelines/DIRECTORY.md)
- `processors/` → [`processors/DIRECTORY.md`](processors/DIRECTORY.md)
- `rag/` → [`rag/DIRECTORY.md`](rag/DIRECTORY.md)
- `services/` → [`services/DIRECTORY.md`](services/DIRECTORY.md)
- `utils/` → [`utils/DIRECTORY.md`](utils/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `config.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 温室黄瓜灌水智能体系统 - Phase 0
- 路径: `src/cucumber_irrigation/__init__.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/core/__init__.py`
- `src/cucumber_irrigation/memory/__init__.py`
- `src/cucumber_irrigation/models/__init__.py`
- `src/cucumber_irrigation/pipelines/__init__.py`
- `src/cucumber_irrigation/processors/__init__.py`
- `src/cucumber_irrigation/rag/__init__.py`
- `src/cucumber_irrigation/services/__init__.py`
- `src/cucumber_irrigation/utils/__init__.py`

**引用了谁（内部依赖）**
（无）

### `config.py`
- 作用/意义: 配置加载模块
- 路径: `src/cucumber_irrigation/config.py`

**被谁引用/调用（代码级）**
- `scripts/build_pairs.py`
- `scripts/calc_growth_stats.py`
- `scripts/generate_responses.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dotenv`
- `os`
- `pathlib`
- `typing`
- `yaml`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `scripts/build_pairs.py`
- `scripts/calc_growth_stats.py`
- `scripts/generate_responses.py`

**本目录引用了谁（跨目录）**
（无）
