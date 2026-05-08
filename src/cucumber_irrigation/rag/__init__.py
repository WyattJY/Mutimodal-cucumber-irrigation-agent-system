"""RAG 组件模块

Phase 7: RAG 组件迁移与文献管理

功能:
- BGE-M3 向量化
- 多源检索 (系统 + 用户文献)
- 文献上传与管理
- 文档分块处理
- 本地 JSON 知识库 (无需外部服务)
"""

from .embedder import BGEM3Embedder
from .retriever import MultiSourceRetriever
from .chunker import DocumentChunker
from .literature_api import LiteratureUploadService
from .indexer import LiteratureIndexer
from .json_store import JsonKnowledgeStore

__all__ = [
    "BGEM3Embedder",
    "MultiSourceRetriever",
    "DocumentChunker",
    "LiteratureUploadService",
    "LiteratureIndexer",
    "JsonKnowledgeStore",
]
