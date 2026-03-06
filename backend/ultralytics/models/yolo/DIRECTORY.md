# `backend/ultralytics/models/yolo` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `classify/` → [`classify/DIRECTORY.md`](classify/DIRECTORY.md)
- `detect/` → [`detect/DIRECTORY.md`](detect/DIRECTORY.md)
- `obb/` → [`obb/DIRECTORY.md`](obb/DIRECTORY.md)
- `pose/` → [`pose/DIRECTORY.md`](pose/DIRECTORY.md)
- `segment/` → [`segment/DIRECTORY.md`](segment/DIRECTORY.md)
- `world/` → [`world/DIRECTORY.md`](world/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `model.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/models/yolo/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/models/yolo/classify/train.py`
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/models/yolo/detect/train.py`
- `backend/ultralytics/models/yolo/model.py`
- `backend/ultralytics/models/yolo/obb/__init__.py`
- `backend/ultralytics/models/yolo/obb/train.py`
- `backend/ultralytics/models/yolo/pose/__init__.py`
- `backend/ultralytics/models/yolo/pose/train.py`
- `backend/ultralytics/models/yolo/segment/__init__.py`
- `backend/ultralytics/models/yolo/segment/train.py`
- （还有 2 项未展开）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/models/yolo/classify/__init__.py`
- `backend/ultralytics/models/yolo/detect/__init__.py`
- `backend/ultralytics/models/yolo/obb/__init__.py`
- `backend/ultralytics/models/yolo/pose/__init__.py`
- `backend/ultralytics/models/yolo/segment/__init__.py`
- `backend/ultralytics/models/yolo/world/__init__.py`

### `model.py`
- 作用/意义: YOLO (You Only Look Once) object detection model.
- 路径: `backend/ultralytics/models/yolo/model.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/yolo/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`

**引用了谁（外部依赖）**
- `pathlib`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/nn/tasks.py`
- `backend/ultralytics/utils/__init__.py`
