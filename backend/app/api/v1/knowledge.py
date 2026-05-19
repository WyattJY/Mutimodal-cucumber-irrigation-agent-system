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

import json
import re
import sys
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

from app.models.schemas import KnowledgeQueryRequest, RAGAnswer, RAGReference
from app.observability.metrics import (
    KNOWLEDGE_ASSETS_INDEXED,
    KNOWLEDGE_CHUNKS_INDEXED,
    KNOWLEDGE_INDEX_DURATION,
    KNOWLEDGE_UPLOADS,
    RAG_LATENCY,
    RAG_QUERIES,
    RAG_RESULTS_COUNT,
)
from app.services.knowledge_index_service import knowledge_indexer
from app.services.pdf_enhanced_parser import enhanced_pdf_parser

# 添加 src 路径以便导入 LocalRAGService
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from cucumber_irrigation.rag.json_store import JsonKnowledgeStore

    _json_store = JsonKnowledgeStore()
except Exception as e:
    print(f"[knowledge.py] JsonKnowledgeStore 初始化失败: {e}")
    JsonKnowledgeStore = None
    _json_store = None

# 导入真正的 RAG 服务
try:
    from cucumber_irrigation.services.local_rag_service import LocalRAGService, LocalRAGConfig

    # 初始化 RAG 服务 (全局单例)
    _rag_service = LocalRAGService(config=LocalRAGConfig(top_k=5))
    RAG_AVAILABLE = _rag_service.is_available
    print(f"[knowledge.py] LocalRAGService 初始化成功, 可用: {RAG_AVAILABLE}")
except Exception as e:
    print(f"[knowledge.py] LocalRAGService 初始化失败: {e}")
    _rag_service = None
    RAG_AVAILABLE = False


router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
USER_LITERATURE_DIR = PROJECT_ROOT / "data" / "user_literature"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".txt", ".md"}


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


def _safe_filename(name: str) -> str:
    suffix = Path(name).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._") or "document"
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{stem}{suffix}"


def _sanitize_upload_text(text: str) -> str:
    """Remove invalid Unicode produced by some PDF extractors before JSON persistence."""
    if not text:
        return ""
    text = text.encode("utf-8", errors="ignore").decode("utf-8")
    return text.replace("\x00", "")


def _write_json_atomic(path: Path, data) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp")
    try:
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _iter_metadata_files() -> list[Path]:
    USER_LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    return [
        path
        for path in sorted(USER_LITERATURE_DIR.glob("*.metadata.json"), reverse=True)
        if not path.name.startswith("._")
    ]


def _chunk_text(
    text: str,
    doc_id: str,
    original_filename: str,
    title: str,
    category: str,
    page_num: int = 0,
    start_index: int = 0,
) -> list[dict]:
    text = _sanitize_upload_text(text)
    text = re.sub(r"\s+\n", "\n", text).strip()
    if not text:
        return []

    chunks: list[dict] = []
    max_chars = 1200
    overlap = 160
    start = 0
    index = start_index
    while start < len(text):
        end = min(len(text), start + max_chars)
        content = text[start:end].strip()
        if content:
            chunks.append({
                "unique_id": f"{doc_id}_chunk_{index:04d}",
                "page_content": content,
                "page_num": page_num,
                "file_name": original_filename,
                "metadata": {
                    "doc_id": doc_id,
                    "title": title,
                    "source": original_filename,
                    "source_type": "user",
                    "category": category,
                    "chunk_index": index,
                    "content_type": "user_literature",
                },
            })
            index += 1
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def _extract_upload_pages(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return [{"page_num": 1, "text": path.read_text(encoding="utf-8", errors="ignore")}]
    if suffix == ".pdf":
        try:
            import fitz  # type: ignore

            pages = []
            with fitz.open(str(path)) as pdf:
                for index, page in enumerate(pdf, start=1):
                    pages.append({"page_num": index, "text": page.get_text("text") or ""})
            return pages
        except Exception:
            try:
                from PyPDF2 import PdfReader

                reader = PdfReader(str(path))
                return [
                    {"page_num": index, "text": page.extract_text() or ""}
                    for index, page in enumerate(reader.pages, start=1)
                ]
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"PDF text extraction failed: {exc}") from exc
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")


