# `frontend/src/components/features` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 子目录
- `dashboard/` → [`dashboard/DIRECTORY.md`](dashboard/DIRECTORY.md)
- `decision/` → [`decision/DIRECTORY.md`](decision/DIRECTORY.md)
- `history/` → [`history/DIRECTORY.md`](history/DIRECTORY.md)
- `knowledge/` → [`knowledge/DIRECTORY.md`](knowledge/DIRECTORY.md)
- `override/` → [`override/DIRECTORY.md`](override/DIRECTORY.md)
- `plant-response/` → [`plant-response/DIRECTORY.md`](plant-response/DIRECTORY.md)
- `settings/` → [`settings/DIRECTORY.md`](settings/DIRECTORY.md)
- `weekly/` → [`weekly/DIRECTORY.md`](weekly/DIRECTORY.md)

## 本目录文件概览
- `FeedbackForm.tsx`
- `index.ts`
- `KnowledgePanel.tsx`
- `PredictionPanel.tsx`
- `SourceBadge.tsx`
- `WeeklySummaryCard.tsx`

## 脚本/模块说明（本目录内）
### `FeedbackForm.tsx`
- 作用/意义: FeedbackForm - 用户反馈表单
- 路径: `frontend/src/components/features/FeedbackForm.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/common/Button/index.ts`
- `frontend/src/components/common/Card/index.ts`
- `frontend/src/components/common/Spinner/index.ts`
- `frontend/src/services/index.ts`
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

### `index.ts`
- 作用/意义: Feature Components - Unified Export
- 路径: `frontend/src/components/features/index.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `KnowledgePanel.tsx`
- 作用/意义: KnowledgePanel - 知识库面板
- 路径: `frontend/src/components/features/KnowledgePanel.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/common/Button/index.ts`
- `frontend/src/components/common/Card/index.ts`
- `frontend/src/components/common/Spinner/index.ts`
- `frontend/src/services/index.ts`
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

### `PredictionPanel.tsx`
- 作用/意义: PredictionPanel - 预测面板组件
- 路径: `frontend/src/components/features/PredictionPanel.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/common/Badge/index.ts`
- `frontend/src/components/common/Button/index.ts`
- `frontend/src/components/common/Card/index.ts`
- `frontend/src/components/common/Spinner/index.ts`
- `frontend/src/components/features/SourceBadge.tsx`
- `frontend/src/services/index.ts`
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

### `SourceBadge.tsx`
- 作用/意义: SourceBadge - 来源显示组件
- 路径: `frontend/src/components/features/SourceBadge.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/features/PredictionPanel.tsx`

**引用了谁（内部依赖）**
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

### `WeeklySummaryCard.tsx`
- 作用/意义: WeeklySummaryCard - 周报卡片组件
- 路径: `frontend/src/components/features/WeeklySummaryCard.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/common/Button/index.ts`
- `frontend/src/components/common/Card/index.ts`
- `frontend/src/components/common/Spinner/index.ts`
- `frontend/src/services/index.ts`
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
- `frontend/src/components/common/Badge/index.ts`
- `frontend/src/components/common/Button/index.ts`
- `frontend/src/components/common/Card/index.ts`
- `frontend/src/components/common/Spinner/index.ts`
- `frontend/src/services/index.ts`
- `frontend/src/types/predict.ts`
