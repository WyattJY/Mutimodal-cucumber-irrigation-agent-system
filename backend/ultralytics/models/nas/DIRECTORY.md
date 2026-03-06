# `backend/ultralytics/models/nas` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `model.py`
- `predict.py`
- `val.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/nas/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/__init__.py`

### `model.py`
- 作用/意义: YOLO-NAS model interface.
- 路径: `backend/ultralytics/models/nas/model.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/nas/predict.py`
- `backend/ultralytics/models/nas/val.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `pathlib`
- `super_gradients`
- `torch`

### `predict.py`
- 作用/意义: Ultralytics YOLO NAS Predictor for object detection.
- 路径: `backend/ultralytics/models/nas/predict.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/nas/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `torch`

### `val.py`
- 作用/意义: Ultralytics YOLO NAS Validator for object detection.
- 路径: `backend/ultralytics/models/nas/val.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/nas/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`
