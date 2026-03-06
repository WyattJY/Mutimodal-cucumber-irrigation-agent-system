"""本地 JSON 知识库

无需外部数据库服务，直接从 JSON 文件加载知识库
"""

import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class KnowledgeChunk:
    """知识块"""
    unique_id: str
    content: str
    page_num: int
    file_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unique_id": self.unique_id,
            "content": self.content,
            "page_num": self.page_num,
            "file_name": self.file_name,
            "metadata": self.metadata
        }


@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    content: str
    score: float
    source: str = "FAO56"
    metadata: Dict[str, Any] = field(default_factory=dict)


class JsonKnowledgeStore:
    """基于 JSON 文件的本地知识库

    不需要 Milvus 或 MongoDB，直接加载 JSON 文件
    使用简单的关键词匹配进行检索
    """

    def __init__(self, json_path: Optional[str] = None):
        """
        初始化知识库

        Args:
            json_path: JSON 文件路径，默认使用 data/knowledge_base/fao56_chunks.json
        """
        if json_path is None:
            # 默认路径
            base_dir = Path(__file__).parent.parent.parent.parent
            json_path = base_dir / "data" / "knowledge_base" / "fao56_chunks.json"

        self.json_path = Path(json_path)
        self._chunks: List[KnowledgeChunk] = []
        self._loaded = False

    def _ensure_loaded(self):
        """确保数据已加载"""
        if self._loaded:
            return

        if not self.json_path.exists():
            logger.warning(f"知识库文件不存在: {self.json_path}")
            self._loaded = True
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data:
                chunk = KnowledgeChunk(
                    unique_id=item.get("unique_id", ""),
                    content=item.get("page_content", ""),
                    page_num=item.get("page_num", 0),
                    file_name=item.get("file_name", ""),
                    metadata=item.get("metadata", {})
                )
                if chunk.content:  # 只添加有内容的块
                    self._chunks.append(chunk)

            logger.info(f"知识库加载完成: {len(self._chunks)} 个知识块")
            self._loaded = True

        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
            self._loaded = True

    @property
    def is_available(self) -> bool:
        """知识库是否可用"""
        self._ensure_loaded()
        return len(self._chunks) > 0

    @property
    def chunk_count(self) -> int:
        """知识块数量"""
        self._ensure_loaded()
        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        keywords: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        搜索知识库

        使用关键词匹配进行检索，支持中英文

        Args:
            query: 查询文本
            top_k: 返回结果数量
            keywords: 额外关键词列表

        Returns:
            搜索结果列表
        """
        self._ensure_loaded()

        if not self._chunks:
            return []

        # 构建搜索关键词
        query_lower = query.lower()
        search_terms = []

        # 1. 按空格分割 (英文)
        for term in query_lower.split():
            if len(term) >= 2:  # 至少2个字符
                search_terms.append(term)

        # 2. 提取中文关键词 (连续中文字符)
        import re
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        chinese_matches = chinese_pattern.findall(query)
        for match in chinese_matches:
            search_terms.append(match)
            # 如果中文词较长，也添加2-3字的子串
            if len(match) >= 3:
                for i in range(len(match) - 1):
                    search_terms.append(match[i:i+2])

        # 3. 添加额外关键词
        if keywords:
            search_terms.extend([k.lower() for k in keywords])

        # 4. 添加常见同义词/翻译
        synonym_map = {
            "kc": ["crop coefficient", "作物系数"],
            "开花": ["flowering", "flower", "bloom"],
            "黄瓜": ["cucumber", "黄瓜"],
            "灌溉": ["irrigation", "灌水", "浇水"],
            "需水量": ["water requirement", "ETc", "evapotranspiration"],
        }
        for term in list(search_terms):
            if term in synonym_map:
                search_terms.extend(synonym_map[term])

        # 去重
        search_terms = list(set(search_terms))

        # 计算每个块的匹配分数
        scored_chunks = []
        for chunk in self._chunks:
            content_lower = chunk.content.lower()
            score = 0.0

            for term in search_terms:
                if term in content_lower:
                    # 根据出现次数和术语长度计算分数
                    count = content_lower.count(term)
                    # 较长的匹配给更高分数
                    term_weight = len(term) * 0.5
                    score += count * term_weight * (100.0 / max(len(chunk.content), 1))

            if score > 0:
                scored_chunks.append((chunk, score))

        # 按分数排序
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # 返回 top_k 结果
        results = []
        for chunk, score in scored_chunks[:top_k]:
            results.append(SearchResult(
                doc_id=chunk.unique_id,
                content=chunk.content,
                score=score,
                source=chunk.file_name,
                metadata=chunk.metadata
            ))

        return results

    def search_for_growth_stage(
        self,
        growth_stage: str,
        top_k: int = 3
    ) -> List[SearchResult]:
        """
        根据生育期搜索相关知识

        Args:
            growth_stage: 生育期 (seedling/vegetative/flowering/fruiting)
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        # 生育期关键词映射
        stage_keywords = {
            "seedling": ["seedling", "germination", "young plant", "initial", "Kc ini"],
            "vegetative": ["vegetative", "growth", "leaf", "Kc mid", "development"],
            "flowering": ["flowering", "flower", "bloom", "pollination", "Kc"],
            "fruiting": ["fruit", "harvest", "yield", "Kc end", "maturity"]
        }

        keywords = stage_keywords.get(growth_stage, [growth_stage])
        query = f"{growth_stage} cucumber irrigation water requirement"

        return self.search(query, top_k, keywords)

    def search_for_anomaly(
        self,
        anomaly_type: str,
        growth_stage: Optional[str] = None
    ) -> List[SearchResult]:
        """
        根据异常类型搜索相关知识

        Args:
            anomaly_type: 异常类型
            growth_stage: 生育期 (可选)

        Returns:
            搜索结果列表
        """
        # 异常类型关键词映射
        anomaly_keywords = {
            "wilting": ["wilting", "water stress", "drought", "deficit"],
            "yellowing": ["yellowing", "chlorosis", "nitrogen", "nutrient"],
            "high_temperature": ["high temperature", "heat stress", "cooling"],
            "high_humidity": ["high humidity", "disease", "ventilation"],
            "low_light": ["low light", "cloudy", "shade", "PAR"]
        }

        keywords = anomaly_keywords.get(anomaly_type, [anomaly_type])
        if growth_stage:
            keywords.append(growth_stage)

        query = f"{anomaly_type} cucumber greenhouse"

        return self.search(query, top_k=3, keywords=keywords)

    def get_irrigation_guidelines(self, top_k: int = 5) -> List[SearchResult]:
        """获取灌溉指南相关知识"""
        return self.search(
            "irrigation scheduling water requirement ETc crop coefficient",
            top_k=top_k,
            keywords=["Kc", "ET0", "evapotranspiration", "irrigation"]
        )
