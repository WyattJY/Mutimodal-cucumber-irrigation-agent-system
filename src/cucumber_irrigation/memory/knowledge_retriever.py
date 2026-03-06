from __future__ import annotations
"""L4 知识检索器

Milvus 向量检索 + FAO56 优先级
参考: task1.md P3-06, P3-07, requirements1.md 4.6节
"""

from typing import Optional, List, Literal
from dataclasses import dataclass, field
import os

from ..models.anomaly import RAGResult


# 异常类型到检索查询的映射模板
QUERY_TEMPLATES = {
    # A2 长势矛盾
    "trend_conflict": (
        "cucumber water stress irrigation adjustment crop coefficient Kc "
        "under stress conditions plant {abnormality} water requirement "
        "growth stage: {stage}"
    ),
    # A3 环境异常
    "high_humidity": "high humidity greenhouse irrigation reduction disease prevention",
    "high_temperature": "high temperature water stress crop evapotranspiration cooling",
    "low_light": "low light photosynthesis reduction irrigation adjustment",
    # 生育期查询
    "vegetative": "cucumber vegetative stage Kc leaf growth water requirement",
    "flowering": "cucumber flowering stage Kc flower development water stress",
    "fruiting": "cucumber fruiting stage Kc fruit development irrigation",
    "mixed": "cucumber transition growth stage Kc adjustment"
}


@dataclass
class RetrievalConfig:
    """检索配置"""
    top_k: int = 3
    fao56_weight: float = 1.5  # FAO56 优先权重
    max_tokens_per_snippet: int = 200
    prefer_fao56: bool = True
    collection_name: str = "greenhouse_bge_m3"

    # 数据隔离: 可选的数据源过滤
    source_filter: Optional[Literal["system", "user", "all"]] = "all"


