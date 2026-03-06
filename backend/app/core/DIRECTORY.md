# `backend/app/core` 目录说明

## 目录定位
后端核心基础设施：配置加载、环境变量、多配置切换等。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `config.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Core module
- 路径: `backend/app/core/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/app/__init__.py`

### `config.py`
- 作用/意义: 配置管理模块 - 管理 API Key、Base URL 等配置
- 路径: `backend/app/core/config.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/settings.py`
- `backend/app/services/llm_service.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `json`
- `pathlib`
- `pydantic`
- `pydantic_settings`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/settings.py`
- `backend/app/services/llm_service.py`

**本目录引用了谁（跨目录）**
- `backend/app/__init__.py`
