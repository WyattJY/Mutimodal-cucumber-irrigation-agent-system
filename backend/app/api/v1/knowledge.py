from __future__ import annotations
# Knowledge API Router
"""
知识库 API

功能:
1. GET /search - 搜索知识库
2. POST /feedback - 提交知识反馈
3. GET /stats/sources - 获取知识来源统计
4. POST /query - RAG 增强问答
5. GET /references - 获取知识引用历史
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

from app.models.schemas import KnowledgeQueryRequest, RAGAnswer, RAGReference

# 添加 src 路径以便导入 LocalRAGService
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入真正的 RAG 服务
try:
    from cucumber_irrigation.services.local_rag_service import LocalRAGService, LocalRAGConfig
    from cucumber_irrigation.rag.json_store import JsonKnowledgeStore

    # 初始化 RAG 服务 (全局单例)
    _rag_service = LocalRAGService(config=LocalRAGConfig(top_k=5))
    RAG_AVAILABLE = _rag_service.is_available
    print(f"[knowledge.py] LocalRAGService 初始化成功, 可用: {RAG_AVAILABLE}")
except Exception as e:
    print(f"[knowledge.py] LocalRAGService 初始化失败: {e}")
    _rag_service = None
    RAG_AVAILABLE = False


router = APIRouter()


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


class KnowledgeFeedback(BaseModel):
    chunk_id: str
    is_helpful: bool
    reason: Optional[str] = None
    context: Optional[str] = None


# 知识引用历史
KNOWLEDGE_REFERENCES_HISTORY: List[dict] = []

# 知识块缓存 (用于 /chunks/{chunk_id} 端点)
_chunks_cache: dict = {}


def _search_knowledge(query: str, top_k: int = 5) -> List[dict]:
    """
    使用 LocalRAGService 搜索知识库

    Returns:
        格式化后的结果列表
    """
    if not RAG_AVAILABLE or _rag_service is None:
        # 如果 RAG 不可用，返回空列表
        return []

    results = _rag_service.search(query, top_k=top_k)

    formatted = []
    for r in results:
        chunk_data = {
            "id": r.doc_id,
            "source": "FAO56" if r.is_fao56 else r.source,
            "source_file": r.source,
            "chapter": None,
            "page": r.page,
            "content": r.snippet,
            "relevance_score": r.relevance_score,
            "content_type": r.content_type,
            "created_at": datetime.now().isoformat(),
        }
        formatted.append(chunk_data)
        # 缓存以备后用
        _chunks_cache[r.doc_id] = chunk_data

    return formatted


@router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    source: Optional[str] = Query(None),
    mode: Optional[Literal["vector", "keyword", "hybrid"]] = Query("hybrid"),
):
    """搜索知识库"""
    start_time = datetime.now()

    # 使用真实 RAG 搜索
    results = _search_knowledge(q, top_k=top_k * 2)  # 多检索一些以便过滤

    # 按来源筛选
    if source and source != "all":
        results = [c for c in results if source.lower() in c.get("source", "").lower()]

    # 取 top_k
    results = results[:top_k]

    search_time = (datetime.now() - start_time).total_seconds() * 1000

    return create_response({
        "chunks": results,
        "total": len(results),
        "query": q,
        "search_time_ms": round(search_time, 2),
        "rag_available": RAG_AVAILABLE,
    })


@router.post("/feedback")
async def submit_feedback(feedback: KnowledgeFeedback):
    """提交知识反馈"""
    # 实际应保存到数据库
    print(f"Received feedback: {feedback}")
    return create_response({"message": "Feedback submitted successfully"})


@router.get("/stats/sources")
async def get_source_stats():
    """获取知识来源统计"""
    if RAG_AVAILABLE and _rag_service is not None:
        # 从真实知识库获取统计
        store = _rag_service.store
        stats = {
            "total_chunks": store.chunk_count,
            "FAO56": store.chunk_count,  # 目前主要是 FAO56
            "rag_available": True,
        }
    else:
        stats = {
            "total_chunks": 0,
            "rag_available": False,
        }
    return create_response(stats)


# ============================================================================
# 新增端点
# ============================================================================

@router.post("/query")
async def query_knowledge(request: KnowledgeQueryRequest):
    """
    RAG 增强问答

    接收问题，检索相关知识，生成增强回答

    Args:
        request: KnowledgeQueryRequest (question, context, top_k)

    Returns:
        RAGAnswer: 增强回答和引用来源
    """
    try:
        question = request.question
        top_k = request.top_k

        # 使用真实 RAG 检索
        relevant_chunks = _search_knowledge(question, top_k=top_k)

        # 构建引用
        references = [
            RAGReference(
                doc_id=chunk["id"],
                title=f"{chunk['source']} - Page {chunk.get('page', 'N/A')}",
                snippet=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                relevance=chunk["relevance_score"]
            )
            for chunk in relevant_chunks
        ]

        # 生成回答
        if relevant_chunks:
            context_text = "\n".join([c["content"] for c in relevant_chunks[:3]])
            answer = f"根据知识库检索结果，关于「{question}」的相关信息如下：\n\n"
            answer += context_text[:800]

            if len(context_text) > 800:
                answer += "\n\n...更多详情请参考上述引用来源。"
        else:
            answer = f"未找到与「{question}」直接相关的知识。建议咨询领域专家或查阅更多资料。"

        # 记录引用历史
        ref_record = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "references": [r.model_dump() for r in references]
        }
        KNOWLEDGE_REFERENCES_HISTORY.append(ref_record)

        return create_response(RAGAnswer(
            answer=answer,
            references=references,
            model="local-rag" if RAG_AVAILABLE else "fallback"
        ).model_dump())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识检索失败: {str(e)}")


@router.get("/references")
async def get_knowledge_references(
    limit: int = Query(20, ge=1, le=100),
    episode_date: Optional[str] = Query(None)
):
    """
    获取知识引用历史

    Args:
        limit: 返回数量限制
        episode_date: 按 Episode 日期过滤 (可选)

    Returns:
        引用历史列表
    """
    try:
        # 按时间倒序
        sorted_refs = sorted(
            KNOWLEDGE_REFERENCES_HISTORY,
            key=lambda x: x["timestamp"],
            reverse=True
        )

        # 过滤和限制
        if episode_date:
            sorted_refs = [r for r in sorted_refs if episode_date in r.get("question", "")]

        return create_response({
            "references": sorted_refs[:limit],
            "total": len(sorted_refs)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/{chunk_id}")
async def get_knowledge_chunk(chunk_id: str):
    """
    获取指定知识块详情

    Args:
        chunk_id: 知识块 ID

    Returns:
        知识块详情
    """
    # 先检查缓存
    if chunk_id in _chunks_cache:
        return create_response(_chunks_cache[chunk_id])

    # 如果不在缓存中，尝试搜索
    if RAG_AVAILABLE and _rag_service is not None:
        # 搜索并查找匹配的 chunk
        results = _rag_service.search(chunk_id[:10], top_k=20)  # 用 ID 前缀搜索
        for r in results:
            if r.doc_id == chunk_id:
                chunk_data = {
                    "id": r.doc_id,
                    "source": "FAO56" if r.is_fao56 else r.source,
                    "source_file": r.source,
                    "page": r.page,
                    "content": r.snippet,
                    "relevance_score": r.relevance_score,
                }
                _chunks_cache[chunk_id] = chunk_data
                return create_response(chunk_data)

    raise HTTPException(status_code=404, detail=f"知识块 {chunk_id} 未找到")


@router.get("/status")
async def get_rag_status():
    """获取 RAG 服务状态"""
    if RAG_AVAILABLE and _rag_service is not None:
        store = _rag_service.store
        return create_response({
            "available": True,
            "chunk_count": store.chunk_count,
            "service": "LocalRAGService",
        })
    else:
        return create_response({
            "available": False,
            "chunk_count": 0,
            "service": None,
        })
