# `backend/ultralytics/trackers` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `utils/` → [`utils/DIRECTORY.md`](utils/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `basetrack.py`
- `bot_sort.py`
- `byte_tracker.py`
- `README.md`
- `track.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/trackers/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`

### `basetrack.py`
- 作用/意义: Module defines the base classes and structures for object tracking in YOLO.
- 路径: `backend/ultralytics/trackers/basetrack.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/trackers/bot_sort.py`
- `backend/ultralytics/trackers/byte_tracker.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `collections`
- `numpy`

### `bot_sort.py`
- 作用/意义: An extended version of the STrack class for YOLOv8, adding object tracking features.
- 路径: `backend/ultralytics/trackers/bot_sort.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/trackers/track.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/trackers/basetrack.py`
- `backend/ultralytics/trackers/byte_tracker.py`
- `backend/ultralytics/trackers/utils/gmc.py`
- `backend/ultralytics/trackers/utils/kalman_filter.py`
- `backend/ultralytics/trackers/utils/matching.py`

**引用了谁（外部依赖）**
- `collections`
- `numpy`

### `byte_tracker.py`
- 作用/意义: Single object tracking representation that uses Kalman filtering for state estimation.
- 路径: `backend/ultralytics/trackers/byte_tracker.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/trackers/bot_sort.py`
- `backend/ultralytics/trackers/track.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/trackers/basetrack.py`
- `backend/ultralytics/trackers/utils/kalman_filter.py`
- `backend/ultralytics/trackers/utils/matching.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `numpy`

### `track.py`
- 作用/意义: Initialize trackers for object tracking during prediction.
- 路径: `backend/ultralytics/trackers/track.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/trackers/bot_sort.py`
- `backend/ultralytics/trackers/byte_tracker.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`

**引用了谁（外部依赖）**
- `functools`
- `pathlib`
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/engine/model.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/ops.py`
