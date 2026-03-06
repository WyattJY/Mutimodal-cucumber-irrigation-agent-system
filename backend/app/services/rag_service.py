from __future__ import annotations
# T2.1 RAGService - 知识检索服务
"""
RAG (Retrieval-Augmented Generation) 知识检索服务
封装向量检索和知识增强功能
"""
import os
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    doc_id: str
    title: Optional[str]
    snippet: str
    relevance: float
    metadata: Optional[Dict[str, Any]] = None


class RAGService:
    """RAG 知识检索服务"""

    def __init__(
        self,
        index_path: Optional[str] = None,
        knowledge_base_path: Optional[str] = None
    ):
        """
        初始化 RAG 服务

        Args:
            index_path: 向量索引路径
            knowledge_base_path: 知识库文件路径
        """
        self.index_path = index_path or os.getenv(
            "RAG_INDEX_PATH",
            "data/rag_index"
        )
        self.knowledge_base_path = knowledge_base_path or os.getenv(
            "KNOWLEDGE_BASE_PATH",
            "data/knowledge"
        )
        self._index = None
        self._documents: List[Dict] = []
        self._initialized = False

        # 尝试加载知识库
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """加载知识库"""
        try:
            kb_path = Path(self.knowledge_base_path)
            if kb_path.exists():
                # 加载所有 JSON 文件
                for json_file in kb_path.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self._documents.extend(data)
                            else:
                                self._documents.append(data)
                    except Exception as e:
                        logger.warning(f"Failed to load {json_file}: {e}")

                # 加载所有 Markdown 文件
                for md_file in kb_path.glob("*.md"):
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self._documents.append({
                                "doc_id": md_file.stem,
                                "title": md_file.stem,
                                "content": content,
                                "type": "markdown"
                            })
                    except Exception as e:
                        logger.warning(f"Failed to load {md_file}: {e}")

                self._initialized = len(self._documents) > 0
                logger.info(f"Loaded {len(self._documents)} documents from knowledge base")
            else:
                logger.warning(f"Knowledge base path not found: {kb_path}")
                self._initialized = False

        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            self._initialized = False

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        通用文本检索

        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            检索结果列表
        """
        if not self._initialized:
            logger.warning("RAG service not initialized, returning mock results")
            return self._mock_search(query, top_k)

        # 简单关键词匹配（实际应使用向量检索）
        results = []
        query_lower = query.lower()
        keywords = query_lower.split()

        for doc in self._documents:
            content = doc.get("content", "")
            title = doc.get("title", "")
            doc_text = f"{title} {content}".lower()

            # 计算简单相关度
            score = 0.0
            for kw in keywords:
                if kw in doc_text:
                    score += 1.0 / len(keywords)

            if score > 0:
                # 应用过滤器
                if filters:
                    if not self._matches_filters(doc, filters):
                        continue

                # 提取片段
                snippet = self._extract_snippet(content, keywords)

                results.append(RetrievalResult(
                    doc_id=doc.get("doc_id", str(id(doc))),
                    title=doc.get("title"),
                    snippet=snippet,
                    relevance=min(score, 1.0),
                    metadata=doc.get("metadata")
                ))

        # 按相关度排序
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:top_k]

    async def search_by_growth_stage(
        self,
        growth_stage: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        按生育期检索相关知识

        Args:
            growth_stage: 生育期 (vegetative/flowering/fruiting/mixed)
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        stage_keywords = {
            "vegetative": ["苗期", "营养生长", "叶片发育", "vegetative", "seedling"],
            "flowering": ["开花期", "花芽分化", "授粉", "flowering", "bloom"],
            "fruiting": ["结果期", "果实发育", "采收", "fruiting", "harvest"],
            "mixed": ["混合期", "过渡期", "mixed"]
        }

        keywords = stage_keywords.get(growth_stage, [growth_stage])
        query = " ".join(keywords)

        return await self.search(
            query=query,
            top_k=top_k,
            filters={"growth_stage": growth_stage}
        )

    async def search_by_anomaly(
        self,
        anomaly_type: str,
        severity: str = "mild"
    ) -> List[RetrievalResult]:
        """
        按异常类型检索相关知识

        Args:
            anomaly_type: 异常类型 (wilting/yellowing/pests/disease)
            severity: 严重程度 (mild/severe)

        Returns:
            检索结果列表
        """
        anomaly_keywords = {
            "wilting": ["萎蔫", "缺水", "wilting", "water stress"],
            "yellowing": ["黄化", "缺素", "yellowing", "chlorosis"],
            "pests": ["虫害", "害虫", "pests", "insects"],
            "disease": ["病害", "真菌", "disease", "fungal"]
        }

        keywords = anomaly_keywords.get(anomaly_type, [anomaly_type])
        if severity == "severe":
            keywords.extend(["严重", "紧急", "severe"])

        query = " ".join(keywords)
        return await self.search(query=query, top_k=5)

    async def build_augmented_answer(
        self,
        question: str,
        context: Optional[str] = None,
        llm_service=None
    ) -> Dict[str, Any]:
        """
        构建 RAG 增强回答

        Args:
            question: 用户问题
            context: 额外上下文
            llm_service: LLM 服务实例

        Returns:
            包含答案和引用的字典
        """
        # 检索相关文档
        results = await self.search(question, top_k=5)

        # 构建增强 prompt
        rag_context = self._build_rag_prompt(question, results)

        # 如果提供了 LLM 服务，生成回答
        if llm_service and hasattr(llm_service, 'generate_text'):
            try:
                answer = await llm_service.generate_text(
                    system_prompt="你是黄瓜灌溉专家。根据提供的知识库内容回答问题。",
                    user_prompt=rag_context
                )
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                answer = self._generate_simple_answer(question, results)
        else:
            answer = self._generate_simple_answer(question, results)

        return {
            "answer": answer,
            "references": self._format_references(results),
            "model": "rag-enhanced"
        }

    def _build_rag_prompt(
        self,
        question: str,
        retrieved_docs: List[RetrievalResult]
    ) -> str:
        """构建 RAG prompt"""
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[{i}] {doc.title or doc.doc_id}:\n{doc.snippet}")

        context = "\n\n".join(context_parts)

        return f"""基于以下知识库内容回答问题：

