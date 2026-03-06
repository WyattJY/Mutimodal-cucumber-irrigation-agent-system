# `backend/ultralytics/models/yolo/world` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `train.py`
- `train_world.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/yolo/world/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/models/yolo/world/train_world.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/models/yolo/__init__.py`

### `train.py`
- 作用/意义: Callback.
- 路径: `backend/ultralytics/models/yolo/world/train.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `clip`
- `itertools`

### `train_world.py`
- 作用/意义: A class extending the WorldTrainer class for training a world model from scratch on open-set dataset.
- 路径: `backend/ultralytics/models/yolo/world/train_world.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/models/yolo/world/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/torch_utils.py`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/models/yolo/__init__.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/utils.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/torch_utils.py`
