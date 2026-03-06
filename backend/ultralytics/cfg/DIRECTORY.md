# `backend/ultralytics/cfg` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 子目录
- `datasets/` → [`datasets/DIRECTORY.md`](datasets/DIRECTORY.md)
- `models/` → [`models/DIRECTORY.md`](models/DIRECTORY.md)
- `solutions/` → [`solutions/DIRECTORY.md`](solutions/DIRECTORY.md)
- `trackers/` → [`trackers/DIRECTORY.md`](trackers/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `default.yaml`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Arguments received: {str(["yolo"] + ARGV[1:])}. Ultralytics 'yolo solutions' usage overview:
- 路径: `backend/ultralytics/cfg/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/tuner.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/utils/benchmarks.py`
- `backend/ultralytics/utils/tuner.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/solutions/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/files.py`

**引用了谁（外部依赖）**
- `cv2`
- `difflib`
- `os`
- `pathlib`
- `shutil`
- `subprocess`
- `sys`
- `types`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/tuner.py`
- `backend/ultralytics/engine/validator.py`
- `backend/ultralytics/utils/benchmarks.py`
- `backend/ultralytics/utils/tuner.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/solutions/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/files.py`