def _extract_upload_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            try:
                from PyPDF2 import PdfReader

                reader = PdfReader(str(path))
                return "\n\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"PDF text extraction failed: {exc}") from exc
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")


def _chunk_pages(pages: list[dict], doc_id: str, original_filename: str, title: str, category: str) -> list[dict]:
    chunks: list[dict] = []
    next_index = 0
    for page in pages:
        page_chunks = _chunk_text(
            page.get("text", ""),
            doc_id,
            original_filename,
            title,
            category,
            page_num=int(page.get("page_num") or 0),
            start_index=next_index,
        )
        chunks.extend(page_chunks)
        next_index += len(page_chunks)
    return chunks


def _asset_public_url(asset_path: Path) -> str:
    try:
        rel = asset_path.relative_to(USER_LITERATURE_DIR).as_posix()
    except ValueError:
        rel = asset_path.name
    return f"/static/user_literature/{rel}"


def _extract_pdf_images(path: Path, doc_id: str, assets_root: Path) -> list[dict]:
    if path.suffix.lower() != ".pdf":
        return []

    try:
        import fitz  # type: ignore
    except Exception as exc:
        print(f"[knowledge.py] PyMuPDF unavailable, skipping PDF image extraction: {exc}")
        return []

    assets: list[dict] = []
    doc_assets_dir = assets_root / doc_id
    doc_assets_dir.mkdir(parents=True, exist_ok=True)

    try:
        with fitz.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                for image_index, image in enumerate(page.get_images(full=True), start=1):
                    xref = image[0]
                    try:
                        extracted = pdf.extract_image(xref)
                    except Exception as exc:
                        print(f"[knowledge.py] failed to extract image xref={xref}: {exc}")
                        continue

                    image_bytes = extracted.get("image")
                    if not image_bytes:
                        continue
                    ext = (extracted.get("ext") or "png").lower()
                    if ext == "jpeg":
                        ext = "jpg"
                    asset_id = f"{doc_id}_page_{page_index:03d}_img_{image_index:03d}"
                    asset_path = doc_assets_dir / f"page_{page_index:03d}_img_{image_index:03d}.{ext}"
                    asset_path.write_bytes(image_bytes)
                    assets.append({
                        "asset_id": asset_id,
                        "doc_id": doc_id,
                        "page_num": page_index,
                        "asset_type": "image",
                        "file_path": str(asset_path),
                        "public_url": _asset_public_url(asset_path),
                        "width": extracted.get("width"),
                        "height": extracted.get("height"),
                        "metadata": {
                            "xref": xref,
                            "ext": ext,
                            "colorspace": extracted.get("colorspace"),
                            "source_file": path.name,
                        },
                    })
    except Exception as exc:
        print(f"[knowledge.py] PDF image extraction failed: {exc}")
    return assets


def _refresh_local_rag() -> None:
    global _json_store, _rag_service, RAG_AVAILABLE

    if JsonKnowledgeStore is not None:
        try:
            _json_store = JsonKnowledgeStore()
        except Exception as exc:
            print(f"[knowledge.py] JsonKnowledgeStore refresh failed: {exc}")

    try:
        from app.services.rag_service import rag_service

        rag_service.reload()
    except Exception as exc:
        print(f"[knowledge.py] app RAG reload skipped: {exc}")

    if _rag_service is not None:
        try:
            _rag_service = LocalRAGService(config=LocalRAGConfig(top_k=5))
            RAG_AVAILABLE = _rag_service.is_available
        except Exception:
            RAG_AVAILABLE = False


