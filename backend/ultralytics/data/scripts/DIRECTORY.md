# `backend/ultralytics/data/scripts` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `download_weights.sh`
- `get_coco.sh`
- `get_coco128.sh`
- `get_imagenet.sh`

## 脚本/模块说明（本目录内）
### `download_weights.sh`
- 作用/意义: Ultralytics YOLO 🚀, AGPL-3.0 license Download latest models from https://github.com/ultralytics/assets/releases Example usage: bash ultralytics/data/scripts/download_weights.sh parent └── weights ├── 
- 路径: `backend/ultralytics/data/scripts/download_weights.sh`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `get_coco.sh`
- 作用/意义: Ultralytics YOLO 🚀, AGPL-3.0 license Download COCO 2017 dataset https://cocodataset.org Example usage: bash data/scripts/get_coco.sh parent ├── ultralytics └── datasets └── coco  ← downloads here Argu
- 路径: `backend/ultralytics/data/scripts/get_coco.sh`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `get_coco128.sh`
- 作用/意义: Ultralytics YOLO 🚀, AGPL-3.0 license Download COCO128 dataset https://www.kaggle.com/ultralytics/coco128 (first 128 images from COCO train2017) Example usage: bash data/scripts/get_coco128.sh parent ├
- 路径: `backend/ultralytics/data/scripts/get_coco128.sh`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `get_imagenet.sh`
- 作用/意义: Ultralytics YOLO 🚀, AGPL-3.0 license Download ILSVRC2012 ImageNet dataset https://image-net.org Example usage: bash data/scripts/get_imagenet.sh parent ├── ultralytics └── datasets └── imagenet  ← dow
- 路径: `backend/ultralytics/data/scripts/get_imagenet.sh`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
（无）
