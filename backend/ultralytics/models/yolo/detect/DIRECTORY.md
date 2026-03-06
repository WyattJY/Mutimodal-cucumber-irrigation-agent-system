# `backend/ultralytics/models/yolo/detect` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `predict.py`
- `train.py`
- `val.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/yolo/detect/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/nas/val.py`
- `backend/ultralytics/models/rtdetr/train.py`
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/models/yolo/obb/val.py`
- `backend/ultralytics/models/yolo/pose/val.py`
- `backend/ultralytics/models/yolo/segment/val.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/yolo/__init__.py`

### `predict.py`
- 作用/意义: A class extending the BasePredictor class for prediction based on a detection model.
- 路径: `backend/ultralytics/models/yolo/detect/predict.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/obb/predict.py`
- `backend/ultralytics/models/yolo/pose/predict.py`
- `backend/ultralytics/models/yolo/segment/predict.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/utils/ops.py`

### `train.py`
- 作用/意义: A class extending the BaseTrainer class for training based on a detection model.
- 路径: `backend/ultralytics/models/yolo/detect/train.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/plotting.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `copy`
- `math`
- `numpy`
- `random`
- `torch`

### `val.py`
- 作用/意义: A class extending the BaseValidator class for validation based on a detection model.
- 路径: `backend/ultralytics/models/yolo/detect/val.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/converter.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `lvis`
- `numpy`
- `os`
- `pathlib`
- `pycocotools`
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/models/nas/val.py`
- `backend/ultralytics/models/rtdetr/train.py`
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/models/yolo/obb/predict.py`
- `backend/ultralytics/models/yolo/obb/val.py`
- `backend/ultralytics/models/yolo/pose/predict.py`
- `backend/ultralytics/models/yolo/pose/val.py`
- `backend/ultralytics/models/yolo/segment/predict.py`
- `backend/ultralytics/models/yolo/segment/val.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/converter.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- （还有 2 项未展开）
