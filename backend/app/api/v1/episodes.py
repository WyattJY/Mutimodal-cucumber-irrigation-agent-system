from __future__ import annotations
# Episodes API Router

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.services.episode_service import (
    get_latest_episode,
    get_episode_by_date,
    get_episodes,
    get_all_dates,
)

router = APIRouter()


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/latest")
async def get_latest():
    """获取最新 Episode"""
    episode = get_latest_episode()
    if not episode:
        raise HTTPException(status_code=404, detail="No episodes found")
    return create_response(episode)


@router.get("/dates")
async def get_date_list():
    """获取所有可用日期列表"""
    dates = get_all_dates()
    return create_response(dates)


@router.get("/{date}")
async def get_by_date(date: str):
    """根据日期获取 Episode"""
    episode = get_episode_by_date(date)
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode not found for date: {date}")
    return create_response(episode)


@router.get("")
async def query_episodes(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    trend: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """查询 Episode 列表"""
    episodes, total = get_episodes(
        start_date=start_date,
        end_date=end_date,
        trend=trend,
        page=page,
        page_size=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return create_response({
        "items": episodes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })
