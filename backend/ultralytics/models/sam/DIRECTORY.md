# `backend/ultralytics/models/sam` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `modules/` → [`modules/DIRECTORY.md`](modules/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `amg.py`
- `build.py`
- `model.py`
- `predict.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/sam/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/__init__.py`

### `amg.py`
- 作用/意义: Determines if bounding boxes are near the edge of a cropped image region using a specified tolerance.
- 路径: `backend/ultralytics/models/sam/amg.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/sam/predict.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `cv2`
- `itertools`
- `math`
- `numpy`
- `torch`
- `typing`

### `build.py`
- 作用/意义: Builds and returns a Segment Anything Model (SAM) h-size model with specified encoder parameters.
- 路径: `backend/ultralytics/models/sam/build.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/sam/model.py`
- `backend/ultralytics/models/sam/predict.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/sam/modules/decoders.py`
- `backend/ultralytics/models/sam/modules/encoders.py`
- `backend/ultralytics/models/sam/modules/memory_attention.py`
- `backend/ultralytics/models/sam/modules/sam.py`
- `backend/ultralytics/models/sam/modules/tiny_encoder.py`
- `backend/ultralytics/models/sam/modules/transformer.py`
- `backend/ultralytics/utils/downloads.py`

**引用了谁（外部依赖）**
- `functools`
- `torch`

### `model.py`
- 作用/意义: SAM model interface.
- 路径: `backend/ultralytics/models/sam/model.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/sam/build.py`
- `backend/ultralytics/models/sam/predict.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `pathlib`

### `predict.py`
- 作用/意义: Generate predictions using the Segment Anything Model (SAM).
- 路径: `backend/ultralytics/models/sam/predict.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/sam/model.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/models/sam/amg.py`
- `backend/ultralytics/models/sam/build.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `collections`
- `numpy`
- `torch`
- `torchvision`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`
