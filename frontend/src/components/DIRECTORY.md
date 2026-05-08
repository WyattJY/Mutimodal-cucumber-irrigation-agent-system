# `frontend/src/components` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 子目录
- `charts/` → [`charts/DIRECTORY.md`](charts/DIRECTORY.md)
- `chat/` → [`chat/DIRECTORY.md`](chat/DIRECTORY.md)
- `common/` → [`common/DIRECTORY.md`](common/DIRECTORY.md)
- `features/` → [`features/DIRECTORY.md`](features/DIRECTORY.md)
- `ImageCompare/` → [`ImageCompare/DIRECTORY.md`](ImageCompare/DIRECTORY.md)
- `layout/` → [`layout/DIRECTORY.md`](layout/DIRECTORY.md)
- `PlantResponseCard/` → [`PlantResponseCard/DIRECTORY.md`](PlantResponseCard/DIRECTORY.md)
- `prediction/` → [`prediction/DIRECTORY.md`](prediction/DIRECTORY.md)
- `RAGReferences/` → [`RAGReferences/DIRECTORY.md`](RAGReferences/DIRECTORY.md)
- `vision/` → [`vision/DIRECTORY.md`](vision/DIRECTORY.md)

## 本目录文件概览
- `OverrideModal.tsx`
- `TrendChart.tsx`

## 脚本/模块说明（本目录内）
### `OverrideModal.tsx`
- 作用/意义: OverrideModal - 人工覆盖对话框组件
- 路径: `frontend/src/components/OverrideModal.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`

### `TrendChart.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/components/TrendChart.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Weekly.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `chart.js`
- `react`
- `react-chartjs-2`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Weekly.tsx`

**本目录引用了谁（跨目录）**
（无）
