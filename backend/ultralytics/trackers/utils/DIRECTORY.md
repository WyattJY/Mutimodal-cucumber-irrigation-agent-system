# `backend/ultralytics/trackers/utils` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `gmc.py`
- `kalman_filter.py`
- `matching.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/trackers/utils/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `gmc.py`
- 作用/意义: Generalized Motion Compensation (GMC) class for tracking and object detection in video frames.
- 路径: `backend/ultralytics/trackers/utils/gmc.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/trackers/bot_sort.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`

**引用了谁（外部依赖）**
- `copy`
- `cv2`
- `numpy`

### `kalman_filter.py`
- 作用/意义: A KalmanFilterXYAH class for tracking bounding boxes in image space using a Kalman filter.
- 路径: `backend/ultralytics/trackers/utils/kalman_filter.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/trackers/bot_sort.py`
- `backend/ultralytics/trackers/byte_tracker.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `numpy`
- `scipy`

### `matching.py`
- 作用/意义: Perform linear assignment using either the scipy or lap.lapjv method.
- 路径: `backend/ultralytics/trackers/utils/matching.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/trackers/bot_sort.py`
- `backend/ultralytics/trackers/byte_tracker.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`

**引用了谁（外部依赖）**
- `lap`
- `numpy`
- `scipy`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/trackers/bot_sort.py`
- `backend/ultralytics/trackers/byte_tracker.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`
