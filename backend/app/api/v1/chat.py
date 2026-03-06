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
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
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


# 临时内存存储对话历史 (后续可改为数据库)
_conversation_history: List[dict] = []


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    use_history: bool = True  # 是否使用对话历史
    use_rag: bool = True      # 是否使用 RAG 检索


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def _search_rag(query: str, top_k: int = 3) -> tuple:
    """
    执行 RAG 检索

    Returns:
        (rag_context_text, references_list)
    """
    if not RAG_AVAILABLE or _rag_service is None:
        return None, []

    try:
        results = _rag_service.search(query, top_k=top_k)

        if not results:
            return None, []

        # 构建上下文文本
        context_parts = []
        references = []

        for i, r in enumerate(results, 1):
            source_tag = "FAO56" if r.is_fao56 else r.source
            context_parts.append(f"[{i}] ({source_tag}, P{r.page}): {r.snippet}")
            references.append({
                "doc_id": r.doc_id,
                "source": source_tag,
                "page": r.page,
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
4. 如果不确定，请诚实说明"""

    # 添加周摘要上下文 (L1)
    if weekly_context:
        base_prompt += f"\n\n<recent_experience>\n{weekly_context}\n</recent_experience>"

    # 添加 RAG 检索结果 (L4)
    if rag_context:
        base_prompt += f"\n\n<knowledge_base>\n以下是与用户问题相关的知识库内容，请参考回答：\n{rag_context}\n</knowledge_base>"

    return base_prompt


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
        # 1. RAG 检索
        rag_context = None
        references = []
        if request.use_rag and RAG_AVAILABLE:
            rag_context, references = _search_rag(request.message)

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
        client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])

        messages = [{"role": "system", "content": enhanced_system}]
        messages.extend(history)
        messages.append({"role": "user", "content": request.message})

        response = await client.chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        answer = response.choices[0].message.content or ""

        # 6. 保存到历史
        _conversation_history.append({"role": "user", "content": request.message})
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
                "rag_used": rag_context is not None,
                "weekly_context_used": weekly_context is not None
            }
        )

    except Exception as e:
        return ChatResponse(
            success=False,
            error=str(e)
        )


@router.get("/stream")
async def chat_stream(
    query: str = Query(..., description="用户问题"),
    use_history: bool = Query(True, description="是否使用对话历史"),
    use_rag: bool = Query(True, description="是否使用 RAG 检索")
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
            # 1. RAG 检索
            rag_context = None
            references = []
            if use_rag and RAG_AVAILABLE:
                rag_context, references = _search_rag(query)

                # 先发送 RAG 检索结果
                if references:
                    yield {
                        "event": "rag",
                        "data": json.dumps({
                            "references": references,
                            "count": len(references)
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
            client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])

            messages = [{"role": "system", "content": enhanced_system}]
            messages.extend(history)
            messages.append({"role": "user", "content": query})

            full_response = ""
            response = await client.chat.completions.create(
                model="gpt-5.2-chat-latest",
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    yield {
                        "event": "content",
                        "data": json.dumps({"text": text}, ensure_ascii=False)
                    }

            # 6. 保存到历史
            _conversation_history.append({"role": "user", "content": query})
            _conversation_history.append({"role": "assistant", "content": full_response})

            # 限制历史长度
            if len(_conversation_history) > 40:
                _conversation_history[:] = _conversation_history[-40:]

            yield {
                "event": "done",
                "data": json.dumps({
                    "rag_used": rag_context is not None,
                    "weekly_context_used": weekly_context is not None
                }, ensure_ascii=False)
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}, ensure_ascii=False)
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
    return {
        "success": True,
        "data": {
            "rag_available": RAG_AVAILABLE,
            "chunk_count": _rag_service.store.chunk_count if RAG_AVAILABLE and _rag_service else 0,
            "weekly_context_available": get_weekly_context() is not None
        }
    }