{context}

用户问题：{question}

请根据以上内容提供准确的回答。如果知识库内容不足以回答问题，请说明。"""

    def _format_references(
        self,
        docs: List[RetrievalResult]
    ) -> List[Dict[str, Any]]:
        """格式化引用列表"""
        return [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "snippet": doc.snippet,
                "relevance": doc.relevance
            }
            for doc in docs
        ]

    def _matches_filters(
        self,
        doc: Dict,
        filters: Dict[str, Any]
    ) -> bool:
        """检查文档是否匹配过滤条件"""
        metadata = doc.get("metadata", {})
        for key, value in filters.items():
            doc_value = doc.get(key) or metadata.get(key)
            if doc_value and doc_value != value:
                return False
        return True

    def _extract_snippet(
        self,
        content: str,
        keywords: List[str],
        max_length: int = 200
    ) -> str:
        """从内容中提取相关片段"""
        content_lower = content.lower()

        # 找到第一个关键词位置
        best_pos = len(content)
        for kw in keywords:
            pos = content_lower.find(kw)
            if pos != -1 and pos < best_pos:
                best_pos = pos

        # 提取片段
        start = max(0, best_pos - 50)
        end = min(len(content), best_pos + max_length)

        snippet = content[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _mock_search(
        self,
        query: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """返回模拟检索结果"""
        mock_data = [
            {
                "doc_id": "cucumber_irrigation_guide",
                "title": "黄瓜灌溉指南",
                "snippet": "黄瓜在不同生育期需水量不同。苗期日灌水量约2-3升/平方米，开花期3-5升，结果期5-7升。",
                "relevance": 0.85
            },
            {
                "doc_id": "growth_stage_management",
                "title": "生育期管理",
                "snippet": "开花期是黄瓜生长的关键时期，需要保持充足水分但避免积水。建议采用少量多次灌溉方式。",
                "relevance": 0.78
            },
            {
                "doc_id": "disease_prevention",
                "title": "病害预防",
                "snippet": "高湿环境容易引发霜霉病和灰霉病。应控制灌水量，保持通风，必要时进行药剂防治。",
                "relevance": 0.65
            }
        ]

        return [
            RetrievalResult(
                doc_id=d["doc_id"],
                title=d["title"],
                snippet=d["snippet"],
                relevance=d["relevance"]
            )
            for d in mock_data[:top_k]
        ]

    def _generate_simple_answer(
        self,
        question: str,
        results: List[RetrievalResult]
    ) -> str:
        """生成简单回答（无 LLM 时使用）"""
        if not results:
            return "抱歉，未找到相关知识。请尝试换一种方式提问。"

        # 拼接相关内容作为回答
        answer_parts = []
        for result in results[:3]:
            if result.title:
                answer_parts.append(f"**{result.title}**")
            answer_parts.append(result.snippet)

        return "\n\n".join(answer_parts)


# 创建单例
rag_service = RAGService()
