# `frontend/src/stores` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `chatStore.ts`

## 脚本/模块说明（本目录内）
### `chatStore.ts`
- 作用/意义: Chat Store - 聊天状态管理
- 路径: `frontend/src/stores/chatStore.ts`

**被谁引用/调用（代码级）**
- `frontend/src/components/chat/ChatMessage.tsx`
- `frontend/src/components/chat/ChatPanel.tsx`
- `frontend/src/components/layout/Layout.tsx`
- `frontend/src/components/layout/Sidebar/Sidebar.tsx`
- `frontend/src/pages/Knowledge.tsx`

**引用了谁（内部依赖）**
- `frontend/src/types/predict.ts`

**引用了谁（外部依赖）**
- `zustand`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/components/chat/ChatMessage.tsx`
- `frontend/src/components/chat/ChatPanel.tsx`
- `frontend/src/components/layout/Layout.tsx`
- `frontend/src/components/layout/Sidebar/Sidebar.tsx`
- `frontend/src/pages/Knowledge.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/types/predict.ts`
