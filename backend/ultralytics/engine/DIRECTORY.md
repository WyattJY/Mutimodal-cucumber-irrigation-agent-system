# `backend/ultralytics/engine` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `exporter.py`
- `model.py`
- `predictor.py`
- `results.py`
- `trainer.py`
- `tuner.py`
- `validator.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/engine/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `exporter.py`
- 作用/意义: Export a YOLO PyTorch model to other formats. TensorFlow exports authored by https://github.com/zldrobit.
- 路径: `backend/ultralytics/engine/exporter.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/utils/benchmarks.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/dataset.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/nn/modules/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/callbacks/__init__.py`
- `backend/ultralytics/utils/checks.py`
- （还有 5 项未展开）

**引用了谁（外部依赖）**
- `MNN`
- `PIL`
- `copy`
- `coremltools`
- `datetime`
- `difflib`
- `flatbuffers`
- `gc`
- `json`
- `model_compression_toolkit`
- `ncnn`
- `nncf`
- `numpy`
- `onnx`
- `onnx2tf`
- （还有 16 项未展开）

### `model.py`
- 作用/意义: A base class for implementing YOLO models, unifying APIs across different model types.
- 路径: `backend/ultralytics/engine/model.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/fastsam/model.py`
- `backend/ultralytics/models/nas/model.py`
- `backend/ultralytics/models/rtdetr/model.py`
- `backend/ultralytics/models/sam/model.py`
- `backend/ultralytics/models/yolo/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/engine/tuner.py`
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/trackers/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- （还有 4 项未展开）

**引用了谁（外部依赖）**
- `PIL`
- `copy`
- `datetime`
- `inspect`
- `numpy`
- `pathlib`
- `torch`
- `typing`
- `urllib`

### `predictor.py`
- 作用/意义: Run prediction on images, videos, directories, globs, YouTube, webcam, streams, etc.
- 路径: `backend/ultralytics/engine/predictor.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/nas/predict.py`
- `backend/ultralytics/models/rtdetr/predict.py`
- `backend/ultralytics/models/sam/predict.py`
- `backend/ultralytics/models/yolo/classify/predict.py`
- `backend/ultralytics/models/yolo/detect/predict.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/callbacks/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/files.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `cv2`
- `numpy`
- `pathlib`
- `platform`
- `re`
- `threading`
- `torch`

### `results.py`
- 作用/意义: Ultralytics Results, Boxes and Masks classes for handling inference results.
- 路径: `backend/ultralytics/engine/results.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/nas/predict.py`
- `backend/ultralytics/models/rtdetr/predict.py`
- `backend/ultralytics/models/sam/predict.py`
- `backend/ultralytics/models/yolo/classify/predict.py`
- `backend/ultralytics/models/yolo/detect/predict.py`
- `backend/ultralytics/models/yolo/detect/val.py`
- `backend/ultralytics/models/yolo/obb/predict.py`
- `backend/ultralytics/models/yolo/obb/val.py`
- `backend/ultralytics/models/yolo/pose/predict.py`
- （还有 3 项未展开）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/plotting.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `copy`
- `functools`
- `json`
- `numpy`
- `pandas`
- `pathlib`
- `torch`

### `trainer.py`
- 作用/意义: Train a model on a dataset.
- 路径: `backend/ultralytics/engine/trainer.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/detect/train.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/autobatch.py`
- `backend/ultralytics/utils/callbacks/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/dist.py`
- `backend/ultralytics/utils/files.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `copy`
- `datetime`
- `gc`
- `io`
- `math`
- `numpy`
- `os`
- `pandas`
- `pathlib`
- `subprocess`
- `time`
- `torch`
- `warnings`

### `tuner.py`
- 作用/意义: Module provides functionalities for hyperparameter tuning of the Ultralytics YOLO models for object detection, instance segmentation, image classification, pose estimation, and multi-object tracking.
- 路径: `backend/ultralytics/engine/tuner.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/callbacks/__init__.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `numpy`
- `random`
- `shutil`
- `subprocess`
- `time`
- `torch`

### `validator.py`
- 作用/意义: Check a model's accuracy on a test or val split of a dataset.
- 路径: `backend/ultralytics/engine/validator.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/classify/val.py`
- `backend/ultralytics/models/yolo/detect/val.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/callbacks/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `json`
- `numpy`
- `pathlib`
- `scipy`
- `time`
- `torch`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/models/fastsam/model.py`
- `backend/ultralytics/models/nas/model.py`
- `backend/ultralytics/models/nas/predict.py`
- `backend/ultralytics/models/rtdetr/model.py`
- `backend/ultralytics/models/rtdetr/predict.py`
- `backend/ultralytics/models/sam/model.py`
- `backend/ultralytics/models/sam/predict.py`
- `backend/ultralytics/models/yolo/classify/predict.py`
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/classify/val.py`
- `backend/ultralytics/models/yolo/detect/predict.py`
- （还有 11 项未展开）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/data/dataset.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/nn/modules/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/trackers/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- （还有 12 项未展开）
