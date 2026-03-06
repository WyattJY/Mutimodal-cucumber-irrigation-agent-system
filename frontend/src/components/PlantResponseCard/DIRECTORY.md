# `frontend/src/components/PlantResponseCard` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `AbnormalityAlert.tsx`
- `ConfidenceBar.tsx`
- `EvidenceList.tsx`
- `index.ts`
- `PlantResponseCard.tsx`
- `TrendBadge.tsx`

## 脚本/模块说明（本目录内）
### `AbnormalityAlert.tsx`
- 作用/意义: T3.5 AbnormalityAlert - 异常警告组件
- 路径: `frontend/src/components/PlantResponseCard/AbnormalityAlert.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`

### `ConfidenceBar.tsx`
- 作用/意义: T3.3 ConfidenceBar - 置信度进度条组件
- 路径: `frontend/src/components/PlantResponseCard/ConfidenceBar.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`

### `EvidenceList.tsx`
- 作用/意义: T3.4 EvidenceList - 证据列表组件
- 路径: `frontend/src/components/PlantResponseCard/EvidenceList.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`

### `index.ts`
- 作用/意义: PlantResponseCard Components Export
- 路径: `frontend/src/components/PlantResponseCard/index.ts`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`

**引用了谁（内部依赖）**
（无）

### `PlantResponseCard.tsx`
- 作用/意义: T3.6 PlantResponseCard - 主组件
- 路径: `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/PlantResponseCard/AbnormalityAlert.tsx`
- `frontend/src/components/PlantResponseCard/ConfidenceBar.tsx`
- `frontend/src/components/PlantResponseCard/EvidenceList.tsx`
- `frontend/src/components/PlantResponseCard/TrendBadge.tsx`
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

### `TrendBadge.tsx`
- 作用/意义: T3.2 TrendBadge - 趋势标签组件
- 路径: `frontend/src/components/PlantResponseCard/TrendBadge.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/pages/DailyDecision.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/types/predict.ts`
