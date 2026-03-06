# `backend/ultralytics/data` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `scripts/` → [`scripts/DIRECTORY.md`](scripts/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `annotator.py`
- `augment.py`
- `base.py`
- `build.py`
- `converter.py`
- `dataset.py`
- `loaders.py`
- `split_dota.py`
- `utils.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/data/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/converter.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/classify/val.py`
- `backend/ultralytics/models/yolo/detect/train.py`
- `backend/ultralytics/models/yolo/detect/val.py`
- `backend/ultralytics/models/yolo/world/train.py`
- （还有 1 项未展开）

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`

### `annotator.py`
- 作用/意义: Automatically annotates images using a YOLO object detection model and a SAM segmentation model.
- 路径: `backend/ultralytics/data/annotator.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`

**引用了谁（外部依赖）**
- `pathlib`

### `augment.py`
- 作用/意义: Base class for image transformations in the Ultralytics library.
- 路径: `backend/ultralytics/data/augment.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/dataset.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/models/rtdetr/predict.py`
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/models/sam/predict.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/instance.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `PIL`
- `albumentations`
- `copy`
- `cv2`
- `math`
- `numpy`
- `random`
- `torch`
- `torchvision`
- `typing`

### `base.py`
- 作用/意义: Base dataset class for loading and processing image data.
- 路径: `backend/ultralytics/data/base.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/dataset.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/utils/__init__.py`

**引用了谁（外部依赖）**
- `copy`
- `cv2`
- `glob`
- `math`
- `multiprocessing`
- `numpy`
- `os`
- `pathlib`
- `psutil`
- `random`
- `shutil`
- `torch`
- `typing`

### `build.py`
- 作用/意义: Dataloader that reuses workers.
- 路径: `backend/ultralytics/data/build.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/dataset.py`
- `backend/ultralytics/data/loaders.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`

**引用了谁（外部依赖）**
- `PIL`
- `numpy`
- `os`
- `pathlib`
- `random`
- `torch`

### `converter.py`
- 作用/意义: Converts 91-index COCO class IDs to 80-index COCO class IDs.
- 路径: `backend/ultralytics/data/converter.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/detect/val.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/files.py`
- `backend/ultralytics/utils/ops.py`

**引用了谁（外部依赖）**
- `PIL`
- `collections`
- `concurrent`
- `cv2`
- `json`
- `numpy`
- `pathlib`
- `random`
- `shutil`

### `dataset.py`
- 作用/意义: Dataset class for loading object detection and/or segmentation labels in YOLO format.
- 路径: `backend/ultralytics/data/dataset.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/build.py`
- `backend/ultralytics/engine/exporter.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/data/base.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `PIL`
- `collections`
- `cv2`
- `itertools`
- `json`
- `multiprocessing`
- `numpy`
- `pathlib`
- `torch`
- `torchvision`

### `loaders.py`
- 作用/意义: Class to represent various types of input sources for predictions.
- 路径: `backend/ultralytics/data/loaders.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/build.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/patches.py`

**引用了谁（外部依赖）**
- `PIL`
- `cv2`
- `dataclasses`
- `glob`
- `math`
- `mss`
- `numpy`
- `os`
- `pafy`
- `pathlib`
- `pillow_heif`
- `pytubefix`
- `requests`
- `threading`
- `time`
- （还有 3 项未展开）

### `split_dota.py`
- 作用/意义: Calculate Intersection over Foreground (IoF) between polygons and bounding boxes.
- 路径: `backend/ultralytics/data/split_dota.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/utils/checks.py`

**引用了谁（外部依赖）**
- `PIL`
- `cv2`
- `glob`
- `itertools`
- `math`
- `numpy`
- `pathlib`
- `shapely`
- `tqdm`

### `utils.py`
- 作用/意义: Define label paths as a function of image paths.
- 路径: `backend/ultralytics/data/utils.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/data/augment.py`
- `backend/ultralytics/data/base.py`
- `backend/ultralytics/data/build.py`
- `backend/ultralytics/data/dataset.py`
- `backend/ultralytics/data/loaders.py`
- `backend/ultralytics/data/split_dota.py`
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/hub/__init__.py`
- （还有 1 项未展开）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `PIL`
- `cv2`
- `gc`
- `hashlib`
- `json`
- `matplotlib`
- `multiprocessing`
- `numpy`
- `os`
- `pathlib`
- `random`
- `subprocess`
- `tarfile`
- `time`
- `torchvision`
- （还有 1 项未展开）

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/results.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/models/rtdetr/predict.py`
- `backend/ultralytics/models/rtdetr/val.py`
- `backend/ultralytics/models/sam/predict.py`
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/classify/val.py`
- `backend/ultralytics/models/yolo/detect/train.py`
- （还有 4 项未展开）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/nn/autobackend.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/files.py`
- `backend/ultralytics/utils/instance.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/patches.py`
- `backend/ultralytics/utils/plotting.py`
- `backend/ultralytics/utils/torch_utils.py`
