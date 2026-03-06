# `backend/ultralytics/models/fastsam` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `model.py`
- `predict.py`
- `utils.py`
- `val.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/fastsam/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/__init__.py`

### `model.py`
- 作用/意义: FastSAM model interface.
- 路径: `backend/ultralytics/models/fastsam/model.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/fastsam/predict.py`
- `backend/ultralytics/models/fastsam/val.py`

**引用了谁（外部依赖）**
- `pathlib`

### `predict.py`
- 作用/意义: FastSAMPredictor is specialized for fast SAM (Segment Anything Model) segmentation prediction tasks in Ultralytics     YOLO framework.
- 路径: `backend/ultralytics/models/fastsam/predict.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/fastsam/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/fastsam/utils.py`
- `backend/ultralytics/models/yolo/segment/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `PIL`
- `clip`
- `torch`

### `utils.py`
- 作用/意义: Adjust bounding boxes to stick to image border if they are within a certain threshold.
- 路径: `backend/ultralytics/models/fastsam/utils.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/fastsam/predict.py`

**引用了谁（内部依赖）**
（无）

### `val.py`
- 作用/意义: Custom validation class for fast SAM (Segment Anything Model) segmentation in Ultralytics YOLO framework.
- 路径: `backend/ultralytics/models/fastsam/val.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/fastsam/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/yolo/segment/__init__.py`
- `backend/ultralytics/utils/metrics.py`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/models/yolo/segment/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
