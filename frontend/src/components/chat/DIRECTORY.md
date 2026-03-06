# `frontend/src/components/chat` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `ChatInput.tsx`
- `ChatMessage.tsx`
- `ChatPanel.tsx`
- `index.ts`

## 脚本/模块说明（本目录内）
### `ChatInput.tsx`
- 作用/意义: ChatInput - 聊天输入框组件
- 路径: `frontend/src/components/chat/ChatInput.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/chat/ChatPanel.tsx`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `react`

### `ChatMessage.tsx`
- 作用/意义: ChatMessage - 聊天消息气泡组件
- 路径: `frontend/src/components/chat/ChatMessage.tsx`

**被谁引用/调用（代码级）**
- `frontend/src/components/chat/ChatPanel.tsx`

**引用了谁（内部依赖）**
- `frontend/src/stores/chatStore.ts`

**引用了谁（外部依赖）**
- `clsx`

### `ChatPanel.tsx`
- 作用/意义: ChatPanel - 聊天面板组件 (AGRI-COPILOT)
- 路径: `frontend/src/components/chat/ChatPanel.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/chat/ChatInput.tsx`
- `frontend/src/components/chat/ChatMessage.tsx`
- `frontend/src/stores/chatStore.ts`

**引用了谁（外部依赖）**
- `clsx`
- `react`

### `index.ts`
- 作用/意义: Chat components index
- 路径: `frontend/src/components/chat/index.ts`

**被谁引用/调用（代码级）**
- `frontend/src/components/layout/Layout.tsx`

**引用了谁（内部依赖）**
（无）

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/components/layout/Layout.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/stores/chatStore.ts`
