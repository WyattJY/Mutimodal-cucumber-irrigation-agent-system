"""本地 RAG 服务

使用 JsonKnowledgeStore 提供 RAG 功能
无需 Milvus/MongoDB 外部服务
"""

from typing import Optional, List
from dataclasses import dataclass

from loguru import logger

from ..rag.json_store import JsonKnowledgeStore, SearchResult
from ..models.anomaly import RAGResult


@dataclass
class LocalRAGConfig:
    """本地 RAG 配置"""
    top_k: int = 3
    fao56_weight: float = 1.5
    max_tokens_per_snippet: int = 200


class LocalRAGService:
    """本地 RAG 服务

    使用 JsonKnowledgeStore 进行知识检索
    无需外部数据库服务
    """

    def __init__(
        self,
        knowledge_store: Optional[JsonKnowledgeStore] = None,
        config: Optional[LocalRAGConfig] = None
    ):
        """
        初始化服务

        Args:
            knowledge_store: JSON 知识库
            config: 配置
        """
        self.store = knowledge_store or JsonKnowledgeStore()
        self.config = config or LocalRAGConfig()
        logger.info(f"LocalRAGService 初始化完成, 知识库可用: {self.store.is_available}")

    @property
    def is_available(self) -> bool:
        """RAG 服务是否可用"""
        return self.store.is_available

    def _convert_to_rag_result(self, result: SearchResult) -> RAGResult:
        """转换搜索结果为 RAGResult"""
        is_fao56 = "fao56" in result.source.lower() or "Fao56" in result.source

        return RAGResult(
            doc_id=result.doc_id,
            snippet=result.content[:self.config.max_tokens_per_snippet * 4],  # 大约估算
            relevance_score=result.score * (self.config.fao56_weight if is_fao56 else 1.0),
            source=result.source,
            is_fao56=is_fao56,
            source_type="system",
            page=result.metadata.get("page"),
            content_type=result.metadata.get("content_type")
        )

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
        top_k = top_k or self.config.top_k
        results = self.store.search(query, top_k=top_k)
        return [self._convert_to_rag_result(r) for r in results]

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
        results = self.store.search_for_anomaly(anomaly_type, growth_stage)
        return [self._convert_to_rag_result(r) for r in results]

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
        top_k = top_k or self.config.top_k
        results = self.store.search_for_growth_stage(growth_stage, top_k=top_k)
        return [self._convert_to_rag_result(r) for r in results]

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
            "seedling": {"Kc_ini": 0.6, "Kc_mid": 0.7, "Kc_end": 0.7},
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
        格式化检索结果用于 Prompt

        Args:
            results: 检索结果
            max_tokens: 最大 token 数

        Returns:
            格式化文本
        """
        if not results:
            return ""

        parts = ["<retrieved_knowledge>"]
        for i, result in enumerate(results, 1):
            source_tag = "[FAO56]" if result.is_fao56 else "[文献]"
            snippet = result.snippet
            if max_tokens:
                # 粗略截断
                snippet = snippet[:max_tokens * 4]
            parts.append(f"{i}. {source_tag} {snippet}")
        parts.append("</retrieved_knowledge>")

        return "\n".join(parts)

    def build_rag_advice(
        self,
        anomaly_type: str,
        growth_stage: Optional[str] = None,
        abnormality: Optional[str] = None
    ) -> str:
        """
        构建 RAG 建议文本

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

        parts = ["根据知识库检索:"]
        for i, result in enumerate(results[:3], 1):
            source_tag = "[FAO56]" if result.is_fao56 else "[文献]"
            parts.append(f"{i}. {source_tag} {result.snippet[:200]}...")

        return "\n".join(parts)
