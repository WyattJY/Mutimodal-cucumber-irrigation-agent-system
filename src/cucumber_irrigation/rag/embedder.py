"""BGE-M3 向量化器

P7-01: RAG 核心组件迁移
支持稀疏+稠密向量生成，用于混合检索
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
import os

import torch
from loguru import logger


@dataclass
class EmbeddingResult:
    """向量化结果"""
    dense: List[List[float]]    # 稠密向量
    sparse: Optional[List[Dict[int, float]]] = None  # 稀疏向量 (词ID -> 权重)


class BGEM3Embedder:
    """BGE-M3 向量化器

    支持:
    - 稠密向量 (Dense Embedding)
    - 稀疏向量 (Lexical/Sparse Embedding)
    - 混合检索 (Hybrid Search)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        use_fp16: bool = True
    ):
        """
        初始化 BGE-M3 向量化器

        Args:
            model_path: 模型路径，None 则从 HuggingFace 下载
            device: 设备 (auto/cpu/cuda)
            use_fp16: 是否使用 FP16
        """
        self.model_path = model_path or "BAAI/bge-m3"
        self.use_fp16 = use_fp16
        self._model = None
        self._tokenizer = None
        self._device = None

        # 确定设备
        if device == "auto":
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self._device = device

        logger.info(f"BGE-M3 Embedder 初始化, 设备: {self._device}")

    def _ensure_model_loaded(self):
        """确保模型已加载 (延迟加载)"""
        if self._model is not None:
            return

        try:
            from FlagEmbedding import BGEM3FlagModel

            logger.info(f"加载 BGE-M3 模型: {self.model_path}")

            self._model = BGEM3FlagModel(
                self.model_path,
                use_fp16=self.use_fp16 and self._device == "cuda"
            )

            logger.info("BGE-M3 模型加载成功")

        except ImportError:
            logger.warning("FlagEmbedding 未安装，使用 sentence-transformers 回退")
            self._load_fallback_model()

        except Exception as e:
            logger.warning(f"BGE-M3 加载失败: {e}, 使用回退模型")
            self._load_fallback_model()

    def _load_fallback_model(self):
        """加载回退模型 (sentence-transformers)"""
        try:
            from sentence_transformers import SentenceTransformer

            fallback_model = "BAAI/bge-small-zh-v1.5"
            logger.info(f"加载回退模型: {fallback_model}")

            self._model = SentenceTransformer(
                fallback_model,
                device=self._device
            )
            self._is_fallback = True

            logger.info("回退模型加载成功")

        except ImportError:
            logger.error("sentence-transformers 也未安装，向量化功能不可用")
            self._model = None

    @property
    def is_available(self) -> bool:
        """检查模型是否可用"""
        try:
            self._ensure_model_loaded()
            return self._model is not None
        except Exception:
            return False

    @property
    def dim(self) -> Dict[str, int]:
        """获取向量维度"""
        self._ensure_model_loaded()

        if hasattr(self._model, 'dim'):
            # FlagEmbedding BGEM3FlagModel
            return {"dense": 1024, "sparse": None}
        elif hasattr(self._model, 'get_sentence_embedding_dimension'):
            # SentenceTransformer
            return {"dense": self._model.get_sentence_embedding_dimension(), "sparse": None}
        else:
            return {"dense": 1024, "sparse": None}

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        return_sparse: bool = True,
        return_dense: bool = True,
        max_length: int = 8192
    ) -> EmbeddingResult:
        """
        编码文本为向量

        Args:
            texts: 文本或文本列表
            batch_size: 批处理大小
            return_sparse: 是否返回稀疏向量
            return_dense: 是否返回稠密向量
            max_length: 最大文本长度

        Returns:
            EmbeddingResult 包含稠密和稀疏向量
        """
        self._ensure_model_loaded()

        if self._model is None:
            logger.warning("模型不可用，返回空向量")
            if isinstance(texts, str):
                texts = [texts]
            return EmbeddingResult(
                dense=[[0.0] * 1024 for _ in texts],
                sparse=None
            )

        if isinstance(texts, str):
            texts = [texts]

        # 使用 FlagEmbedding BGEM3FlagModel
        if hasattr(self._model, 'encode'):
            try:
                output = self._model.encode(
                    texts,
                    batch_size=batch_size,
                    max_length=max_length,
                    return_sparse=return_sparse,
                    return_dense=return_dense
                )

                if isinstance(output, dict):
                    dense = output.get('dense_vecs', [])
                    sparse = output.get('lexical_weights', None)

                    # 转换为列表格式
                    if hasattr(dense, 'tolist'):
                        dense = dense.tolist()

                    return EmbeddingResult(dense=dense, sparse=sparse)
                else:
                    # 直接返回向量
                    if hasattr(output, 'tolist'):
                        output = output.tolist()
                    return EmbeddingResult(dense=output, sparse=None)

            except Exception as e:
                logger.warning(f"FlagEmbedding 编码失败: {e}, 使用回退方法")

        # 使用 SentenceTransformer 回退
        if hasattr(self._model, 'encode'):
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return EmbeddingResult(
                dense=embeddings.tolist() if hasattr(embeddings, 'tolist') else list(embeddings),
                sparse=None
            )

        # 无法编码
        return EmbeddingResult(
            dense=[[0.0] * 1024 for _ in texts],
            sparse=None
        )

    def encode_queries(
        self,
        queries: Union[str, List[str]],
        max_length: int = 512
    ) -> EmbeddingResult:
        """
        编码查询文本 (针对查询优化)

        Args:
            queries: 查询文本
            max_length: 最大长度

        Returns:
            EmbeddingResult
        """
        return self.encode(
            queries,
            max_length=max_length,
            return_sparse=True,
            return_dense=True
        )

    def encode_documents(
        self,
        documents: Union[str, List[str]],
        max_length: int = 8192
    ) -> EmbeddingResult:
        """
        编码文档文本 (针对文档优化)

        Args:
            documents: 文档文本
            max_length: 最大长度

        Returns:
            EmbeddingResult
        """
        return self.encode(
            documents,
            max_length=max_length,
            return_sparse=True,
            return_dense=True
        )
