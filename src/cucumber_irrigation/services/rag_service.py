"""RAG 检索服务

封装 Milvus 知识检索，FAO56 优先
参考: task1.md P4-03, requirements1.md 4.6节
"""

from typing import Optional, List

from ..memory.knowledge_retriever import KnowledgeRetriever, RetrievalConfig
from ..models.anomaly import RAGResult


class RAGService:
    """RAG 检索服务

    封装知识检索功能:
    - Milvus 混合检索 (稀疏+稠密向量)
    - FAO56 优先返回
    - 异常类型专用查询
    - 生育期知识检索
    """

    def __init__(
        self,
        milvus_uri: Optional[str] = None,
        mongo_client=None,
        config: Optional[RetrievalConfig] = None,
        embedding_model_path: Optional[str] = None
    ):
        """
        初始化服务

        Args:
            milvus_uri: Milvus 连接 URI
            mongo_client: MongoDB 客户端
            config: 检索配置
            embedding_model_path: BGE-M3 模型路径
        """
        self.retriever = KnowledgeRetriever(
            milvus_uri=milvus_uri,
            mongo_client=mongo_client,
            config=config,
            embedding_model_path=embedding_model_path
        )
        self.config = config or RetrievalConfig()

    def search(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RAGResult]:
        """
        执行知识检索

        Args:
            query: 检索查询
            top_k: 返回数量

        Returns:
            RAGResult 列表
        """
        return self.retriever.search(query, top_k=top_k)

    def search_for_anomaly(
        self,
        anomaly_type: str,
        growth_stage: Optional[str] = None,
        abnormality: Optional[str] = None
    ) -> List[RAGResult]:
        """
        为异常检索知识

        Args:
            anomaly_type: 异常类型
            growth_stage: 生育期
            abnormality: 异常详情

        Returns:
            RAGResult 列表
        """
        return self.retriever.search_by_anomaly(
            anomaly_type=anomaly_type,
            growth_stage=growth_stage,
            abnormality=abnormality
        )

    def search_for_growth_stage(
        self,
        growth_stage: str,
        top_k: Optional[int] = None
    ) -> List[RAGResult]:
        """
        为生育期检索知识

        Args:
            growth_stage: 生育期
            top_k: 返回数量

        Returns:
            RAGResult 列表
        """
        return self.retriever.search_by_growth_stage(growth_stage, top_k=top_k)

    def get_fao56_kc(self, growth_stage: str) -> Optional[dict]:
        """
        获取 FAO56 作物系数

        Args:
            growth_stage: 生育期

        Returns:
            Kc 系数信息
        """
        return self.retriever.get_fao56_kc(growth_stage)

    def format_for_prompt(
        self,
        results: List[RAGResult],
        max_tokens: Optional[int] = None
    ) -> str:
        """
        格式化检索结果用于 Prompt

        Args:
            results: 检索结果
            max_tokens: 最大 token 数

        Returns:
            格式化文本
        """
        return self.retriever.format_for_prompt(results, max_tokens)

    def build_rag_advice(
        self,
        anomaly_type: str,
        growth_stage: Optional[str] = None,
        abnormality: Optional[str] = None
    ) -> str:
        """
        构建 RAG 建议文本 (用于 SanityCheck)

        Args:
            anomaly_type: 异常类型
            growth_stage: 生育期
            abnormality: 异常详情

        Returns:
            RAG 建议文本
        """
        results = self.search_for_anomaly(
            anomaly_type=anomaly_type,
            growth_stage=growth_stage,
            abnormality=abnormality
        )

        if not results:
            return ""

        # 构建建议
        parts = ["根据知识库检索:"]
        for i, result in enumerate(results[:3], 1):
            source_tag = "[FAO56]" if result.metadata.get("is_fao56") else "[文献]"
            parts.append(f"{i}. {source_tag} {result.snippet[:200]}...")

        return "\n".join(parts)
