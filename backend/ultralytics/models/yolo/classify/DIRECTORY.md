# `backend/ultralytics/models/yolo/classify` 目录说明

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
- 路径: `backend/ultralytics/models/yolo/classify/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/__init__.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/yolo/classify/predict.py`
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/classify/val.py`

### `predict.py`
- 作用/意义: A class extending the BasePredictor class for prediction based on a classification model.
- 路径: `backend/ultralytics/models/yolo/classify/predict.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/classify/__init__.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `PIL`
- `cv2`
- `torch`

### `train.py`
- 作用/意义: A class extending the BaseTrainer class for training based on a classification model.
- 路径: `backend/ultralytics/models/yolo/classify/train.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/classify/__init__.py`

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
- `torch`
- `torchvision`

### `val.py`
- 作用/意义: A class extending the BaseValidator class for validation based on a classification model.
- 路径: `backend/ultralytics/models/yolo/classify/val.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/classify/__init__.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/models/yolo/__init__.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/plotting.py`
- `backend/ultralytics/utils/torch_utils.py`
