from __future__ import annotations
# Chat API - 智能问答接口 (RAG 增强版)
"""
智能问答 API

端点:
- POST /chat - 非流式对话 (支持 RAG)
- GET /chat/stream - 流式对话 (SSE, 支持 RAG)
- GET /chat/history - 获取对话历史 (暂存内存)
- DELETE /chat/history - 清除对话历史

RAG 增强:
- 自动检索知识库中的相关内容
- 注入周摘要上下文 (Working Context L1)
- 返回引用来源
"""

import sys
import json
import re
import uuid
import base64
import mimetypes
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.core.openai_compat import completion_token_kwargs, temperature_kwargs
from app.services.llm_service import llm_service
from app.services.episode_service import get_weekly_context

# 添加 src 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 导入 RAG 服务
try:
    from cucumber_irrigation.services.local_rag_service import LocalRAGService, LocalRAGConfig
    _rag_service = LocalRAGService(config=LocalRAGConfig(top_k=3))
    RAG_AVAILABLE = _rag_service.is_available
    print(f"[chat.py] RAG 服务可用: {RAG_AVAILABLE}")
except Exception as e:
    _rag_service = None
    RAG_AVAILABLE = False
    print(f"[chat.py] RAG 服务不可用: {e}")


router = APIRouter(prefix="/chat", tags=["chat"])
USER_LITERATURE_DIR = PROJECT_ROOT / "data" / "user_literature"
CHAT_ATTACHMENTS_DIR = PROJECT_ROOT / "data" / "chat_attachments"
MAX_CHAT_IMAGE_BYTES = 20 * 1024 * 1024
SUPPORTED_CHAT_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# 临时内存存储对话历史 (后续可改为数据库)
_conversation_history: List[dict] = []


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    use_history: bool = True  # 是否使用对话历史
    use_rag: bool = True      # 是否使用 RAG 检索
    attachment_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def _is_uploaded_literature_query(query: str) -> bool:
    q = query.lower()
    upload_terms = ("上传", "送审", "论文", "文献", "pdf", "附件", "这篇", "那个")
    intent_terms = ("讲什么", "是什么", "内容", "总结", "概括", "摘要", "研究", "方向", "主题")
    return any(term in q for term in upload_terms) and any(term in q for term in intent_terms)


def _safe_attachment_filename(name: str) -> str:
    suffix = Path(name).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._") or "image"
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{stem}{suffix}"


def _chat_attachment_public_url(path: Path) -> str:
    try:
        rel = path.relative_to(CHAT_ATTACHMENTS_DIR).as_posix()
    except ValueError:
        rel = path.name
    return f"/static/chat_attachments/{rel}"


def _chat_attachment_metadata_path(attachment_id: str) -> Path:
    return CHAT_ATTACHMENTS_DIR / f"{attachment_id}.metadata.json"


def _write_chat_attachment_metadata(metadata: dict) -> None:
    CHAT_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = Path(metadata["metadata_path"])
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_chat_attachment(attachment_id: Optional[str]) -> Optional[dict]:
    if not attachment_id:
        return None
    metadata_path = _chat_attachment_metadata_path(attachment_id)
    if not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    stored_path = Path(metadata.get("stored_path") or "")
    if not stored_path.exists():
        return None
    return metadata


def _image_attachment_to_data_url(attachment: dict) -> str:
    stored_path = Path(attachment["stored_path"])
    mime_type = attachment.get("mime_type") or mimetypes.guess_type(stored_path.name)[0] or "image/png"
    encoded = base64.b64encode(stored_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_user_message(query: str, attachment: Optional[dict] = None) -> dict:
    if not attachment:
        return {"role": "user", "content": query}
    text = query.strip() or "请分析这张图片，并结合 AgriAgent 系统给出专业回复。"
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": _image_attachment_to_data_url(attachment)}},
        ],
    }


def _attachment_history_text(query: str, attachment: Optional[dict]) -> str:
    if not attachment:
        return query
    filename = attachment.get("original_filename") or attachment.get("stored_filename") or "image"
    return f"{query}\n[uploaded_image: {filename}]"


@router.post("/attachments/image")
async def upload_chat_image(file: UploadFile = File(...)):
    """Upload an image attachment for a normal AgriAgent chat turn."""
    original_filename = file.filename or "image.png"
    suffix = Path(original_filename).suffix.lower()
    content_type = (file.content_type or mimetypes.guess_type(original_filename)[0] or "").lower()

    if suffix not in SUPPORTED_CHAT_IMAGE_EXTENSIONS or not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image attachments are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty image attachment")
    if len(content) > MAX_CHAT_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image attachment exceeds 20MB")

    CHAT_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    stored_filename = _safe_attachment_filename(original_filename)
    stored_path = CHAT_ATTACHMENTS_DIR / stored_filename
    stored_path.write_bytes(content)
    attachment_id = stored_path.stem
    metadata_path = _chat_attachment_metadata_path(attachment_id)
    metadata = {
        "attachment_id": attachment_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "stored_path": str(stored_path),
        "metadata_path": str(metadata_path),
        "public_url": _chat_attachment_public_url(stored_path),
        "mime_type": content_type,
        "size_bytes": len(content),
        "uploaded_at": datetime.now().isoformat(),
    }
    _write_chat_attachment_metadata(metadata)
    return {
        "success": True,
        "data": metadata,
    }


def _query_mentions_uploaded_literature(query: str) -> bool:
    q = query.lower()
    upload_terms = ("上传", "送审", "论文", "文献", "pdf", "附件", "这篇", "那个")
    return any(term in q for term in upload_terms)


def _normalize_doc_match_text(value: str) -> str:
    text = (value or "").lower()
    text = re.sub(r"\.(pdf|txt|md)$", "", text)
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    for token in ("的", "这篇", "那篇", "论文", "文献", "文件", "pdf"):
        text = text.replace(token, "")
    return text