class KnowledgeRetriever:
    """L4 知识检索器

    支持:
    - Milvus 混合检索 (稀疏+稠密向量)
    - FAO56 优先返回
    - 异常类型查询模板
    - 生育期知识检索
    - 数据隔离 (系统文献 vs 用户文献)
    """

    def __init__(
        self,
        milvus_uri: Optional[str] = None,
        mongo_client=None,
        config: Optional[RetrievalConfig] = None,
        embedding_model_path: Optional[str] = None
    ):
        """
        初始化检索器

        Args:
            milvus_uri: Milvus 连接 URI
            mongo_client: MongoDB 客户端 (用于获取文档原文)
            config: 检索配置
            embedding_model_path: BGE-M3 模型路径
        """
        self.config = config or RetrievalConfig()
        self.mongo_client = mongo_client
        self.milvus_uri = milvus_uri
        self.embedding_model_path = embedding_model_path

        # 延迟初始化 (需要 Milvus 连接)
        self._collection = None
        self._embedding_handler = None
        self._mongo_collection = None
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化 Milvus 和 BGE-M3"""
        if self._initialized:
            return

        try:
            from pymilvus import connections, Collection
            from pymilvus.model.hybrid import BGEM3EmbeddingFunction

            # 连接 Milvus
            if self.milvus_uri:
                connections.connect(uri=self.milvus_uri)

            # 初始化集合
            self._collection = Collection(self.config.collection_name)
            self._collection.load()

            # 初始化嵌入模型
            if self.embedding_model_path:
                self._embedding_handler = BGEM3EmbeddingFunction(
                    model_name=self.embedding_model_path
                )

            # 初始化 MongoDB 集合
            if self.mongo_client:
                self._mongo_collection = self.mongo_client["greenhouse_db"]["literature_chunks"]

            self._initialized = True
        except ImportError:
            # Milvus 未安装，使用 mock 模式
            self._initialized = True
        except Exception as e:
            print(f"Warning: Failed to initialize Milvus: {e}")
            self._initialized = True

    def build_query(
        self,
        anomaly_type: Optional[str] = None,
        growth_stage: Optional[str] = None,
        abnormality: Optional[str] = None,
        custom_query: Optional[str] = None
    ) -> str:
        """
        构建检索查询

        Args:
            anomaly_type: 异常类型 (trend_conflict, high_humidity 等)
            growth_stage: 生育期 (vegetative, flowering, fruiting, mixed)
            abnormality: 异常详情 (用于 trend_conflict)
            custom_query: 自定义查询

        Returns:
            检索查询字符串
        """
        if custom_query:
            return custom_query

        # 优先使用异常类型模板
        if anomaly_type and anomaly_type in QUERY_TEMPLATES:
            template = QUERY_TEMPLATES[anomaly_type]
            return template.format(
                abnormality=abnormality or "unknown",
                stage=growth_stage or "unknown"
            )

        # 使用生育期模板
        if growth_stage and growth_stage in QUERY_TEMPLATES:
            return QUERY_TEMPLATES[growth_stage]

        # 默认查询
        return "cucumber irrigation water requirement greenhouse"

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None
    ) -> List[RAGResult]:
        """
        执行向量检索

        Args:
            query: 检索查询
            top_k: 返回数量
            source_filter: 数据源过滤 (system/user/all)

        Returns:
            RAGResult 列表
        """
        self._lazy_init()

        top_k = top_k or self.config.top_k
        source_filter = source_filter or self.config.source_filter

        # 如果 Milvus 未正确初始化，返回空结果
        if not self._collection or not self._embedding_handler:
            return self._mock_search(query, top_k)

        try:
            return self._milvus_search(query, top_k, source_filter)
        except Exception as e:
            print(f"Warning: Milvus search failed: {e}")
            return self._mock_search(query, top_k)

    def _milvus_search(
        self,
        query: str,
        top_k: int,
        source_filter: Optional[str]
    ) -> List[RAGResult]:
        """执行 Milvus 混合检索"""
        from pymilvus import AnnSearchRequest, RRFRanker

        # 生成查询向量
        query_embeddings = self._embedding_handler.encode_queries([query])

        # 构建混合检索请求
        search_requests = [
            AnnSearchRequest(
                [query_embeddings["sparse"][[0]]],
                "sparse_vector",
                {"metric_type": "IP", "params": {}},
                limit=top_k * 2,  # 多检索一些用于重排
            ),
            AnnSearchRequest(
                [query_embeddings["dense"][0]],
                "dense_vector",
                {"metric_type": "IP", "params": {}},
                limit=top_k * 2,
            ),
        ]

        # 执行混合检索
        results = self._collection.hybrid_search(
            search_requests,
            rerank=RRFRanker(),
            limit=top_k * 2,
            output_fields=["unique_id", "text"],
        )[0]

        # 转换为 RAGResult
        rag_results = []
        for result in results:
            unique_id = result["id"]

            # 从 MongoDB 获取完整文档
            doc = None
            if self._mongo_collection:
                doc = self._mongo_collection.find_one({"unique_id": unique_id})

            if doc:
                metadata = doc.get("metadata", {})
                is_fao56 = metadata.get("is_fao56", False)

                # 应用数据源过滤
                doc_source = "system" if is_fao56 else "user"
                if source_filter == "system" and not is_fao56:
                    continue
                if source_filter == "user" and is_fao56:
                    continue

                rag_results.append(RAGResult(
                    doc_id=unique_id,
                    snippet=doc.get("page_content", result.get("text", "")),
                    score=result.distance * (self.config.fao56_weight if is_fao56 else 1.0),
                    source=metadata.get("source", "unknown"),
                    metadata={
                        "is_fao56": is_fao56,
                        "chapter": metadata.get("chapter"),
                        "page": metadata.get("page"),
                        "content_type": metadata.get("content_type")
                    }
                ))
            else:
                # MongoDB 无记录，使用 Milvus 结果
                rag_results.append(RAGResult(
                    doc_id=unique_id,
                    snippet=result.get("text", ""),
                    score=result.distance,
                    source="milvus",
                    metadata={}
                ))

        # 按分数排序并截取 top_k
        rag_results.sort(key=lambda x: x.score, reverse=True)

        # FAO56 优先: 如果配置了优先返回 FAO56
        if self.config.prefer_fao56:
            fao56_results = [r for r in rag_results if r.metadata.get("is_fao56")]
            other_results = [r for r in rag_results if not r.metadata.get("is_fao56")]
            rag_results = fao56_results + other_results

        return rag_results[:top_k]

    def _mock_search(self, query: str, top_k: int) -> List[RAGResult]:
        """Mock 检索 (Milvus 不可用时)"""
        # 返回空列表或基于关键词的简单匹配
        return []

    def search_by_anomaly(
        self,
        anomaly_type: str,
        growth_stage: Optional[str] = None,
        abnormality: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[RAGResult]:
        """
        根据异常类型检索知识

        Args:
            anomaly_type: 异常类型
            growth_stage: 生育期
            abnormality: 异常详情
            top_k: 返回数量

        Returns:
            RAGResult 列表
        """
        query = self.build_query(
            anomaly_type=anomaly_type,
            growth_stage=growth_stage,
            abnormality=abnormality
        )
        return self.search(query, top_k=top_k)

    def search_by_growth_stage(
        self,
        growth_stage: str,
        top_k: Optional[int] = None
    ) -> List[RAGResult]:
        """
        根据生育期检索知识

        Args:
            growth_stage: 生育期
            top_k: 返回数量

        Returns:
            RAGResult 列表
        """
        query = self.build_query(growth_stage=growth_stage)
        return self.search(query, top_k=top_k)

    def get_fao56_kc(self, growth_stage: str) -> Optional[dict]:
        """
        获取 FAO56 作物系数

        Args:
            growth_stage: 生育期

        Returns:
            Kc 系数信息
        """
        # FAO56 黄瓜作物系数 (Table 12)
        kc_values = {
            "vegetative": {"Kc_ini": 0.6, "Kc_mid": 1.0, "Kc_end": 0.75},
            "flowering": {"Kc_ini": 0.6, "Kc_mid": 1.0, "Kc_end": 0.75},
            "fruiting": {"Kc_ini": 0.6, "Kc_mid": 1.0, "Kc_end": 0.75},
            "mixed": {"Kc_ini": 0.6, "Kc_mid": 1.0, "Kc_end": 0.75}
        }
        return kc_values.get(growth_stage)

    def format_for_prompt(
        self,
        results: List[RAGResult],
        max_tokens: Optional[int] = None
    ) -> str:
        """
        格式化检索结果用于 Prompt 注入

        Args:
            results: 检索结果
            max_tokens: 最大 token 数

        Returns:
            格式化的文本
        """
        if not results:
            return ""

        parts = ["<retrieved_knowledge>"]
        for i, result in enumerate(results, 1):
            source_tag = "[FAO56]" if result.metadata.get("is_fao56") else "[文献]"
            parts.append(f"{i}. {source_tag} {result.snippet}")
        parts.append("</retrieved_knowledge>")

        return "\n".join(parts)