def _search_knowledge(query: str, top_k: int = 5) -> List[dict]:
    """
    使用 LocalRAGService 搜索知识库

    Returns:
        格式化后的结果列表
    """
    started = time.perf_counter()
    if not RAG_AVAILABLE or _rag_service is None:
        if _json_store is None:
            return []
        results = _json_store.search(query, top_k=top_k)
        formatted = []
        for r in results:
            chunk_data = {
                "id": r.doc_id,
                "source": "FAO56" if "fao56" in r.source.lower() else r.source,
                "source_file": r.source,
                "chapter": None,
                "page": r.metadata.get("page") or r.metadata.get("page_num"),
                "content": r.content,
                "relevance_score": r.score,
                "content_type": r.metadata.get("content_type"),
                "created_at": datetime.now().isoformat(),
            }
            formatted.append(chunk_data)
            _chunks_cache[r.doc_id] = chunk_data
        RAG_QUERIES.labels(stage="keyword").inc()
        RAG_RESULTS_COUNT.observe(len(formatted))
        RAG_LATENCY.labels(stage="keyword").observe(time.perf_counter() - started)
        return formatted

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

    RAG_QUERIES.labels(stage="local_rag").inc()
    RAG_RESULTS_COUNT.observe(len(formatted))
    RAG_LATENCY.labels(stage="local_rag").observe(time.perf_counter() - started)
    return formatted


@router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("user_literature"),
):
    """Upload PDF/TXT/MD user literature and make it available to local RAG."""
    started = time.perf_counter()
    original_filename = file.filename or "document"
    suffix = Path(original_filename).suffix.lower()
    file_type = suffix.lstrip(".") or "unknown"
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        KNOWLEDGE_UPLOADS.labels(file_type=file_type, status="rejected").inc()
        KNOWLEDGE_INDEX_DURATION.labels(status="rejected").observe(time.perf_counter() - started)
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        KNOWLEDGE_UPLOADS.labels(file_type=file_type, status="rejected").inc()
        KNOWLEDGE_INDEX_DURATION.labels(status="rejected").observe(time.perf_counter() - started)
        raise HTTPException(status_code=413, detail="File exceeds 50MB upload limit")

    USER_LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    stored_filename = _safe_filename(original_filename)
    stored_path = USER_LITERATURE_DIR / stored_filename
    stored_path.write_bytes(content)

    doc_id = stored_path.stem
    document_title = title or Path(original_filename).stem
    pages = _extract_upload_pages(stored_path)
    chunks = _chunk_pages(pages, doc_id, original_filename, document_title, category)
    if not chunks:
        KNOWLEDGE_UPLOADS.labels(file_type=file_type, status="empty").inc()
        KNOWLEDGE_INDEX_DURATION.labels(status="empty").observe(time.perf_counter() - started)
        raise HTTPException(status_code=400, detail="No extractable text found in uploaded document")

    chunks_path = USER_LITERATURE_DIR / f"{doc_id}_chunks.json"
    metadata_path = USER_LITERATURE_DIR / f"{doc_id}.metadata.json"
    assets_root = USER_LITERATURE_DIR / "assets"
    assets = _extract_pdf_images(stored_path, doc_id, assets_root)
    enhanced_pdf = {
        "chunks": [],
        "assets": [],
        "layout_blocks": [],
        "parser_status": {"status": "not_pdf" if suffix != ".pdf" else "not_run"},
        "table_count": 0,
    }
    if suffix == ".pdf":
        try:
            enhanced_pdf = enhanced_pdf_parser.parse(
                path=stored_path,
                doc_id=doc_id,
                assets_root=assets_root,
                original_filename=original_filename,
                title=document_title,
                category=category,
            )
            chunks.extend(enhanced_pdf.get("chunks") or [])
            assets.extend(enhanced_pdf.get("assets") or [])
        except Exception as exc:
            print(f"[knowledge.py] enhanced PDF parsing skipped: {exc}")
            enhanced_pdf = {
                "chunks": [],
                "assets": [],
                "layout_blocks": [],
                "parser_status": {"status": f"failed:{exc}"},
                "table_count": 0,
            }

    image_count = sum(1 for asset in assets if (asset.get("asset_type") or "image") == "image")
    metadata = {
        "doc_id": doc_id,
        "title": document_title,
        "category": category,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "stored_path": str(stored_path),
        "chunks_path": str(chunks_path),
        "chunk_count": len(chunks),
        "image_count": image_count,
        "asset_count": len(assets),
        "table_count": int(enhanced_pdf.get("table_count") or 0),
        "layout_block_count": len(enhanced_pdf.get("layout_blocks") or []),
        "layout_blocks": enhanced_pdf.get("layout_blocks") or [],
        "parser_status": enhanced_pdf.get("parser_status") or {},
        "assets": assets,
        "assets_dir": str(assets_root / doc_id),
        "index_status": "pending",
        "uploaded_at": datetime.now().isoformat(),
    }
    _write_json_atomic(chunks_path, chunks)
    metadata["index_backends"] = await knowledge_indexer.index_document(metadata, chunks, assets)
    metadata["index_status"] = (
        "indexed"
        if metadata["index_backends"].get("postgres", {}).get("indexed")
        or metadata["index_backends"].get("chroma", {}).get("indexed")
        else "fallback_indexed"
    )
    _write_json_atomic(metadata_path, metadata)
    _refresh_local_rag()
    KNOWLEDGE_UPLOADS.labels(file_type=file_type, status=metadata["index_status"]).inc()
    KNOWLEDGE_INDEX_DURATION.labels(status=metadata["index_status"]).observe(time.perf_counter() - started)
    for backend, result in (metadata.get("index_backends") or {}).items():
        if result.get("indexed") or result.get("indexed_count"):
            KNOWLEDGE_CHUNKS_INDEXED.labels(backend=backend).inc(len(chunks))
            if assets:
                KNOWLEDGE_ASSETS_INDEXED.labels(backend=backend).inc(len(assets))

    return create_response(metadata)


