"""
RAG MCP Server — 将 FAO56 知识检索封装为标准 MCP 工具

启动方式:
  python mcp_servers/rag_server.py          # stdio 模式
  python mcp_servers/rag_server.py --http   # Streamable HTTP 模式
"""
from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

mcp = FastMCP("RAG Search Server")


@mcp.tool()
async def rag_search(
    query: str,
    top_k: int = 3,
    growth_stage: Optional[str] = None,
) -> dict:
    """
    检索 FAO56 灌溉知识库，返回相关文档和建议。

    Args:
        query: 查询文本（如"黄瓜开花期灌水量"）
        top_k: 返回文档数量（默认 3）
        growth_stage: 可选的生长阶段过滤（如"flowering"、"fruiting"）

    Returns:
        {
            "documents": [
                {"content": "...", "source": "FAO56 p.123", "relevance": 0.92},
                ...
            ],
            "advice": "根据检索结果生成的灌溉建议",
            "chunk_count": 10211
        }
    """
    from app.services.rag_service import rag_service, RetrievalResult

    try:
        # 如果指定了生长阶段，增强查询
        enhanced_query = query
        if growth_stage:
            enhanced_query = f"{growth_stage}期 {query}"

        # 调用已有的 RAG Service
        results: list[RetrievalResult] = rag_service.retrieve(
            enhanced_query, top_k=top_k
        )

        documents = []
        for r in results:
            documents.append({
                "doc_id": r.doc_id,
                "title": r.title,
                "content": r.snippet,
                "source": r.metadata.get("source", "unknown") if r.metadata else "unknown",
                "relevance": round(r.relevance, 3),
            })

        # 生成综合建议
        advice = _generate_advice(documents, query)

        return {
            "documents": documents,
            "advice": advice,
            "query_used": enhanced_query,
        }

    except Exception as e:
        return {"error": str(e), "documents": [], "advice": ""}


@mcp.tool()
async def rag_search_multi_query(
    query: str,
    num_variants: int = 3,
    top_k: int = 5,
) -> dict:
    """
    Multi-Query RAG 检索：自动生成多个语义变体查询，扩大召回覆盖。

    Args:
        query: 原始查询
        num_variants: 生成的变体查询数量（默认 3）
        top_k: 每个查询返回的文档数

    Returns:
        {
            "queries": ["原始查询", "变体1", "变体2", ...],
            "documents": [...],  # 去重合并后的文档
            "total_unique_docs": 8
        }
    """
    from app.services.rag_service import rag_service
    from app.services.llm_service import llm_service

    try:
        # Step 1: LLM 生成查询变体
        variant_prompt = f"""请为以下问题生成 {num_variants} 个不同角度的语义变体查询，用于扩大知识库检索覆盖面。
只返回 JSON 数组，不要其他内容。

原始问题: {query}

示例输出: ["变体查询1", "变体查询2", "变体查询3"]"""

        variant_response = await llm_service.call_llm(
            system="你是一个查询扩展助手。",
            user=variant_prompt,
            response_format={"type": "json_object"},
        )

        try:
            variants = json.loads(variant_response)
            if isinstance(variants, dict):
                variants = variants.get("queries", variants.get("variants", []))
        except json.JSONDecodeError:
            variants = []

        all_queries = [query] + variants[:num_variants]

        # Step 2: 每个查询独立检索
        seen_doc_ids = set()
        all_documents = []

        for q in all_queries:
            results = rag_service.retrieve(q, top_k=top_k)
            for r in results:
                if r.doc_id not in seen_doc_ids:
                    seen_doc_ids.add(r.doc_id)
                    all_documents.append({
                        "doc_id": r.doc_id,
                        "title": r.title,
                        "content": r.snippet,
                        "relevance": round(r.relevance, 3),
                        "matched_query": q,
                    })

        # Step 3: 按 relevance 排序
        all_documents.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "queries": all_queries,
            "documents": all_documents[:top_k],
            "total_unique_docs": len(all_documents),
        }

    except Exception as e:
        return {"error": str(e), "queries": [query], "documents": []}


def _generate_advice(documents: list, query: str) -> str:
    """根据检索结果生成简要建议"""
    if not documents:
        return "未检索到相关知识库内容，建议参考 FAO56 标准公式。"

    top_doc = documents[0]
    return f"根据 FAO56 知识库（相关度 {top_doc['relevance']:.0%}）：{top_doc['content'][:200]}..."


@mcp.tool()
async def rag_health_check() -> dict:
    """检查 RAG 服务和知识库状态。"""
    from app.services.rag_service import rag_service

    return {
        "available": hasattr(rag_service, "retrieve"),
        "index_loaded": rag_service._index is not None if hasattr(rag_service, "_index") else False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="使用 Streamable HTTP 模式")
    parser.add_argument("--port", type=int, default=8011, help="HTTP 端口")
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport="stdio")
