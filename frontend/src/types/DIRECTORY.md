# `frontend/src/types` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `api.ts`
- `episode.ts`
- `index.ts`
- `knowledge.ts`
- `predict.ts`
- `weekly.ts`

## 脚本/模块说明（本目录内）
### `api.ts`
- 作用/意义: API Types - 通用 API 类型定义 API 错误
- 路径: `frontend/src/types/api.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `episode.ts`
- 作用/意义: Episode Types - 灌溉决策数据类型定义 YOLO 检测指标
- 路径: `frontend/src/types/episode.ts`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`

**引用了谁（内部依赖）**
（无）

### `index.ts`
- 作用/意义: Types - Unified Export
- 路径: `frontend/src/types/index.ts`

**被谁引用/调用（代码级）**
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/hooks/useKnowledgeSearch.ts`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Weekly.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/services/episodeService.ts`
- `frontend/src/services/knowledgeService.ts`
- `frontend/src/services/predictService.ts`
- `frontend/src/services/weeklyService.ts`

**引用了谁（内部依赖）**
（无）

### `knowledge.ts`
- 作用/意义: Knowledge Types - 知识库类型定义 知识来源
- 路径: `frontend/src/types/knowledge.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `predict.ts`
- 作用/意义: Predict Types - 预测相关类型定义 预测选项
- 路径: `frontend/src/types/predict.ts`

**被谁引用/调用（代码级）**
- `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`
- `frontend/src/components/RAGReferences/RAGReferences.tsx`
- `frontend/src/components/features/FeedbackForm.tsx`
- `frontend/src/components/features/KnowledgePanel.tsx`
- `frontend/src/components/features/PredictionPanel.tsx`
- `frontend/src/components/features/SourceBadge.tsx`
- `frontend/src/components/features/WeeklySummaryCard.tsx`
- `frontend/src/hooks/useDailyPredict.ts`
- `frontend/src/services/predictService.ts`
- `frontend/src/stores/chatStore.ts`

**引用了谁（内部依赖）**
（无）

### `weekly.ts`
- 作用/意义: Weekly Types - 周报数据类型定义 周统计数据
- 路径: `frontend/src/types/weekly.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/components/PlantResponseCard/PlantResponseCard.tsx`
- `frontend/src/components/RAGReferences/RAGReferences.tsx`
- `frontend/src/components/features/FeedbackForm.tsx`
- `frontend/src/components/features/KnowledgePanel.tsx`
- `frontend/src/components/features/PredictionPanel.tsx`
- `frontend/src/components/features/SourceBadge.tsx`
- `frontend/src/components/features/WeeklySummaryCard.tsx`
- `frontend/src/hooks/useDailyPredict.ts`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/hooks/useKnowledgeSearch.ts`
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/History.tsx`
- （还有 7 项未展开）

**本目录引用了谁（跨目录）**
（无）
