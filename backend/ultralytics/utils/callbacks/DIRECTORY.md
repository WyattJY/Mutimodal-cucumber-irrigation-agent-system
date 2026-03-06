# `backend/ultralytics/utils/callbacks` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `base.py`
- `clearml.py`
- `comet.py`
- `dvc.py`
- `hub.py`
- `mlflow.py`
- `neptune.py`
- `raytune.py`
- `tensorboard.py`
- `wb.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/utils/callbacks/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/tuner.py`
- `backend/ultralytics/engine/validator.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`

### `base.py`
- 作用/意义: Base callbacks.
- 路径: `backend/ultralytics/utils/callbacks/base.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/callbacks/clearml.py`
- `backend/ultralytics/utils/callbacks/comet.py`
- `backend/ultralytics/utils/callbacks/dvc.py`
- `backend/ultralytics/utils/callbacks/hub.py`
- `backend/ultralytics/utils/callbacks/mlflow.py`
- `backend/ultralytics/utils/callbacks/neptune.py`
- `backend/ultralytics/utils/callbacks/raytune.py`
- `backend/ultralytics/utils/callbacks/tensorboard.py`
- `backend/ultralytics/utils/callbacks/wb.py`

**引用了谁（外部依赖）**
- `collections`
- `copy`

### `clearml.py`
- 作用/意义: Log files (images) as debug samples in the ClearML task.
- 路径: `backend/ultralytics/utils/callbacks/clearml.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `clearml`
- `matplotlib`
- `re`

### `comet.py`
- 作用/意义: Returns the mode of comet set in the environment variables, defaults to 'online' if not set.
- 路径: `backend/ultralytics/utils/callbacks/comet.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `comet_ml`
- `os`
- `pathlib`

### `dvc.py`
- 作用/意义: Logs images at specified path with an optional prefix using DVCLive.
- 路径: `backend/ultralytics/utils/callbacks/dvc.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `dvclive`
- `os`
- `pathlib`
- `re`

### `hub.py`
- 作用/意义: Create a remote Ultralytics HUB session to log local model training.
- 路径: `backend/ultralytics/utils/callbacks/hub.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `json`
- `time`

### `mlflow.py`
- 作用/意义: MLflow Logging for Ultralytics YOLO.
- 路径: `backend/ultralytics/utils/callbacks/mlflow.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`

**引用了谁（外部依赖）**
- `mlflow`
- `os`
- `pathlib`

### `neptune.py`
- 作用/意义: Log scalars to the NeptuneAI experiment logger.
- 路径: `backend/ultralytics/utils/callbacks/neptune.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `matplotlib`
- `neptune`

### `raytune.py`
- 作用/意义: Sends training metrics to Ray Tune at end of each epoch.
- 路径: `backend/ultralytics/utils/callbacks/raytune.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`

**引用了谁（外部依赖）**
- `ray`

### `tensorboard.py`
- 作用/意义: Logs scalar values to TensorBoard.
- 路径: `backend/ultralytics/utils/callbacks/tensorboard.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `copy`
- `torch`
- `warnings`

### `wb.py`
- 作用/意义: Create and log a custom metric visualization to wandb.plot.pr_curve.
- 路径: `backend/ultralytics/utils/callbacks/wb.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/utils/callbacks/base.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/torch_utils.py`

**引用了谁（外部依赖）**
- `numpy`
- `pandas`
- `wandb`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/engine/exporter.py`
- `backend/ultralytics/engine/model.py`
- `backend/ultralytics/engine/predictor.py`
- `backend/ultralytics/engine/trainer.py`
- `backend/ultralytics/engine/tuner.py`
- `backend/ultralytics/engine/validator.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/hub/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/metrics.py`
- `backend/ultralytics/utils/ops.py`
- `backend/ultralytics/utils/torch_utils.py`
