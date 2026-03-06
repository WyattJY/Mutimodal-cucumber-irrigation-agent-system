# `backend/ultralytics` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `assets/` → [`assets/DIRECTORY.md`](assets/DIRECTORY.md)
- `cfg/` → [`cfg/DIRECTORY.md`](cfg/DIRECTORY.md)
- `data/` → [`data/DIRECTORY.md`](data/DIRECTORY.md)
- `engine/` → [`engine/DIRECTORY.md`](engine/DIRECTORY.md)
- `hub/` → [`hub/DIRECTORY.md`](hub/DIRECTORY.md)
- `models/` → [`models/DIRECTORY.md`](models/DIRECTORY.md)
- `nn/` → [`nn/DIRECTORY.md`](nn/DIRECTORY.md)
- `solutions/` → [`solutions/DIRECTORY.md`](solutions/DIRECTORY.md)
- `trackers/` → [`trackers/DIRECTORY.md`](trackers/DIRECTORY.md)
- `utils/` → [`utils/DIRECTORY.md`](utils/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/__init__.py`

**被谁引用/调用（代码级）**
- `backend/app/services/yolo_service.py`
- `backend/ultralytics/cfg/__init__.py`
- `backend/ultralytics/data/__init__.py`
- `backend/ultralytics/data/annotator.py`
- `backend/ultralytics/data/converter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/nn/__init__.py`
- `backend/ultralytics/solutions/__init__.py`
- `backend/ultralytics/solutions/solutions.py`
- （还有 6 项未展开）

**引用了谁（内部依赖）**
- `backend/ultralytics/models/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`

**引用了谁（外部依赖）**
- `os`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/services/yolo_service.py`

**本目录引用了谁（跨目录）**
（无）
