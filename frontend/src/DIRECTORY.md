# `frontend/src` 目录说明

## 目录定位
前端源码根目录：按 components/pages/services/hooks/store 等组织。

[上级目录](../DIRECTORY.md)

## 子目录
- `assets/` → [`assets/DIRECTORY.md`](assets/DIRECTORY.md)
- `components/` → [`components/DIRECTORY.md`](components/DIRECTORY.md)
- `hooks/` → [`hooks/DIRECTORY.md`](hooks/DIRECTORY.md)
- `pages/` → [`pages/DIRECTORY.md`](pages/DIRECTORY.md)
- `routes/` → [`routes/DIRECTORY.md`](routes/DIRECTORY.md)
- `services/` → [`services/DIRECTORY.md`](services/DIRECTORY.md)
- `store/` → [`store/DIRECTORY.md`](store/DIRECTORY.md)
- `stores/` → [`stores/DIRECTORY.md`](stores/DIRECTORY.md)
- `styles/` → [`styles/DIRECTORY.md`](styles/DIRECTORY.md)
- `types/` → [`types/DIRECTORY.md`](types/DIRECTORY.md)
- `utils/` → [`utils/DIRECTORY.md`](utils/DIRECTORY.md)

## 本目录文件概览
- `index.css`
- `main.tsx`

## 脚本/模块说明（本目录内）
### `main.tsx`
- 作用/意义: （建议补充文件头注释/模块 docstring 以便自动提取）
- 路径: `frontend/src/main.tsx`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `frontend/src/index.css`
- `frontend/src/routes/index.tsx`
- `frontend/src/styles/cankao.css`

**引用了谁（外部依赖）**
- `@tanstack`
- `react`
- `react-dom`
- `react-hot-toast`
- `react-router-dom`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
（无）
