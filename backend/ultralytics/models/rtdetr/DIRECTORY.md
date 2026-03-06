# `backend/ultralytics/models/rtdetr` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `model.py`
- `predict.py`
- `train.py`
- `val.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/rtdetr/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/__init__.py`

### `model.py`
- 作用/意义: Interface for Baidu's RT-DETR, a Vision Transformer-based real-time object detector. RT-DETR offers real-time performance and high accuracy, excelling in accelerated backends like CUDA with TensorRT. It features an efficient hybrid encoder and IoU-aware query selection for enhanced detection accuracy.
- 路径: `backend/ultralytics/models/rtdetr/model.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/rtdetr/predict.py`
- `backend/ultralytics/models/rtdetr/train.py`
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/nn/tasks.py`

### `predict.py`
- 作用/意义: RT-DETR (Real-Time Detection Transformer) Predictor extending the BasePredictor class for making predictions using     Baidu's RT-DETR model.
- 路径: `backend/ultralytics/models/rtdetr/predict.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/rtdetr/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `torch`

### `train.py`
- 作用/意义: Trainer class for the RT-DETR model developed by Baidu for real-time object detection. Extends the DetectionTrainer     class for YOLO to adapt to the specific features and architecture of RT-DETR. This model leverages Vision     Transformers and has capabilities like IoU-aware query selection and adaptable inference speed.
- 路径: `backend/ultralytics/models/rtdetr/train.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/rtdetr/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`

**引用了谁（外部依赖）**
- `copy`
- `torch`

### `val.py`
- 作用/意义: Real-Time DEtection and TRacking (RT-DETR) dataset class extending the base YOLODataset class.
- 路径: `backend/ultralytics/models/rtdetr/val.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/rtdetr/model.py`
- `backend/ultralytics/models/rtdetr/train.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/ops.py`
