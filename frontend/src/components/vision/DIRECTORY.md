# `frontend/src/components/vision` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `ImageUpload.tsx`
- `ImageViewer.tsx`
- `index.ts`
- `MetricsDisplay.tsx`

## 脚本/模块说明（本目录内）
### `ImageUpload.tsx`
- 作用/意义: ImageUpload - 图像上传组件
- 路径: `frontend/src/components/vision/ImageUpload.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `clsx`
- `react`

### `ImageViewer.tsx`
- 作用/意义: ImageViewer - 图像查看器组件 (支持原图/分割图切换)
- 路径: `frontend/src/components/vision/ImageViewer.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `clsx`
- `react`

### `index.ts`
- 作用/意义: Vision components index
- 路径: `frontend/src/components/vision/index.ts`

**被谁引用/调用（代码级）**
- `frontend/src/pages/Predict.tsx`
- `frontend/src/pages/Vision.tsx`

**引用了谁（内部依赖）**
（无）

### `MetricsDisplay.tsx`
- 作用/意义: MetricsDisplay - 分割指标显示组件
- 路径: `frontend/src/components/vision/MetricsDisplay.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `clsx`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/pages/Predict.tsx`
- `frontend/src/pages/Vision.tsx`

**本目录引用了谁（跨目录）**
（无）