def _metadata_match_score(query: str, metadata: dict) -> int:
    q_norm = _normalize_doc_match_text(query)
    score = 0
    candidates = [
        metadata.get("title"),
        metadata.get("original_filename"),
        metadata.get("stored_filename"),
        metadata.get("doc_id"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        text = str(candidate).lower()
        stem = Path(text).stem.lower()
        c_norm = _normalize_doc_match_text(stem or text)
        if c_norm and (c_norm in q_norm or q_norm in c_norm):
            score = max(score, 100)
        elif stem and len(stem) >= 2 and stem in query.lower():
            score = max(score, 80)

    if _query_mentions_uploaded_literature(query):
        score = max(score, 1)
    return score


def _extract_uploaded_query_terms(query: str) -> list[str]:
    q = query.lower()
    terms: set[str] = set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_+.-]{1,}", q))
    phrase_map = {
        "模型": ("模型", "model", "models", "architecture"),
        "使用": ("使用", "used", "using", "employed", "applied", "utilized", "pipeline", "workflow"),
        "怎么": ("used", "using", "employed", "applied", "method", "approach"),
        "如何": ("used", "using", "employed", "applied", "method", "approach"),
        "方法": ("method", "approach", "pipeline", "workflow"),
        "结构": ("structure", "architecture", "backbone", "neck", "head"),
        "改进": ("improved", "enhanced", "optimization", "FBC", "HyperNeck", "LSCDHead"),
        "识别": ("recognition", "detection", "segmentation"),
        "检测": ("detection", "segmentation"),
        "分割": ("segmentation", "instance segmentation"),
        "训练": ("training", "trained", "dataset"),
        "结果": ("result", "results", "performance", "mAP", "precision"),
        "灌水": ("irrigation", "water", "water demand"),
        "灌溉": ("irrigation", "water", "water demand"),
        "特征": ("feature", "features", "phenotypic"),
    }
    for phrase, mapped_terms in phrase_map.items():
        if phrase in query:
            terms.update(term.lower() for term in mapped_terms)

    # Keep short Chinese technical terms only; long title fragments are handled
    # by metadata matching and should not dominate chunk retrieval.
    for term in re.findall(r"[\u4e00-\u9fff]{2,6}", query):
        if term not in {"这篇论文", "论文中", "文献中"}:
            terms.add(term)
    return sorted(terms, key=len, reverse=True)


def _score_uploaded_chunk(query_terms: list[str], chunk: dict) -> int:
    content = (chunk.get("page_content") or chunk.get("content") or "").lower()
    if not content:
        return 0
    score = 0
    high_value_terms = {
        "yolo",
        "yolo11",
        "yolo11n",
        "tsmixer",
        "rag",
        "fao56",
        "fao-56",
        "chromadb",
        "postgresql",
        "redis",
        "langgraph",
        "mcp",
    }
    generic_terms = {
        "model",
        "models",
        "method",
        "approach",
        "using",
        "used",
        "applied",
        "employed",
        "pipeline",
        "workflow",
        "architecture",
    }
    for term in query_terms:
        term_l = term.lower().strip()
        if not term_l or term_l not in content:
            continue
        occurrence_count = min(content.count(term_l), 5)
        if term_l in high_value_terms:
            score += 60 + occurrence_count * 10
        elif term_l in generic_terms:
            score += occurrence_count * 2
        else:
            score += max(2, min(len(term_l), 18)) + occurrence_count

    if "yolo" in query_terms and "yolo" in content:
        if "segmentation" in content or "分割" in content:
            score += 20
        if "improved" in content or "enhanced" in content or "改进" in content:
            score += 15
        if "fbc" in content or "hyperneck" in content or "lscdhead" in content or "inner-iou" in content:
            score += 15

    if "tsmixer" in query_terms and "tsmixer" in content:
        if "irrigation" in content or "灌溉" in content or "灌水" in content:
            score += 20
        if "time-series" in content or "time series" in content or "时间序列" in content:
            score += 15
    return score


def _uploaded_chunk_snippet(content: str, query_terms: list[str], max_chars: int = 1000) -> str:
    if len(content) <= max_chars:
        return content

    lowered = content.lower()
    anchor_terms = [
        term.lower()
        for term in query_terms
        if term.lower() in {"yolo", "yolo11", "yolo11n", "tsmixer", "rag", "fao56", "fao-56"}
    ]
    anchor_terms.extend(term.lower() for term in query_terms if len(term) >= 4)

    anchor_positions = [lowered.find(term) for term in anchor_terms if term and lowered.find(term) >= 0]
    if not anchor_positions:
        return content[:max_chars]

    start = max(min(anchor_positions) - 180, 0)
    end = min(start + max_chars, len(content))
    snippet = content[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(content):
        snippet = f"{snippet}..."
    return snippet


def _is_uploaded_literature_asset_query(query: str) -> bool:
    q = query.lower()
    asset_terms = (
        "图",
        "图片",
        "图表",
        "结果图",
        "结果图片",
        "抽图",
        "抽取图片",
        "提取图片",
        "figure",
        "fig",
        "image",
        "chart",
        "展示",
        "显示",
        "查看",
        "看一下",
    )
    filename_only = bool(re.fullmatch(r"[\w\s.\-\u4e00-\u9fff]+\.pdf", q.strip()))
    return _query_mentions_uploaded_literature(q) and (filename_only or any(term in q for term in asset_terms))


def _is_uploaded_literature_visual_topic(query: str) -> bool:
    q = query.lower()
    visual_terms = (
        "图",
        "图片",
        "图表",
        "带图",
        "配图",
        "结构",
        "框架",
        "模型",
        "改进",
        "结果",
        "分割",
        "识别",
        "检测",
        "展示",
        "显示",
        "figure",
        "fig",
        "image",
        "chart",
        "result",
        "architecture",
        "structure",
        "framework",
        "model",
        "yolo",
        "yolo11",
        "yolo11n",
        "tsmixer",
        "backbone",
        "neck",
        "head",
        "fbc",
        "hyperneck",
        "lscdhead",
        "inner-iou",
        "map",
        "precision",
    )
    return any(term in q for term in visual_terms)


def _is_contextual_followup(query: str) -> bool:
    q = query.lower().strip()
    if len(q) <= 24:
        return True
    followup_terms = (
        "继续",
        "上面",
        "上述",
        "刚才",
        "前面",
        "这个",
        "那个",
        "这篇",
        "它",
        "一起",
        "带图",
        "配图",
        "详细",
        "展开",
        "补充",
        "再说",
        "最好",
        "also",
        "continue",
        "same",
        "previous",
        "above",
        "with figure",
        "with image",
    )
    return any(term in q for term in followup_terms)


def _recent_uploaded_literature_context_query(max_messages: int = 8) -> Optional[str]:
    if not USER_LITERATURE_DIR.exists() or not _conversation_history:
        return None

    recent_messages = _conversation_history[-max_messages:]
    recent_text = "\n".join(str(message.get("content") or "") for message in recent_messages)
    if not recent_text.strip():
        return None

    recent_norm = _normalize_doc_match_text(recent_text)
    metadata_files = sorted(
        USER_LITERATURE_DIR.glob("*.metadata.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for metadata_file in metadata_files:
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        candidates = [
            metadata.get("title"),
            metadata.get("original_filename"),
            metadata.get("stored_filename"),
            metadata.get("doc_id"),
        ]
        matched = False
        for candidate in candidates:
            if not candidate:
                continue
            candidate_text = str(candidate)
            candidate_norm = _normalize_doc_match_text(candidate_text)
            if candidate_text and candidate_text in recent_text:
                matched = True
                break
            if candidate_norm and candidate_norm in recent_norm:
                matched = True
                break
        if not matched:
            raw_assets = metadata.get("assets") or []
            matched = any(
                isinstance(asset, dict)
                and asset.get("asset_id")
                and str(asset.get("asset_id")) in recent_text
                for asset in raw_assets
            )
        if matched:
            title = metadata.get("title") or metadata.get("original_filename") or metadata_file.stem
            filename = metadata.get("original_filename") or metadata.get("stored_filename") or ""
            recent_user = next(
                (
                    str(message.get("content") or "")
                    for message in reversed(recent_messages)
                    if message.get("role") == "user"
                ),
                "",
            )
            return f"{title} {filename} {recent_user}".strip()

    return None


def _contextualize_uploaded_literature_query(query: str) -> str:
    if _query_mentions_uploaded_literature(query) or _is_uploaded_literature_query(query):
        return query
    if not (_is_contextual_followup(query) or _is_uploaded_literature_visual_topic(query)):
        return query
    recent_context = _recent_uploaded_literature_context_query()
    if not recent_context:
        return query
    return f"{recent_context} {query}".strip()


def _references_include_uploaded_literature(references: list) -> bool:
    return any(ref.get("source_type") == "user_upload" for ref in references if isinstance(ref, dict))


def _should_attach_uploaded_literature_assets(query: str, rag_query: str, references: list) -> bool:
    if _is_uploaded_literature_asset_query(query) or _is_uploaded_literature_asset_query(rag_query):
        return True
    if _references_include_uploaded_literature(references):
        return _is_uploaded_literature_visual_topic(f"{query} {rag_query}")
    return False


async def _prepare_rag_payload(query: str, use_rag: bool = True) -> tuple[Optional[str], list, list[dict], str]:
    if not use_rag:
        return None, [], [], query

    rag_query = _contextualize_uploaded_literature_query(query)
    rag_context, references = await _search_rag(rag_query)
    assets: list[dict] = []
    if _should_attach_uploaded_literature_assets(query, rag_query, references):
        assets = _load_uploaded_literature_assets(rag_query)
        if not assets and rag_query != query:
            assets = _load_uploaded_literature_assets(query)
        rag_context = _merge_asset_context(rag_context, assets)
    return rag_context, references, assets, rag_query


def _metadata_matches_query(query: str, metadata: dict) -> bool:
    return _metadata_match_score(query, metadata) > 0


def _load_uploaded_literature_chunks(metadata: dict, metadata_file: Path) -> list[dict]:
    chunks_path = Path(metadata.get("chunks_path") or "")
    if not chunks_path.exists():
        chunks_path = USER_LITERATURE_DIR / f"{metadata.get('doc_id', metadata_file.stem)}_chunks.json"
    try:
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return chunks if isinstance(chunks, list) else []


def _load_uploaded_literature_assets(query: str, max_assets: int = 12) -> list[dict]:
    if not USER_LITERATURE_DIR.exists():
        return []

    metadata_files = sorted(
        USER_LITERATURE_DIR.glob("*.metadata.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not metadata_files:
        return []

    q = query.lower()
    result_focused = any(term in q for term in ("结果", "影响", "产量", "品质", "模型", "验证", "result"))
    result_terms = ("第三章", "第四章", "第五章", "第六章", "图3-", "图4-", "图5-", "图6-", "结果", "影响", "产量", "品质", "模型", "验证")
    figure_terms = ("图", "Figure", "figure", "Fig", "fig")

    for metadata_file in metadata_files:
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[chat.py] failed to load uploaded literature metadata {metadata_file}: {exc}")
            continue
        if not _metadata_matches_query(query, metadata):
            continue

        raw_assets = metadata.get("assets") or []
        if not isinstance(raw_assets, list) or not raw_assets:
            continue

        chunks = _load_uploaded_literature_chunks(metadata, metadata_file)
        result_pages: set[int] = set()
        captions_by_page: dict[int, str] = {}
        for chunk in chunks:
            try:
                page = int(chunk.get("page_num") or chunk.get("page") or 0)
            except (TypeError, ValueError):
                page = 0
            if page <= 0:
                continue
            content = (chunk.get("page_content") or chunk.get("content") or "").strip()
            if any(term in content for term in figure_terms):
                captions_by_page.setdefault(page, content[:220])
            if any(term in content for term in result_terms):
                result_pages.add(page)

        original_filename = metadata.get("original_filename") or metadata.get("stored_filename") or metadata_file.name
        title = metadata.get("title") or original_filename
        enriched_assets = []
        doc_metadata = metadata
        for asset in raw_assets:
            if not isinstance(asset, dict):
                continue
            if (asset.get("asset_type") or "image") != "image":
                continue
            try:
                page = int(asset.get("page_num") or asset.get("page") or 0)
            except (TypeError, ValueError):
                page = 0
            public_url = asset.get("public_url")
            if not public_url:
                continue
            width = asset.get("width") or 0
            height = asset.get("height") or 0
            try:
                area = int(width) * int(height)
            except (TypeError, ValueError):
                area = 0
            score = 0
            caption = captions_by_page.get(page) or ""
            asset_metadata = asset.get("metadata") or {}
            layout_label = asset_metadata.get("layout_label")
            searchable_asset_text = " ".join(
                str(value)
                for value in (
                    asset.get("asset_id"),
                    asset.get("file_path"),
                    asset.get("public_url"),
                    layout_label,
                    caption,
                )
                if value
            ).lower()
            if page in result_pages:
                score += 100
            if any(term in q for term in ("结果", "result", "预测", "对比", "验证")) and any(
                term in searchable_asset_text
                for term in ("result", "prediction", "predict", "comparison", "validation", "model", "fig. 6", "fig 6")
            ):
                score += 65
            if any(term in q for term in ("yolo", "结构", "框架", "模型", "tsmixer")) and any(
                term in searchable_asset_text
                for term in ("yolo", "tsmixer", "framework", "model", "hyperneck", "structure", "architecture")
            ):
                score += 45
            if result_focused and page >= 30:
                score += 25
            if layout_label in {"figure", "table"}:
                score += 30
            if layout_label == "figure" and any(term in q for term in ("图", "图片", "figure", "fig")):
                score += 10
            if layout_label == "table" and not any(term in q for term in ("表", "table")):
                score -= 8
            if "layout_crops" in str(asset.get("public_url") or asset.get("file_path") or ""):
                score += 20
            if area >= 120_000:
                score += 10
            if page <= 2:
                score -= 30

            enriched = dict(asset)
            enriched.update({
                "doc_id": asset.get("doc_id") or doc_metadata.get("doc_id"),
                "source_title": title,
                "source_file": original_filename,
                "page_num": page or asset.get("page_num"),
                "caption": caption,
                "_score": score,
            })
            enriched_assets.append(enriched)

        enriched_assets.sort(key=lambda item: (item.get("_score", 0), item.get("page_num") or 0), reverse=True)
        selected = enriched_assets[:max_assets]
        for item in selected:
            item.pop("_score", None)
        return selected

    return []


def _format_uploaded_assets_markdown(assets: list[dict]) -> str:
    if not assets:
        return ""

    lines = ["", "", "我已经从上传 PDF 的图片资产中找到相关图片，下面直接展示："]
    for index, asset in enumerate(assets, 1):
        title = asset.get("source_title") or asset.get("source_file") or "上传文献"
        page = asset.get("page_num") or "N/A"
        public_url = asset.get("public_url")
        if not public_url:
            continue
        lines.append(f"![{title} P{page} 图{index}]({public_url})")
        caption = asset.get("caption")
        if caption:
            lines.append(f"图注/页内文本：{caption[:180]}")
    return "\n".join(lines).strip()


def _format_uploaded_asset_tokens(assets: list[dict]) -> str:
    if not assets:
        return ""
    lines = ["", "", "相关图片："]
    for asset in assets[:8]:
        asset_id = asset.get("asset_id")
        if asset_id:
            lines.append(f"[[asset:{asset_id}]]")
    return "\n".join(lines).strip()


def _append_uploaded_asset_markdown(answer: str, assets: list[dict]) -> str:
    markdown = _format_uploaded_asset_tokens(assets)
    if not markdown:
        return answer
    if any(asset.get("asset_id") and f"[[asset:{asset['asset_id']}]]" in answer for asset in assets):
        return answer
    return f"{answer.rstrip()}\n\n{markdown}".strip()


def _merge_asset_context(rag_context: Optional[str], assets: list[dict]) -> Optional[str]:
    if not assets:
        return rag_context
    asset_lines = []
    for index, asset in enumerate(assets, 1):
        token = f"[[asset:{asset.get('asset_id')}]]" if asset.get("asset_id") else f"asset-{index}"
        asset_lines.append(
            f"[asset-{index}] token={token} ({asset.get('source_title') or asset.get('source_file')}, "
            f"P{asset.get('page_num') or 'N/A'}): {asset.get('public_url')}"
        )
        if asset.get("caption"):
            asset_lines.append(f"caption: {asset['caption'][:220]}")
    asset_context = "\n".join(asset_lines)
    if rag_context:
        return f"{rag_context}\n\n<uploaded_pdf_assets>\n{asset_context}\n</uploaded_pdf_assets>"
    return f"<uploaded_pdf_assets>\n{asset_context}\n</uploaded_pdf_assets>"


def _load_uploaded_literature_context(query: str, top_k: int = 3) -> tuple[Optional[str], list]:
    if not USER_LITERATURE_DIR.exists():
        return None, []

    metadata_files = sorted(
        USER_LITERATURE_DIR.glob("*.metadata.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not metadata_files:
        return None, []

    context_parts: list[str] = []
    references: list[dict] = []
    generic_doc_question = _is_uploaded_literature_query(query)
    uploaded_query = _query_mentions_uploaded_literature(query)
    query_terms = _extract_uploaded_query_terms(query)
    max_references = max(top_k, 7) if uploaded_query else top_k

    matched_metadata: list[tuple[int, float, Path, dict]] = []
    for metadata_file in metadata_files:
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[chat.py] failed to load uploaded literature metadata {metadata_file}: {exc}")
            continue
        score = _metadata_match_score(query, metadata)
        if score > 0:
            matched_metadata.append((score, metadata_file.stat().st_mtime, metadata_file, metadata))

    if not matched_metadata and uploaded_query:
        for metadata_file in metadata_files[:top_k]:
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            matched_metadata.append((1, metadata_file.stat().st_mtime, metadata_file, metadata))

    matched_metadata.sort(key=lambda item: (item[0], item[1]), reverse=True)

    for metadata_score, _, metadata_file, metadata in matched_metadata[:max(top_k, 3)]:
        try:
            chunks_path = Path(metadata.get("chunks_path") or "")
            if not chunks_path.exists():
                chunks_path = USER_LITERATURE_DIR / f"{metadata.get('doc_id', metadata_file.stem)}_chunks.json"
            chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[chat.py] failed to load uploaded literature chunks {metadata_file}: {exc}")
            continue

        if not isinstance(chunks, list) or not chunks:
            continue

        selected_chunks: list[dict] = []
        scored_chunks = []
        for index, chunk in enumerate(chunks):
            chunk_score = _score_uploaded_chunk(query_terms, chunk)
            if chunk_score > 0:
                scored_chunks.append((chunk_score, -index, chunk))

        scored_chunks.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_chunks.extend(chunk for _, _, chunk in scored_chunks[:max_references])

        if selected_chunks and uploaded_query and chunks[0] not in selected_chunks:
            selected_chunks.insert(0, chunks[0])

        if not selected_chunks and generic_doc_question:
            priority_terms = ("摘要", "研究目的", "研究内容", "研究结果", "结论", "本研究", "主要研究")
            selected_chunks.extend(chunks[:2])
            selected_chunks.extend(
                chunk for chunk in chunks[2:] if any(term in (chunk.get("page_content") or "") for term in priority_terms)
            )

        if not selected_chunks:
            selected_chunks = chunks[:2]

        deduped_chunks: list[dict] = []
        seen_chunk_keys: set[str] = set()
        for chunk in selected_chunks:
            key = str(chunk.get("unique_id") or chunk.get("doc_id") or chunk.get("chunk_id") or (chunk.get("page_content") or "")[:80])
            if key in seen_chunk_keys:
                continue
            seen_chunk_keys.add(key)
            deduped_chunks.append(chunk)

        original_filename = metadata.get("original_filename") or metadata.get("stored_filename") or chunks_path.name
        title = metadata.get("title") or original_filename
        for chunk in deduped_chunks[:max_references]:
            content = (chunk.get("page_content") or chunk.get("content") or "").strip()
            if not content:
                continue
            snippet = _uploaded_chunk_snippet(content, query_terms, max_chars=1000)
            source = chunk.get("file_name") or original_filename
            page = chunk.get("page_num") or chunk.get("page")
            label = f"{title} / {source}"
            context_parts.append(f"[{len(references) + 1}] ({label}, P{page or 'N/A'}): {snippet}")
            references.append({
                "doc_id": chunk.get("unique_id") or chunk.get("doc_id") or metadata.get("doc_id"),
                "parent_doc_id": metadata.get("doc_id"),
                "title": title,
                "source": source,
                "source_type": "user_upload",
                "page": page,
                "page_url": f"/api/knowledge/uploads/{metadata.get('doc_id')}/pdf#page={page}" if page else f"/api/knowledge/uploads/{metadata.get('doc_id')}/pdf",
                "detail_url": f"/api/knowledge/chunks/{chunk.get('unique_id') or chunk.get('doc_id') or metadata.get('doc_id')}",
                "snippet": snippet[:150] + "..." if len(snippet) > 150 else snippet,
                "relevance": 1.0 if metadata_score >= 100 else 0.9,
            })
            if len(references) >= max_references:
                break

        if references and (metadata_score >= 100 or len(references) >= max_references):
            break

    if not context_parts:
        return None, []
    return "\n".join(context_parts), references


def _count_uploaded_literature() -> tuple[int, int]:
    if not USER_LITERATURE_DIR.exists():
        return 0, 0
    doc_count = 0
    chunk_count = 0
    for metadata_file in USER_LITERATURE_DIR.glob("*.metadata.json"):
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            doc_count += 1
            chunk_count += int(metadata.get("chunk_count") or 0)
        except Exception:
            continue
    return doc_count, chunk_count


async def _search_rag(query: str, top_k: int = 3) -> tuple:
    """
    执行 RAG 检索

    Returns:
        (rag_context_text, references_list)
    """
    if _query_mentions_uploaded_literature(query) or _is_uploaded_literature_query(query) or _is_uploaded_literature_asset_query(query):
        upload_context, upload_references = _load_uploaded_literature_context(query, top_k=top_k)
        if upload_context:
            return upload_context, upload_references

    try:
        if RAG_AVAILABLE and _rag_service is not None:
            results = _rag_service.search(query, top_k=top_k)
        else:
            from app.services.rag_service import rag_service

            docs = await rag_service.retrieve(query, top_k=top_k)
            results = []
            for doc in docs:
                metadata = getattr(doc, "metadata", None) or {}
                snippet = getattr(doc, "page_content", None) or getattr(doc, "snippet", "")
                results.append(type("RAGResult", (), {
                    "doc_id": getattr(doc, "doc_id", None) or metadata.get("chunk_id", "local_doc"),
                    "is_fao56": (metadata.get("is_fao56") is True) or ("fao56" in (metadata.get("source") or "").lower()),
                    "source": metadata.get("source") or getattr(doc, "title", None) or "local_keyword",
                    "page": metadata.get("page"),
                    "snippet": snippet,
                    "relevance_score": getattr(doc, "relevance", None) or 0.0,
                })())

        if not results:
            upload_context, upload_references = _load_uploaded_literature_context(query, top_k=top_k)
            if upload_context and (
                _query_mentions_uploaded_literature(query)
                or _is_uploaded_literature_query(query)
                or _is_uploaded_literature_asset_query(query)
            ):
                return upload_context, upload_references
            return None, []

        # 构建上下文文本
        context_parts = []
        references = []

        for i, r in enumerate(results, 1):
            source_tag = "FAO56" if r.is_fao56 else r.source
            context_parts.append(f"[{i}] ({source_tag}, P{r.page}): {r.snippet}")
            references.append({
                "doc_id": r.doc_id,
                "parent_doc_id": r.doc_id,
                "source": source_tag,
                "source_type": "fao56" if r.is_fao56 else "system",
                "page": r.page,
                "detail_url": f"/api/knowledge/chunks/{r.doc_id}",
                "snippet": r.snippet[:150] + "..." if len(r.snippet) > 150 else r.snippet,
                "relevance": r.relevance_score
            })

        rag_context = "\n".join(context_parts)
        return rag_context, references

    except Exception as e:
        print(f"[chat.py] RAG 检索失败: {e}")
        return None, []


def _build_enhanced_system_prompt(rag_context: Optional[str], weekly_context: Optional[str]) -> str:
    """
    构建增强的系统提示词

    包含:
    - RAG 检索结果
    - 周摘要上下文 (Working Context L1)
    """
    base_prompt = """你是 AGRI-COPILOT，一个专业的温室农业专家助手。

你擅长以下领域：
- 温室黄瓜种植技术与管理
- 灌溉调度与水分管理
- 作物需水量计算 (FAO56 Penman-Monteith)
- 病虫害识别与防治
- 环境调控 (温度、湿度、光照、CO2)
- 营养管理与施肥策略

回答规范：
1. 使用专业但易懂的语言
2. 提供具体可操作的建议
3. 如果引用了知识库内容，请标注来源
4. 如果不确定，请诚实说明
5. 输出保持 ChatGPT 风格的自然段落：每段 2-4 句，不要每个短句都换行，不要频繁使用分割线"""

    # 添加周摘要上下文 (L1)
    if weekly_context:
        base_prompt += f"\n\n<recent_experience>\n{weekly_context}\n</recent_experience>"

    # 添加 RAG 检索结果 (L4)
    if rag_context:
        base_prompt += (
            "\n\n<knowledge_base>\n"
            "以下是已检索到的知识库或用户上传文献内容。回答必须优先依据这些片段；"
            "如果片段来自用户上传 PDF/文献，不要声称无法访问上传文献。"
            "请在回答中标注文件名、页码或编号；如果片段不足，再明确说明缺失的信息。"
            "如果 <uploaded_pdf_assets> 中提供了 [[asset:...]] 图片占位符，请在解释对应图片的位置直接插入该占位符，"
            "不要改写占位符，也不要把所有图片都堆到最后。"
            "当用户询问上传论文里的 YOLO、TSMixer、模型结构、改进方案或实验结果时，只要给出了图片占位符，"
            "就应把最相关图片插入对应说明段落中。\n"
            f"{rag_context}\n</knowledge_base>"
        )

    return base_prompt


def _has_real_llm_key(config: dict) -> bool:
    key = (config.get("api_key") or "").strip()
    if not key:
        return False
    placeholders = {
        "your_api_key_here",
        "your_qwen_or_openai_compatible_key",
        "your_openai_api_key",
        "your_qwen_api_key",
    }
    return key.lower() not in placeholders and not key.lower().startswith("your_")


async def _local_rag_fallback(question: str, rag_context: Optional[str], references: list) -> tuple[str, list]:
    """Build a deterministic local answer when LLM credentials are absent or invalid."""
    if rag_context and references:
        return rag_context, references

    try:
        from app.services.rag_service import rag_service

        docs = await rag_service.retrieve(question, top_k=3)
        fallback_refs = []
        context_parts = []
        for doc in docs:
            metadata = getattr(doc, "metadata", None) or {}
            snippet = getattr(doc, "page_content", None) or getattr(doc, "snippet", "")
            fallback_refs.append({
                "doc_id": getattr(doc, "doc_id", None) or metadata.get("chunk_id", "local_doc"),
                "source": metadata.get("retrieval_backend", "local_keyword"),
                "page": metadata.get("page"),
                "snippet": snippet[:150] + "..." if len(snippet) > 150 else snippet,
                "relevance": getattr(doc, "relevance", None),
            })
            context_parts.append(snippet)
        return "\n".join(context_parts), fallback_refs
    except Exception:
        return "", references


def _compose_local_answer(question: str, context: str, reason: str) -> str:
    if context:
        return (
            "当前对话已进入本地模式：未检测到可用的真实 LLM API Key，"
            "系统先基于本地农业知识库和规则给出可执行答复。\n\n"
            f"问题：{question}\n\n"
            f"参考依据：\n{context}\n\n"
            "建议：温室黄瓜灌水仍需结合当日温度、湿度、光照、植株图像表型和历史灌水量综合判断；"
            "若出现叶片萎蔫、黄化或棚内湿度异常，应人工复核后再执行。"
        )
    return (
        "当前对话已进入本地模式：未检测到可用的真实 LLM API Key，且本地知识库召回不足。\n\n"
        f"问题：{question}\n\n"
        "可先使用“灌水预测/Agent 决策”链路运行一次完整决策；该链路会调用 Router、YOLO、RAG、"
        "TSMixer 和 Plan Agent，并返回 11 维多模态特征与 96 天窗口的决策结果。"
    )


async def _fallback_chat_payload(
    question: str,
    rag_context: Optional[str],
    references: list,
    reason: str,
    assets: Optional[list[dict]] = None,
) -> dict:
    context, refs = await _local_rag_fallback(question, rag_context, references)
    answer = _compose_local_answer(question, context, reason)
    asset_list = assets or []
    if asset_list:
        answer = _append_uploaded_asset_markdown(answer, asset_list)
    return {
        "answer": answer,
        "references": refs,
        "assets": asset_list,
        "rag_used": bool(context),
        "fallback_reason": reason,
    }


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    非流式对话 (支持 RAG)

    Request Body:
    - message: 用户消息
    - use_history: 是否使用对话历史 (默认 True)
    - use_rag: 是否使用 RAG 检索 (默认 True)

    Response:
    - success: 是否成功
    - data.content: AI 回复内容
    - data.role: "assistant"
    - data.references: RAG 引用来源 (如果启用)
    - data.rag_used: 是否使用了 RAG
    """
    try:
        attachment = _load_chat_attachment(request.attachment_id)
        if request.attachment_id and not attachment:
            raise HTTPException(status_code=404, detail="Image attachment not found")

        # 1. RAG 检索
        rag_context = None
        references = []
        assets = []
        if request.use_rag:
            rag_context, references, assets, _ = await _prepare_rag_payload(request.message, request.use_rag)

        # 2. 获取周摘要上下文 (L1)
        weekly_context = get_weekly_context()

        # 3. 构建增强的系统提示词
        enhanced_system = _build_enhanced_system_prompt(rag_context, weekly_context)

        # 4. 准备对话历史
        history = _conversation_history.copy() if request.use_history else []

        # 5. 调用 LLM (使用增强的系统提示词)
        from openai import AsyncOpenAI
        from app.core.config import get_active_openai_config

        config = get_active_openai_config()
        if not _has_real_llm_key(config):
            fallback = await _fallback_chat_payload(
                request.message,
                rag_context,
                references,
                "missing_or_placeholder_llm_key",
                assets=assets,
            )
            answer = fallback["answer"]
            _conversation_history.append({"role": "user", "content": _attachment_history_text(request.message, attachment)})
            _conversation_history.append({"role": "assistant", "content": answer})
            if len(_conversation_history) > 40:
                _conversation_history[:] = _conversation_history[-40:]
            return ChatResponse(
                success=True,
                data={
                    "role": "assistant",
                    "content": answer,
                    "references": fallback["references"],
                    "assets": fallback["assets"],
                    "rag_used": fallback["rag_used"],
                    "weekly_context_used": weekly_context is not None,
                    "fallback": True,
                    "fallback_reason": fallback["fallback_reason"],
                },
            )

        client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])

        messages = [{"role": "system", "content": enhanced_system}]
        messages.extend(history)
        messages.append(_build_user_message(request.message, attachment))

        model = config["vision_model"] if attachment else config["model"]
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            **temperature_kwargs(model, 0.7),
            **completion_token_kwargs(model, 2048),
        )
        answer = response.choices[0].message.content or ""
        if assets:
            answer = _append_uploaded_asset_markdown(answer, assets)

        # 6. 保存到历史
        _conversation_history.append({"role": "user", "content": _attachment_history_text(request.message, attachment)})
        _conversation_history.append({"role": "assistant", "content": answer})

        # 限制历史长度 (保留最近 20 条)
        if len(_conversation_history) > 40:
            _conversation_history[:] = _conversation_history[-40:]

        return ChatResponse(
            success=True,
            data={
                "role": "assistant",
                "content": answer,
                "references": references,
                "assets": assets,
                "rag_used": rag_context is not None,
                "weekly_context_used": weekly_context is not None
            }
        )

    except Exception as e:
        fallback = await _fallback_chat_payload(
            request.message,
            None,
            [],
            f"llm_error: {e}",
            assets=locals().get("assets", []),
        )
        answer = fallback["answer"]
        _conversation_history.append({"role": "user", "content": request.message})
        _conversation_history.append({"role": "assistant", "content": answer})
        if len(_conversation_history) > 40:
            _conversation_history[:] = _conversation_history[-40:]
        return ChatResponse(
            success=True,
            data={
                "role": "assistant",
                "content": answer,
                "references": fallback["references"],
                "assets": fallback["assets"],
                "rag_used": fallback["rag_used"],
                "fallback": True,
                "fallback_reason": fallback["fallback_reason"],
            }
        )


@router.get("/stream")
async def chat_stream(
    query: str = Query(..., description="用户问题"),
    use_history: bool = Query(True, description="是否使用对话历史"),
    use_rag: bool = Query(True, description="是否使用 RAG 检索"),
    attachment_id: Optional[str] = Query(None, description="Uploaded image attachment id")
):
    """
    流式对话 (SSE, 支持 RAG)

    Query Parameters:
    - query: 用户问题
    - use_history: 是否使用对话历史
    - use_rag: 是否使用 RAG 检索

    SSE Events:
    - event: rag, data: {"references": [...]}  (RAG 检索结果)
    - event: content, data: {"text": "..."}
    - event: done, data: {}
    - event: error, data: {"message": "..."}
    """
    async def generate():
        try:
            attachment = _load_chat_attachment(attachment_id)
            if attachment_id and not attachment:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Image attachment not found"}, ensure_ascii=False),
                }
                return

            # 1. RAG 检索
            rag_context = None
            references = []
            assets = []
            if use_rag:
                rag_context, references, assets, _ = await _prepare_rag_payload(query, use_rag)

                # 先发送 RAG 检索结果
                if references or assets:
                    yield {
                        "event": "rag",
                        "data": json.dumps({
                            "references": references,
                            "assets": assets,
                            "count": len(references),
                            "asset_count": len(assets),
                        }, ensure_ascii=False)
                    }

            # 2. 获取周摘要上下文 (L1)
            weekly_context = get_weekly_context()

            # 3. 构建增强的系统提示词
            enhanced_system = _build_enhanced_system_prompt(rag_context, weekly_context)

            # 4. 准备对话历史
            history = _conversation_history.copy() if use_history else []

            # 5. 流式调用 LLM
            from openai import AsyncOpenAI
            from app.core.config import get_active_openai_config

            config = get_active_openai_config()
            if not _has_real_llm_key(config):
                fallback = await _fallback_chat_payload(
                    query,
                    rag_context,
                    references,
                    "missing_or_placeholder_llm_key",
                    assets=assets,
                )
                for chunk in [fallback["answer"][i:i + 80] for i in range(0, len(fallback["answer"]), 80)]:
                    yield {
                        "event": "content",
                        "data": json.dumps({"text": chunk}, ensure_ascii=False)
                    }
                _conversation_history.append({"role": "user", "content": _attachment_history_text(query, attachment)})
                _conversation_history.append({"role": "assistant", "content": fallback["answer"]})
                if len(_conversation_history) > 40:
                    _conversation_history[:] = _conversation_history[-40:]
                yield {
                    "event": "done",
                    "data": json.dumps({
                        "rag_used": fallback["rag_used"],
                        "weekly_context_used": weekly_context is not None,
                        "fallback": True,
                        "fallback_reason": fallback["fallback_reason"],
                        "assets": fallback["assets"],
                    }, ensure_ascii=False)
                }
                return

            client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])

            messages = [{"role": "system", "content": enhanced_system}]
            messages.extend(history)
            messages.append(_build_user_message(query, attachment))

            full_response = ""
            model = config["vision_model"] if attachment else config["model"]
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **temperature_kwargs(model, 0.7),
                **completion_token_kwargs(model, 2048),
            )

            pending_text = ""
            last_flush = time.perf_counter()
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    pending_text += text
                    now = time.perf_counter()
                    should_flush = (
                        len(pending_text) >= 36
                        or pending_text.endswith(("\n\n", "。", "！", "？", "；", ". ", "! ", "? "))
                        or (len(pending_text) >= 16 and now - last_flush >= 0.16)
                    )
                    if should_flush:
                        yield {
                            "event": "content",
                            "data": json.dumps({"text": pending_text}, ensure_ascii=False)
                        }
                        pending_text = ""
                        last_flush = now

            if pending_text:
                yield {
                    "event": "content",
                    "data": json.dumps({"text": pending_text}, ensure_ascii=False)
                }

            if assets:
                asset_markdown = _format_uploaded_asset_tokens(assets)
                if asset_markdown and not any(
                    asset.get("asset_id") and f"[[asset:{asset['asset_id']}]]" in full_response
                    for asset in assets
                ):
                    streamed_asset_markdown = f"\n\n{asset_markdown}"
                    full_response += streamed_asset_markdown
                    yield {
                        "event": "content",
                        "data": json.dumps({"text": streamed_asset_markdown}, ensure_ascii=False)
                    }

            # 6. 保存到历史
            _conversation_history.append({"role": "user", "content": _attachment_history_text(query, attachment)})
            _conversation_history.append({"role": "assistant", "content": full_response})

            # 限制历史长度
            if len(_conversation_history) > 40:
                _conversation_history[:] = _conversation_history[-40:]

            yield {
                "event": "done",
                "data": json.dumps({
                    "rag_used": rag_context is not None,
                    "weekly_context_used": weekly_context is not None,
                    "assets": assets,
                }, ensure_ascii=False)
            }

        except Exception as e:
            fallback = await _fallback_chat_payload(
                query,
                None,
                [],
                f"llm_error: {e}",
                assets=locals().get("assets", []),
            )
            for chunk in [fallback["answer"][i:i + 80] for i in range(0, len(fallback["answer"]), 80)]:
                yield {
                    "event": "content",
                    "data": json.dumps({"text": chunk}, ensure_ascii=False)
                }
            _conversation_history.append({"role": "user", "content": query})
            _conversation_history.append({"role": "assistant", "content": fallback["answer"]})
            if len(_conversation_history) > 40:
                _conversation_history[:] = _conversation_history[-40:]
            yield {
                "event": "done",
                "data": json.dumps({
                    "rag_used": fallback["rag_used"],
                    "fallback": True,
                    "fallback_reason": fallback["fallback_reason"],
                    "assets": fallback["assets"],
                }, ensure_ascii=False)
            }

    return EventSourceResponse(generate())


@router.get("/history")
async def get_history():
    """获取对话历史"""
    return {
        "success": True,
        "data": {
            "messages": _conversation_history,
            "count": len(_conversation_history)
        }
    }


@router.delete("/history")
async def clear_history():
    """清除对话历史"""
    _conversation_history.clear()
    return {
        "success": True,
        "message": "对话历史已清除"
    }


@router.get("/test")
async def test_connection():
    """测试 LLM 连接"""
    result = await llm_service.test_connection()
    return {
        "success": result["success"],
        "data": result
    }


@router.get("/rag-status")
async def get_rag_status():
    """获取 RAG 状态"""
    uploaded_docs, uploaded_chunks = _count_uploaded_literature()
    app_rag_chunks = 0
    try:
        from app.services.rag_service import rag_service

        app_rag_chunks = len(getattr(rag_service, "_documents", []) or [])
    except Exception:
        app_rag_chunks = 0

    return {
        "success": True,
        "data": {
            "rag_available": RAG_AVAILABLE or app_rag_chunks > 0 or uploaded_chunks > 0,
            "legacy_local_rag_available": RAG_AVAILABLE,
            "fallback_rag_available": app_rag_chunks > 0 or uploaded_chunks > 0,
            "chunk_count": (
                _rag_service.store.chunk_count
                if RAG_AVAILABLE and _rag_service
                else max(app_rag_chunks, uploaded_chunks)
            ),
            "uploaded_documents": uploaded_docs,
            "uploaded_chunks": uploaded_chunks,
            "weekly_context_available": get_weekly_context() is not None
        }
    }
