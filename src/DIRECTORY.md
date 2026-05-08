# `src` 目录说明

## 目录定位
核心 Python 包源码：实现 Daily/Weekly pipeline、4层记忆、RAG 等可复用组件。

[上级目录](../DIRECTORY.md)

## 子目录
- `cucumber_irrigation/` → [`cucumber_irrigation/DIRECTORY.md`](cucumber_irrigation/DIRECTORY.md)

## 本目录文件概览
- `build_index.py`
- `build_pairs.py`
- `run_daily.py`
- `run_weekly.py`
- `tsmixer_batch.py`
- `yolo_batch.py`

## 脚本/模块说明（本目录内）
### `build_index.py`
- 作用/意义: Generate `data/index/image_index.csv` from `data/images/`.
- 路径: `src/build_index.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `build_pairs.py`
- 作用/意义: Generate `data/index/daily_pairs.csv` from `data/index/image_index.csv`.
- 路径: `src/build_pairs.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `run_daily.py`
- 作用/意义: Daily pipeline: build context -> call LLM -> write episode.
- 路径: `src/run_daily.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `run_weekly.py`
- 作用/意义: Weekly pipeline: read 7-day episodes -> generate weekly block -> persist.
- 路径: `src/run_weekly.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `tsmixer_batch.py`
- 作用/意义: Run TSMixer in batch and write the prediction table.
- 路径: `src/tsmixer_batch.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `yolo_batch.py`
- 作用/意义: Run YOLO in batch and write the features table.
- 路径: `src/yolo_batch.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
（无）
