# `frontend/src/hooks` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `index.ts`
- `useDailyPredict.ts`
- `useEpisodes.ts`
- `useKnowledgeSearch.ts`
- `useToast.ts`
- `useWeeklySummary.ts`

## 脚本/模块说明（本目录内）
### `index.ts`
- 作用/意义: Hooks - Unified Export
- 路径: `frontend/src/hooks/index.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

### `useDailyPredict.ts`
- 作用/意义: T3.1 useDailyPredict Hook 调用每日预测 API 的 React Hook
- 路径: `frontend/src/hooks/useDailyPredict.ts`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`

**引用了谁（内部依赖）**
- `frontend/src/services/index.ts`
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `react`

### `useEpisodes.ts`
- 作用/意义: Episode Hooks - 决策数据 Query Hooks
- 路径: `frontend/src/hooks/useEpisodes.ts`

**被谁引用/调用（代码级）**
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Weekly.tsx`

**引用了谁（内部依赖）**
- `frontend/src/services/index.ts`
- `frontend/src/types/index.ts`

**引用了谁（外部依赖）**
- `@tanstack`

### `useKnowledgeSearch.ts`
- 作用/意义: Knowledge Hooks - 知识库 Query Hooks
- 路径: `frontend/src/hooks/useKnowledgeSearch.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/services/index.ts`
- `frontend/src/types/index.ts`

**引用了谁（外部依赖）**
- `@tanstack`

### `useToast.ts`
- 作用/意义: Toast Hook - 封装 react-hot-toast
- 路径: `frontend/src/hooks/useToast.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react-hot-toast`

### `useWeeklySummary.ts`
- 作用/意义: Weekly Hooks - 周报 Query Hooks
- 路径: `frontend/src/hooks/useWeeklySummary.ts`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/services/index.ts`

**引用了谁（外部依赖）**
- `@tanstack`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/pages/DailyDecision.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Weekly.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/services/index.ts`
- `frontend/src/types/index.ts`
- `frontend/src/types/predict.ts`