@router.get("/uploads")
async def list_knowledge_uploads():
    """List uploaded user literature documents."""
    items = []
    for metadata_file in _iter_metadata_files():
        try:
            items.append(json.loads(metadata_file.read_text(encoding="utf-8")))
        except Exception:
            continue
    return create_response({"items": items, "total": len(items)})


def _load_upload_metadata_by_doc_id(doc_id: str) -> dict:
    USER_LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = USER_LITERATURE_DIR / f"{doc_id}.metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail=f"Uploaded document {doc_id} not found")
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read document metadata: {exc}") from exc


@router.get("/uploads/{doc_id}/pdf")
async def open_uploaded_pdf(doc_id: str):
    """Open an uploaded PDF inline so browser PDF viewer can jump to #page=N."""
    metadata = _load_upload_metadata_by_doc_id(doc_id)
    path = Path(metadata.get("stored_path") or "")
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Uploaded PDF file not found")
    filename = metadata.get("original_filename") or path.name
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{path.name}"'},
    )


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
    elif _json_store is not None:
        stats = {
            "total_chunks": _json_store.chunk_count,
            "FAO56": _json_store.chunk_count,
            "user_uploads": len(_iter_metadata_files()) if USER_LITERATURE_DIR.exists() else 0,
            "rag_available": _json_store.is_available,
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
    # 用户上传文献 chunk 优先从本地 chunks.json 精确读取。
    if USER_LITERATURE_DIR.exists():
        for metadata_file in _iter_metadata_files():
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                chunks_path = Path(metadata.get("chunks_path") or "")
                if not chunks_path.exists():
                    chunks_path = USER_LITERATURE_DIR / f"{metadata.get('doc_id', metadata_file.stem)}_chunks.json"
                chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for chunk in chunks if isinstance(chunks, list) else []:
                current_id = chunk.get("unique_id") or chunk.get("id") or chunk.get("doc_id")
                if current_id != chunk_id:
                    continue
                content = chunk.get("page_content") or chunk.get("content") or ""
                chunk_data = {
                    "id": current_id,
                    "doc_id": metadata.get("doc_id"),
                    "source": metadata.get("title") or metadata.get("original_filename"),
                    "source_file": chunk.get("file_name") or metadata.get("original_filename"),
                    "page": chunk.get("page_num") or chunk.get("page"),
                    "content": content,
                    "relevance_score": 1.0,
                    "source_type": "user_upload",
                    "page_url": (
                        f"/api/knowledge/uploads/{metadata.get('doc_id')}/pdf#page={chunk.get('page_num') or chunk.get('page')}"
                        if chunk.get("page_num") or chunk.get("page")
                        else f"/api/knowledge/uploads/{metadata.get('doc_id')}/pdf"
                    ),
                    "metadata": chunk.get("metadata") or {},
                }
                _chunks_cache[chunk_id] = chunk_data
                return create_response(chunk_data)

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
