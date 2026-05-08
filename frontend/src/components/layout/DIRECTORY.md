# `frontend/src/components/layout` 目录说明

## 目录定位
该目录用于承载项目的相关代码/数据/配置；详见下方文件与引用关系。

[上级目录](../DIRECTORY.md)

## 子目录
- `AuroraBackground/` → [`AuroraBackground/DIRECTORY.md`](AuroraBackground/DIRECTORY.md)
- `Header/` → [`Header/DIRECTORY.md`](Header/DIRECTORY.md)
- `MobileMenu/` → [`MobileMenu/DIRECTORY.md`](MobileMenu/DIRECTORY.md)
- `Sidebar/` → [`Sidebar/DIRECTORY.md`](Sidebar/DIRECTORY.md)

## 本目录文件概览
- `index.ts`
- `Layout.tsx`

## 脚本/模块说明（本目录内）
### `index.ts`
- 作用/意义: Layout Components - Unified Export
- 路径: `frontend/src/components/layout/index.ts`

**被谁引用/调用（代码级）**
- `frontend/src/routes/index.tsx`

**引用了谁（内部依赖）**
（无）

### `Layout.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/components/layout/Layout.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/components/chat/index.ts`
- `frontend/src/components/layout/AuroraBackground/index.ts`
- `frontend/src/components/layout/Sidebar/index.ts`
- `frontend/src/stores/chatStore.ts`

**引用了谁（外部依赖）**
- `react`
- `react-router-dom`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `frontend/src/routes/index.tsx`

**本目录引用了谁（跨目录）**
- `frontend/src/components/chat/index.ts`
- `frontend/src/stores/chatStore.ts`
