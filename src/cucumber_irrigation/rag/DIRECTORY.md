# `src/cucumber_irrigation/rag` 目录说明

## 目录定位
RAG 组件：分块/向量化/索引/检索、本地 JSON 知识库与 CLI。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `chunker.py`
- `cli.py`
- `embedder.py`
- `indexer.py`
- `json_store.py`
- `literature_api.py`
- `retriever.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: RAG 组件模块
- 路径: `src/cucumber_irrigation/rag/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

### `chunker.py`
- 作用/意义: 文档分块处理器
- 路径: `src/cucumber_irrigation/rag/chunker.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/rag/indexer.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `PyPDF2`
- `dataclasses`
- `enum`
- `hashlib`
- `loguru`
- `os`
- `pathlib`
- `pdfplumber`
- `re`
- `typing`

### `cli.py`
- 作用/意义: 用户文献管理界面 (CLI)
- 路径: `src/cucumber_irrigation/rag/cli.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/rag/indexer.py`
- `src/cucumber_irrigation/rag/literature_api.py`
- `src/cucumber_irrigation/rag/retriever.py`

**引用了谁（外部依赖）**
- `argparse`
- `loguru`
- `pathlib`
- `typing`

### `embedder.py`
- 作用/意义: BGE-M3 向量化器
- 路径: `src/cucumber_irrigation/rag/embedder.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/rag/indexer.py`
- `src/cucumber_irrigation/rag/retriever.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `FlagEmbedding`
- `dataclasses`
- `loguru`
- `os`
- `sentence_transformers`
- `torch`
- `typing`

### `indexer.py`
- 作用/意义: 文献入库服务
- 路径: `src/cucumber_irrigation/rag/indexer.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/rag/cli.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/rag/chunker.py`
- `src/cucumber_irrigation/rag/embedder.py`

**引用了谁（外部依赖）**
- `dataclasses`
- `loguru`
- `pymilvus`
- `typing`

### `json_store.py`
- 作用/意义: 本地 JSON 知识库
- 路径: `src/cucumber_irrigation/rag/json_store.py`

**被谁引用/调用（代码级）**
- `backend/app/api/v1/knowledge.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/services/local_rag_service.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `dataclasses`
- `json`
- `loguru`
- `pathlib`
- `re`
- `typing`

### `literature_api.py`
- 作用/意义: 文献上传 API
- 路径: `src/cucumber_irrigation/rag/literature_api.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/rag/cli.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `dataclasses`
- `datetime`
- `json`
- `loguru`
- `os`
- `pathlib`
- `shutil`
- `typing`
- `uuid`

### `retriever.py`
- 作用/意义: 多源检索器
- 路径: `src/cucumber_irrigation/rag/retriever.py`

**被谁引用/调用（代码级）**
- `src/cucumber_irrigation/rag/cli.py`

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/rag/embedder.py`

**引用了谁（外部依赖）**
- `dataclasses`
- `enum`
- `loguru`
- `pymilvus`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/app/api/v1/knowledge.py`
- `scripts/run_weekly_real.py`
- `src/cucumber_irrigation/services/local_rag_service.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
