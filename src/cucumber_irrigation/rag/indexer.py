"""文献入库服务

P7-04: 文献入库服务（隔离）
将分块后的文献向量化并入库到用户专属集合
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class IndexerConfig:
    """索引器配置"""
    # Milvus 配置
    milvus_uri: str = "http://localhost:19530"
    user_collection: str = "cucumber_user_literature"

    # 向量配置
    dense_dim: int = 1024
    max_text_length: int = 512
    id_max_length: int = 100

    # 批处理配置
    batch_size: int = 50


class LiteratureIndexer:
    """文献入库服务

    功能:
    - 分块向量化
    - 入库到用户专属集合
    - 确保不污染系统文献

    数据隔离原则:
    - 用户文献只能写入 cucumber_user_literature (Milvus)
    - 用户文献只能写入 cucumber_irrigation.user_docs (MongoDB)
    - 系统集合 (greenhouse_bge_m3) 为只读
    """

    def __init__(
        self,
        config: Optional[IndexerConfig] = None,
        embedder=None,
        chunker=None,
        mongo_client=None
    ):
        """
        初始化索引器

        Args:
            config: 索引配置
            embedder: 向量化器
            chunker: 分块器
            mongo_client: MongoDB 客户端
        """
        self.config = config or IndexerConfig()
        self._embedder = embedder
        self._chunker = chunker
        self._mongo_client = mongo_client
        self._collection = None
        self._initialized = False

        logger.info("LiteratureIndexer 初始化完成")

    def _ensure_initialized(self):
        """确保已初始化"""
        if self._initialized:
            return

        try:
            from pymilvus import (
                connections, Collection, CollectionSchema,
                FieldSchema, DataType, utility
            )

            # 连接 Milvus
            connections.connect(uri=self.config.milvus_uri)

            # 定义集合 schema
            fields = [
                FieldSchema(
                    name="unique_id",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    max_length=self.config.id_max_length
                ),
                FieldSchema(
                    name="text",
                    dtype=DataType.VARCHAR,
                    max_length=self.config.max_text_length
                ),
                FieldSchema(
                    name="source_id",
                    dtype=DataType.VARCHAR,
                    max_length=self.config.id_max_length
                ),
                FieldSchema(
                    name="source_type",
                    dtype=DataType.VARCHAR,
                    max_length=20
                ),
                FieldSchema(
                    name="dense_vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.config.dense_dim
                ),
            ]
            schema = CollectionSchema(fields, description="用户文献集合")

            # 创建或加载集合
            if not utility.has_collection(self.config.user_collection):
                self._collection = Collection(
                    self.config.user_collection,
                    schema,
                    consistency_level="Strong"
                )
                logger.info(f"创建用户集合: {self.config.user_collection}")

                # 创建索引
                dense_index = {"index_type": "AUTOINDEX", "metric_type": "IP"}
                self._collection.create_index("dense_vector", dense_index)
            else:
                self._collection = Collection(self.config.user_collection)
                logger.info(f"加载用户集合: {self.config.user_collection}")

            self._collection.load()
            self._initialized = True

        except ImportError:
            logger.warning("pymilvus 未安装，索引功能不可用")

        except Exception as e:
            logger.warning(f"Milvus 初始化失败: {e}")

    def _ensure_embedder(self):
        """确保向量化器已加载"""
        if self._embedder is None:
            from .embedder import BGEM3Embedder
            self._embedder = BGEM3Embedder()

    def _ensure_chunker(self):
        """确保分块器已加载"""
        if self._chunker is None:
            from .chunker import DocumentChunker
            self._chunker = DocumentChunker()

    @property
    def is_available(self) -> bool:
        """检查索引器是否可用"""
        try:
            self._ensure_initialized()
            return self._collection is not None
        except Exception:
            return False

    def index_literature(
        self,
        file_path: str,
        literature_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        索引文献

        Args:
            file_path: 文件路径
            literature_id: 文献 ID
            metadata: 元数据

        Returns:
            索引的分块数量
        """
        self._ensure_initialized()
        self._ensure_embedder()
        self._ensure_chunker()

        if self._collection is None:
            logger.warning("Milvus 不可用，无法索引")
            return 0

        # 分块
        chunks = self._chunker.chunk_file(
            file_path,
            source_id=literature_id,
            is_user=True,
            metadata=metadata
        )

        if not chunks:
            logger.warning(f"文件分块为空: {file_path}")
            return 0

        # 向量化
        texts = [chunk.content for chunk in chunks]
        embeddings = self._embedder.encode_documents(texts)

        if not embeddings.dense:
            logger.warning("向量化失败")
            return 0

        # 批量入库
        indexed_count = 0

        for i in range(0, len(chunks), self.config.batch_size):
            batch_chunks = chunks[i:i + self.config.batch_size]
            batch_vectors = embeddings.dense[i:i + self.config.batch_size]

            entities = [
                [chunk.chunk_id for chunk in batch_chunks],  # unique_id
                [chunk.content[:self.config.max_text_length] for chunk in batch_chunks],  # text
                [chunk.source_id for chunk in batch_chunks],  # source_id
                [chunk.source_type for chunk in batch_chunks],  # source_type
                batch_vectors,  # dense_vector
            ]

            try:
                self._collection.insert(entities)
                indexed_count += len(batch_chunks)
            except Exception as e:
                logger.warning(f"批量插入失败: {e}")

        # 保存到 MongoDB (如果可用)
        self._save_chunks_to_mongo(chunks, metadata)

        logger.info(f"文献 {literature_id} 索引完成: {indexed_count} 个分块")
        return indexed_count

    def index_chunks(
        self,
        chunks,
        literature_id: str
    ) -> int:
        """
        索引分块列表

        Args:
            chunks: 分块列表
            literature_id: 文献 ID

        Returns:
            索引的分块数量
        """
        self._ensure_initialized()
        self._ensure_embedder()

        if self._collection is None or not chunks:
            return 0

        # 向量化
        texts = [chunk.content for chunk in chunks]
        embeddings = self._embedder.encode_documents(texts)

        if not embeddings.dense:
            return 0

        # 入库
        entities = [
            [chunk.chunk_id for chunk in chunks],
            [chunk.content[:self.config.max_text_length] for chunk in chunks],
            [chunk.source_id for chunk in chunks],
            [chunk.source_type for chunk in chunks],
            embeddings.dense,
        ]

        try:
            self._collection.insert(entities)
            return len(chunks)
        except Exception as e:
            logger.warning(f"插入失败: {e}")
            return 0

    def delete_literature(self, literature_id: str) -> bool:
        """
        删除文献的所有分块

        Args:
            literature_id: 文献 ID

        Returns:
            是否删除成功
        """
        self._ensure_initialized()

        if self._collection is None:
            return False

        try:
            # 删除 Milvus 中的分块
            expr = f'source_id == "{literature_id}"'
            self._collection.delete(expr)

            # 删除 MongoDB 中的分块
            if self._mongo_client:
                try:
                    db = self._mongo_client["cucumber_irrigation"]
                    db["user_docs"].delete_many({"source_id": literature_id})
                except Exception as e:
                    logger.warning(f"MongoDB 删除失败: {e}")

            logger.info(f"文献 {literature_id} 的所有分块已删除")
            return True

        except Exception as e:
            logger.warning(f"删除失败: {e}")
            return False

    def rebuild_index(self, literature_id: str, file_path: str) -> int:
        """
        重建文献索引

        Args:
            literature_id: 文献 ID
            file_path: 文件路径

        Returns:
            新索引的分块数量
        """
        # 先删除旧索引
        self.delete_literature(literature_id)

        # 重新索引
        return self.index_literature(file_path, literature_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计"""
        self._ensure_initialized()

        stats = {
            "available": self._collection is not None,
            "collection": self.config.user_collection,
            "entity_count": 0
        }

        if self._collection:
            try:
                stats["entity_count"] = self._collection.num_entities
            except Exception as e:
                logger.warning(f"获取统计失败: {e}")

        return stats

    def _save_chunks_to_mongo(
        self,
        chunks,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """保存分块到 MongoDB"""
        if self._mongo_client is None:
            return

        try:
            db = self._mongo_client["cucumber_irrigation"]
            collection = db["user_docs"]

            docs = []
            for chunk in chunks:
                doc = chunk.to_dict()
                if metadata:
                    doc["literature_metadata"] = metadata
                docs.append(doc)

            if docs:
                collection.insert_many(docs)

        except Exception as e:
            logger.warning(f"MongoDB 保存失败: {e}")
