# `backend/ultralytics/models/utils` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `loss.py`
- `ops.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/utils/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `loss.py`
- 作用/意义: DETR (DEtection TRansformer) Loss class. This class calculates and returns the different loss components for the     DETR object detection model. It computes classification loss, bounding box loss, GIoU loss, and optionally auxiliary     losses.
- 路径: `backend/ultralytics/models/utils/loss.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/nn/tasks.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/utils/ops.py`
- `backend/ultralytics/utils/loss.py`
- `backend/ultralytics/utils/metrics.py`

**引用了谁（外部依赖）**
- `torch`

### `ops.py`
- 作用/意义: A module implementing the HungarianMatcher, which is a differentiable module to solve the assignment problem in an     end-to-end fashion.
- 路径: `backend/ultralytics/models/utils/ops.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/utils/loss.py`
- `backend/ultralytics/nn/modules/head.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `scipy`
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/nn/modules/head.py`
- `backend/ultralytics/nn/tasks.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/utils/loss.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
