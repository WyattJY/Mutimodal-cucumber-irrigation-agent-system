# `frontend/src/pages` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `DailyDecision.tsx`
- `Dashboard.tsx`
- `History.tsx`
- `Knowledge.tsx`
- `NotFound.tsx`
- `PlantResponse.tsx`
- `Predict.tsx`
- `Settings.tsx`
- `Vision.tsx`
- `Weekly.tsx`

## 脚本/模块说明（本目录内）
### `DailyDecision.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/DailyDecision.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
- `frontend/src/components/ImageCompare/index.ts`
- `frontend/src/components/OverrideModal.tsx`
- `frontend/src/components/PlantResponseCard/index.ts`
- `frontend/src/components/TrendChart.tsx`
- `frontend/src/hooks/useDailyPredict.ts`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/services/imageService.ts`
- `frontend/src/types/episode.ts`

**引用了谁（外部依赖）**
- `react`

### `Dashboard.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/Dashboard.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
- `frontend/src/components/OverrideModal.tsx`
- `frontend/src/components/TrendChart.tsx`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/services/imageService.ts`

**引用了谁（外部依赖）**
- `react`
- `react-router-dom`

### `History.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/History.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
- `frontend/src/components/TrendChart.tsx`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/types/index.ts`

**引用了谁（外部依赖）**
- `react`

### `Knowledge.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/Knowledge.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
- `frontend/src/components/RAGReferences/index.ts`
- `frontend/src/stores/chatStore.ts`

**引用了谁（外部依赖）**
- `react`

### `NotFound.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/NotFound.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react-router-dom`

### `PlantResponse.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/PlantResponse.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react-router-dom`

### `Predict.tsx`
- 作用/意义: Predict - 灌水量预测页面
- 路径: `frontend/src/pages/Predict.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
- `frontend/src/components/prediction/index.ts`
- `frontend/src/components/vision/index.ts`

**引用了谁（外部依赖）**
- `react`
- `react-hot-toast`

### `Settings.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/Settings.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`
- `react-hot-toast`

### `Vision.tsx`
- 作用/意义: Vision - 视觉分析页面
- 路径: `frontend/src/pages/Vision.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
- `frontend/src/components/vision/index.ts`

**引用了谁（外部依赖）**
- `react`
- `react-hot-toast`

### `Weekly.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/pages/Weekly.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/TrendChart.tsx`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/types/index.ts`

**引用了谁（外部依赖）**
- `react`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/routes/index.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/components/ImageCompare/index.ts`
- `frontend/src/components/OverrideModal.tsx`
- `frontend/src/components/PlantResponseCard/index.ts`
- `frontend/src/components/RAGReferences/index.ts`
- `frontend/src/components/TrendChart.tsx`
- `frontend/src/components/prediction/index.ts`
- `frontend/src/components/vision/index.ts`
- `frontend/src/hooks/useDailyPredict.ts`
- `frontend/src/hooks/useEpisodes.ts`
- `frontend/src/services/imageService.ts`
- `frontend/src/stores/chatStore.ts`
- `frontend/src/types/episode.ts`
- （还有 1 项未展开）
