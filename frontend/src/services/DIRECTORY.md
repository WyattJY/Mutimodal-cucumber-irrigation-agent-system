# `frontend/src/services` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `api.ts`
- `episodeService.ts`
- `imageService.ts`
- `index.ts`
- `knowledgeService.ts`
- `predictService.ts`
- `weeklyService.ts`

## 脚本/模块说明（本目录内）
### `api.ts`
- 作用/意义: API Configuration - Axios 实例配置
- 路径: `frontend/src/services/api.ts`

**被谁引用/调用（代码级）**
- `frontend/src/services/episodeService.ts`
- `frontend/src/services/imageService.ts`
- `frontend/src/services/knowledgeService.ts`
- `frontend/src/services/predictService.ts`
- `frontend/src/services/weeklyService.ts`

**引用了谁（内部依赖）**
- `frontend/src/types/index.ts`

**引用了谁（外部依赖）**
- `axios`

### `episodeService.ts`
- 作用/意义: Episode Service - 决策数据服务
- 路径: `frontend/src/services/episodeService.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`

### `imageService.ts`
- 作用/意义: Image Service - 图像相关 API
- 路径: `frontend/src/services/imageService.ts`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`

**引用了谁（内部依赖）**
- `frontend/src/services/api.ts`

### `index.ts`
- 作用/意义: Services - Unified Export
- 路径: `frontend/src/services/index.ts`

**被谁引用/调用（代码级）**
- `frontend/src/components/features/FeedbackForm.tsx`
- `frontend/src/components/features/KnowledgePanel.tsx`
- `frontend/src/components/features/PredictionPanel.tsx`
- `frontend/src/components/features/WeeklySummaryCard.tsx`
- `frontend/src/hooks/useDailyPredict.ts`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/hooks/useKnowledgeSearch.ts`
- `frontend/src/hooks/useWeeklySummary.ts`

**引用了谁（内部依赖）**
（无）

### `knowledgeService.ts`
- 作用/意义: Knowledge Service - 知识库服务
- 路径: `frontend/src/services/knowledgeService.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`

### `predictService.ts`
- 作用/意义: Prediction Service - 预测相关 API 服务
- 路径: `frontend/src/services/predictService.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`
- `frontend/src/types/predict.ts`

### `weeklyService.ts`
- 作用/意义: Weekly Service - 周报服务
- 路径: `frontend/src/services/weeklyService.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/components/features/FeedbackForm.tsx`
- `frontend/src/components/features/KnowledgePanel.tsx`
- `frontend/src/components/features/PredictionPanel.tsx`
- `frontend/src/components/features/WeeklySummaryCard.tsx`
- `frontend/src/hooks/useDailyPredict.ts`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/hooks/useKnowledgeSearch.ts`
- `frontend/src/hooks/useWeeklySummary.ts`
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/types/index.ts`
- `frontend/src/types/predict.ts`
