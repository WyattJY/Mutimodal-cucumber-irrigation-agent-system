from __future__ import annotations
# Stats API Router

from fastapi import APIRouter, Query
from datetime import datetime

from app.services.episode_service import get_growth_stats, get_trend_data

router = APIRouter()


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/growth")
async def growth_stats():
    """获取生长统计数据"""
    stats = get_growth_stats()
    if not stats:
        return create_response({
            "created_at": datetime.now().isoformat(),
            "all_leaf_mask": {
                "start_value": 0,
                "end_value": 0,
                "total_growth": 0,
                "daily_avg": 0,
                "daily_std": 0,
                "growth_rate_percent": 0,
            },
            "date_range": {
                "start": "",
                "end": "",
                "total_days": 0,
            },
            "thresholds": {
                "better": 0,
                "worse": 0,
                "description": "",
            },
        })
    return create_response(stats)


@router.get("/trend")
async def trend_data(days: int = Query(30, ge=7, le=90)):
    """获取趋势数据 (用于图表)"""
    data = get_trend_data(days)
    return create_response(data)
