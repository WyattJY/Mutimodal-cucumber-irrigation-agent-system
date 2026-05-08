# `backend/app` 目录说明

## 目录定位
后端应用主包 `app`：FastAPI 应用入口、API 路由注册、服务编排与模型调用。

[上级目录](../DIRECTORY.md)

## 子目录
- `api/` → [`api/DIRECTORY.md`](api/DIRECTORY.md)
- `core/` → [`core/DIRECTORY.md`](core/DIRECTORY.md)
- `ml/` → [`ml/DIRECTORY.md`](ml/DIRECTORY.md)
- `models/` → [`models/DIRECTORY.md`](models/DIRECTORY.md)
- `services/` → [`services/DIRECTORY.md`](services/DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `main.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Empty init file
- 路径: `backend/app/__init__.py`

**被谁引用/调用（代码级）**
- `backend/app/core/__init__.py`
- `backend/app/services/__init__.py`

**引用了谁（内部依赖）**
（无）

### `main.py`
- 作用/意义: Application lifespan handler
- 路径: `backend/app/main.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/episodes.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/memory.py`
- `backend/app/api/v1/override.py`
- `backend/app/api/v1/predict.py`
- `backend/app/api/v1/settings.py`
- `backend/app/api/v1/stats.py`
- `backend/app/api/v1/upload.py`
- `backend/app/api/v1/vision.py`
- （还有 1 项未展开）

**引用了谁（外部依赖）**
- `contextlib`
- `fastapi`
- `pathlib`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
（无）
