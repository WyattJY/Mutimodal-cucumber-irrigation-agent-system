# `backend/ultralytics/nn` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `modules/` → [`modules/DIRECTORY.md`](modules/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `autobackend.py`
- `tasks.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/nn/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/nn/modules/__init__.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`

### `autobackend.py`
- 作用/意义: Check class names.
- 路径: `backend/ultralytics/nn/autobackend.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/utils/files.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/triton.py`

**引用了谁（外部依赖）**
- `MNN`
- `PIL`
- `ast`
- `collections`
- `coremltools`
- `cv2`
- `json`
- `mct_quantizers`
- `ncnn`
- `numpy`
- `onnxruntime`
- `openvino`
- `os`
- `paddle`
- `pathlib`
- （还有 9 项未展开）

### `tasks.py`
- 作用/意义: The BaseModel class serves as a base class for all the models in the Ultralytics YOLO family.
- 路径: `backend/ultralytics/nn/tasks.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/models/rtdetr/model.py`
- `backend/ultralytics/models/rtdetr/train.py`
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/detect/train.py`
- `backend/ultralytics/models/yolo/model.py`
- `backend/ultralytics/models/yolo/obb/train.py`
- `backend/ultralytics/models/yolo/pose/train.py`
- （还有 3 项未展开）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/utils/loss.py`
- `backend/ultralytics/nn/modules/__init__.py`
- `backend/ultralytics/nn/modules/block.py`
- `backend/ultralytics/nn/modules/head.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/loss.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/plotting.py`
- （还有 1 项未展开）

**引用了谁（外部依赖）**
- `ast`
- `clip`
- `contextlib`
- `copy`
- `importlib`
- `pathlib`
- `pickle`
- `re`
- `sys`
- `thop`
- `torch`
- `types`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/models/rtdetr/model.py`
- `backend/ultralytics/models/rtdetr/train.py`
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/detect/train.py`
- `backend/ultralytics/models/yolo/model.py`
- `backend/ultralytics/models/yolo/obb/train.py`
- （还有 4 项未展开）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/models/utils/loss.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/loss.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/plotting.py`
- `backend/ultralytics/utils/torch_utils.py`
- `backend/ultralytics/utils/triton.py`
