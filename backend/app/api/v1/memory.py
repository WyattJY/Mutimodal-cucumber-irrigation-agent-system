from __future__ import annotations
# Memory API Router
"""
记忆系统 API

功能:
1. GET /status - 获取记忆系统状态
2. GET /weekly - 获取最新周摘要
3. GET /context - 获取完整的 Working Context
4. GET /episodes - 获取记忆中的 Episodes
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from pathlib import Path
import json

from app.services.episode_service import (
    get_weekly_context,
    _load_memory_episodes,
    _load_weekly_summary,
)
from app.services.memory_service import memory_service

router = APIRouter()

# 项目路径 (memory.py 在 backend/app/api/v1/ 中，需要向上 5 级到项目根目录)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MEMORY_EPISODES_FILE = DATA_DIR / "storage" / "episodes.json"
MEMORY_WEEKLY_FILE = DATA_DIR / "storage" / "weekly_summaries.json"


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/status")
async def get_memory_status():
    """
    获取记忆系统状态

    返回:
    - L1: Working Context 状态
    - L2: Episode Store 状态
    - L3: Weekly Summary 状态
    - L4: RAG 状态
    """
    # L2: Episode Store
    episodes = _load_memory_episodes()
    episode_count = len(episodes)
    episode_dates = [ep.get('date') for ep in episodes] if episodes else []

    # L3: Weekly Summary
    weekly = _load_weekly_summary()
    has_weekly = weekly is not None
    weekly_range = None
    if weekly:
        weekly_range = f"{weekly.get('week_start', '?')} ~ {weekly.get('week_end', '?')}"

    # L1: Working Context
    weekly_context = get_weekly_context()
    has_working_context = weekly_context is not None

    return create_response({
        "memory_layers": {
            "L1_working_context": {
                "enabled": has_working_context,
                "has_weekly_summary": has_weekly,
                "description": "自动注入周摘要到 LLM 调用"
            },
            "L2_episode_store": {
                "enabled": True,
                "count": episode_count,
                "dates": episode_dates[-5:] if episode_dates else [],
                "file_exists": MEMORY_EPISODES_FILE.exists()
            },
            "L3_weekly_summary": {
                "enabled": has_weekly,
                "current_week": weekly_range,
                "file_exists": MEMORY_WEEKLY_FILE.exists()
            },
            "L4_rag": {
                "enabled": True,
                "description": "见 /api/knowledge/status"
            }
        },
        "overall_status": "active" if (episode_count > 0 or has_weekly) else "empty"
    })


@router.get("/weekly")
async def get_weekly_summary():
    """获取最新的周摘要"""
    weekly = _load_weekly_summary()

    if not weekly:
        return create_response(None, success=False, error="无可用的周摘要")

    return create_response({
        "week_start": weekly.get("week_start"),
        "week_end": weekly.get("week_end"),
        "trend_stats": weekly.get("trend_stats"),
        "irrigation_stats": weekly.get("irrigation_stats"),
        "key_insights": weekly.get("key_insights"),
        "prompt_block": weekly.get("prompt_block"),
        "prompt_block_tokens": weekly.get("prompt_block_tokens"),
    })


@router.get("/context")
async def get_working_context():
    """
    获取完整的 Working Context (L1)

    这是注入到 LLM 调用中的上下文
    """
    weekly_context = get_weekly_context()
    weekly = _load_weekly_summary()

    # 构建完整的 Working Context
    context_parts = []

    if weekly_context:
        context_parts.append(f"<recent_experience>\n{weekly_context}\n</recent_experience>")

    # 可以在这里添加更多上下文，如 RAG 结果等

    full_context = "\n\n".join(context_parts) if context_parts else None

    return create_response({
        "has_context": full_context is not None,
        "weekly_summary_included": weekly_context is not None,
        "full_context": full_context,
        "context_sources": {
            "weekly_summary": weekly is not None,
            "rag_results": False,  # 需要在预测时动态添加
        }
    })


@router.get("/episodes")
async def get_memory_episodes(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """获取记忆中的 Episodes"""
    episodes = _load_memory_episodes()

    # 按日期排序
    sorted_eps = sorted(episodes, key=lambda x: x.get('date', ''), reverse=True)

    # 分页
    paginated = sorted_eps[offset:offset + limit]

    # 简化返回数据
    simplified = []
    for ep in paginated:
        simplified.append({
            "date": ep.get("date"),
            "growth_stage": ep.get("predictions", {}).get("growth_stage"),
            "trend": ep.get("predictions", {}).get("plant_response", {}).get("trend"),
            "irrigation": ep.get("final_decision", {}).get("value"),
            "source": ep.get("final_decision", {}).get("source"),
        })

    return create_response({
        "episodes": simplified,
        "total": len(episodes),
        "limit": limit,
        "offset": offset
    })


@router.post("/sync")
async def sync_memory():
    """
    同步记忆数据

    将 output/responses/ 中的 PlantResponse 同步到 episodes.json
    """
    from app.services.episode_service import RESPONSES_DIR

    synced = 0
    errors = []

    if not RESPONSES_DIR.exists():
        return create_response({"synced": 0, "errors": ["responses 目录不存在"]})

    existing_episodes = _load_memory_episodes()
    existing_dates = {ep.get('date') for ep in existing_episodes}

    for file in RESPONSES_DIR.glob("*.json"):
        date = file.stem
        if date in existing_dates:
            continue

        try:
            with open(file, 'r', encoding='utf-8') as f:
                response_data = json.load(f)

            # 转换为 Episode 格式
            episode = {
                "date": date,
                "inputs": {
                    "environment": response_data.get("env_today", {}),
                    "yolo_metrics": response_data.get("yolo_today", {}),
                },
                "predictions": {
                    "tsmixer_raw": 5.0,  # 默认值
                    "plant_response": response_data.get("response", {}),
                    "growth_stage": response_data.get("response", {}).get("growth_stage"),
                },
                "final_decision": {
                    "value": 5.0,
                    "source": "tsmixer"
                },
                "created_at": response_data.get("created_at", datetime.now().isoformat()),
            }

            existing_episodes.append(episode)
            synced += 1

        except Exception as e:
            errors.append(f"{date}: {str(e)}")

    # 保存更新后的 episodes
    if synced > 0:
        MEMORY_EPISODES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MEMORY_EPISODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_episodes, f, ensure_ascii=False, indent=2)

    return create_response({
        "synced": synced,
        "total_episodes": len(existing_episodes),
        "errors": errors
    })
