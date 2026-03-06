"""多源检索器

P7-01: RAG 核心组件迁移
支持系统文献 + 用户文献的隔离检索
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger


class SourceType(str, Enum):
    """文献来源类型"""
    SYSTEM = "system"  # 系统文献 (FAO56 等)
    USER = "user"      # 用户上传文献


@dataclass
class RAGResult:
    """检索结果"""
    doc_id: str
    content: str
    score: float
    source_type: SourceType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "source_type": self.source_type.value,
            "metadata": self.metadata
        }


@dataclass
class MultiSourceConfig:
    """多源检索配置"""
    # Milvus 配置
    milvus_uri: str = "http://localhost:19530"
    system_collection: str = "greenhouse_bge_m3"
    user_collection: str = "cucumber_user_literature"

    # 权重配置
    system_weight: float = 1.5
    user_weight: float = 0.8

    # 混合检索配置
    use_hybrid: bool = True
    sparse_weight: float = 0.3
    dense_weight: float = 0.7

    # 默认返回数量
    default_top_k: int = 5


class MultiSourceRetriever:
    """多源文献检索器

    支持:
    - 系统文献检索 (只读)
    - 用户文献检索 (可写)
    - 混合检索 (稀疏+稠密)
    - 加权排序
    """

    def __init__(
        self,
        config: Optional[MultiSourceConfig] = None,
        embedder=None
    ):
        """
        初始化多源检索器

        Args:
            config: 检索配置
            embedder: 向量化器实例
        """
        self.config = config or MultiSourceConfig()
        self._embedder = embedder
        self._milvus_client = None
        self._mongo_client = None
        self._connected = False

        logger.info("MultiSourceRetriever 初始化完成")

    def _ensure_connected(self):
        """确保已连接到数据库"""
        if self._connected:
            return

        try:
            from pymilvus import connections, Collection, utility

            # 连接 Milvus
            connections.connect(uri=self.config.milvus_uri)

            # 检查集合是否存在
            if utility.has_collection(self.config.system_collection):
                self._system_col = Collection(self.config.system_collection)
                self._system_col.load()
                logger.info(f"系统集合 {self.config.system_collection} 已加载")
            else:
                self._system_col = None
                logger.warning(f"系统集合 {self.config.system_collection} 不存在")

            if utility.has_collection(self.config.user_collection):
                self._user_col = Collection(self.config.user_collection)
                self._user_col.load()
                logger.info(f"用户集合 {self.config.user_collection} 已加载")
            else:
                self._user_col = None
                logger.info(f"用户集合 {self.config.user_collection} 不存在，将在首次写入时创建")

            self._connected = True

        except ImportError:
            logger.warning("pymilvus 未安装，Milvus 检索不可用")
            self._system_col = None
            self._user_col = None

        except Exception as e:
            logger.warning(f"Milvus 连接失败: {e}")
            self._system_col = None
            self._user_col = None

    @property
    def is_available(self) -> bool:
        """检查检索器是否可用"""
        try:
            self._ensure_connected()
            return self._system_col is not None or self._user_col is not None
        except Exception:
            return False

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        sources: Optional[List[str]] = None
    ) -> List[RAGResult]:
        """
        多源检索

        Args:
            query: 查询文本
            top_k: 返回数量
            sources: 检索范围 ["system"] / ["user"] / ["system", "user"]

        Returns:
            合并后的检索结果，按加权分数排序
        """
        self._ensure_connected()

        top_k = top_k or self.config.default_top_k
        sources = sources or ["system", "user"]

        results = []

        # 获取查询向量
        query_embedding = self._get_query_embedding(query)

        if query_embedding is None:
            logger.warning("无法获取查询向量")
            return []

        # 从系统集合检索
        if "system" in sources and self._system_col is not None:
            system_results = self._search_collection(
                self._system_col,
                query_embedding,
                top_k,
                SourceType.SYSTEM,
                self.config.system_weight
            )
            results.extend(system_results)

        # 从用户集合检索
        if "user" in sources and self._user_col is not None:
            user_results = self._search_collection(
                self._user_col,
                query_embedding,
                top_k,
                SourceType.USER,
                self.config.user_weight
            )
            results.extend(user_results)

        # 按加权分数排序，取 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def search_system_only(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RAGResult]:
        """仅检索系统文献"""
        return self.search(query, top_k, sources=["system"])

    def search_user_only(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RAGResult]:
        """仅检索用户文献"""
        return self.search(query, top_k, sources=["user"])

    def _get_query_embedding(self, query: str) -> Optional[Dict[str, Any]]:
        """获取查询向量"""
        if self._embedder is None:
            from .embedder import BGEM3Embedder
            self._embedder = BGEM3Embedder()

        if not self._embedder.is_available:
            return None

        result = self._embedder.encode_queries(query)
        return {
            "dense": result.dense[0] if result.dense else None,
            "sparse": result.sparse[0] if result.sparse else None
        }

    def _search_collection(
        self,
        collection,
        query_embedding: Dict[str, Any],
        top_k: int,
        source_type: SourceType,
        weight: float
    ) -> List[RAGResult]:
        """在指定集合中检索"""
        try:
            from pymilvus import AnnSearchRequest, RRFRanker

            requests = []

            # 稀疏向量检索
            if query_embedding.get("sparse") and self.config.use_hybrid:
                sparse_req = AnnSearchRequest(
                    data=[query_embedding["sparse"]],
                    anns_field="sparse_vector",
                    param={"metric_type": "IP"},
                    limit=top_k
                )
                requests.append(sparse_req)

            # 稠密向量检索
            if query_embedding.get("dense"):
                dense_req = AnnSearchRequest(
                    data=[query_embedding["dense"]],
                    anns_field="dense_vector",
                    param={"metric_type": "IP"},
                    limit=top_k
                )
                requests.append(dense_req)

            if not requests:
                return []

            # 混合检索
            if len(requests) > 1:
                search_results = collection.hybrid_search(
                    requests,
                    rerank=RRFRanker(),
                    limit=top_k,
                    output_fields=["unique_id", "text"]
                )[0]
            else:
                # 单一检索
                search_results = collection.search(
                    data=[query_embedding["dense"]],
                    anns_field="dense_vector",
                    param={"metric_type": "IP"},
                    limit=top_k,
                    output_fields=["unique_id", "text"]
                )[0]

            # 转换结果
            results = []
            for hit in search_results:
                result = RAGResult(
                    doc_id=hit.entity.get("unique_id", hit.id),
                    content=hit.entity.get("text", ""),
                    score=hit.score * weight,  # 应用权重
                    source_type=source_type,
                    metadata={"original_score": hit.score}
                )
                results.append(result)

            return results

        except Exception as e:
            logger.warning(f"集合检索失败: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        self._ensure_connected()

        stats = {
            "system_available": self._system_col is not None,
            "user_available": self._user_col is not None,
            "system_count": 0,
            "user_count": 0
        }

        try:
            if self._system_col:
                stats["system_count"] = self._system_col.num_entities
            if self._user_col:
                stats["user_count"] = self._user_col.num_entities
        except Exception as e:
            logger.warning(f"获取集合统计失败: {e}")

        return stats
