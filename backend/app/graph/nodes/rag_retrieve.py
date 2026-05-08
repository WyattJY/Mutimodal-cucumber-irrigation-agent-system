"""
RAG knowledge retrieval node.

Wraps: LocalRAGService from the core library.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger

from app.observability.decorators import traced_node

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from cucumber_irrigation.services.local_rag_service import LocalRAGService, LocalRAGConfig
    _rag_service = LocalRAGService(config=LocalRAGConfig(top_k=3))
    RAG_AVAILABLE = _rag_service.is_available
except Exception:
    _rag_service = None
    RAG_AVAILABLE = False


def _search_rag(growth_stage: Optional[str], env_data: dict) -> Tuple[list, Optional[str]]:
    """Execute RAG search, return (results, formatted_advice)."""
    if not RAG_AVAILABLE or _rag_service is None:
        return [], None

    try:
        if growth_stage:
            results = _rag_service.search_for_growth_stage(growth_stage=growth_stage, top_k=3)
        else:
            results = _rag_service.search("cucumber irrigation water requirement greenhouse", top_k=3)

        if not results:
            return [], None

        advice_parts = ["## 知识库参考"]
        for i, r in enumerate(results, 1):
            source_tag = "[FAO56]" if r.is_fao56 else "[文献]"
            advice_parts.append(f"{i}. {source_tag} {r.snippet[:200]}...")

        return results, "\n".join(advice_parts)

    except Exception as e:
        logger.warning(f"[rag_retrieve] 检索失败: {e}")
        return [], None


@traced_node("rag_retrieve")
def run(state: dict) -> dict:
    """Retrieve relevant knowledge from the RAG knowledge base."""
    use_rag = state.get("options", {}).get("use_rag", True)

    if not use_rag or not RAG_AVAILABLE:
        return {
            "rag_results": [],
            "rag_advice": None,
            "rag_references": [],
            "node_trace": [{"node": "rag_retrieve", "status": "skipped"}],
        }

    growth_stage = None
    pr = state.get("plant_response")
    if pr and isinstance(pr, dict):
        growth_stage = pr.get("growth_stage")

    env_data = state.get("env_data", {})
    results, advice = _search_rag(growth_stage, env_data)

    refs = []
    for r in results:
        refs.append({
            "doc_id": r.doc_id,
            "title": f"FAO56 - Page {r.page}" if r.is_fao56 else r.source,
            "snippet": r.snippet[:200] + "..." if len(r.snippet) > 200 else r.snippet,
            "relevance": r.relevance_score,
        })

    logger.info(f"[rag_retrieve] 检索到 {len(results)} 条知识")
    return {
        "rag_results": results,
        "rag_advice": advice,
        "rag_references": refs,
        "node_trace": [{"node": "rag_retrieve", "status": "ok", "count": len(results)}],
    }
