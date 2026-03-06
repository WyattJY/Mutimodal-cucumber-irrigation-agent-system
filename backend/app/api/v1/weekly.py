from __future__ import annotations
# Weekly API Router
"""
周报 API

功能:
1. GET / - 获取所有周报列表
2. GET /latest - 获取最新周报
3. GET /{week_start} - 获取指定周报
4. POST /generate - 生成周报
5. GET /prompt-block - 获取最新的 prompt_block
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.services.weekly_summary_service import weekly_summary_service
from app.services.memory_service import memory_service
from app.models.schemas import WeeklyGenerateRequest, WeeklySummaryResult

router = APIRouter()


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


# 模拟周报数据 (实际应从文件或数据库读取)
MOCK_WEEKLY_SUMMARIES = [
    {
        "id": "week-2024-06-10",
        "week_start": "2024-06-10",
        "week_end": "2024-06-16",
        "created_at": "2024-06-17T08:00:00",
        "insights": [
            "本周平均灌水量 4.8 L/m²，较上周增加 5%",
            "连续 3 天检测到高温胁迫，建议加强通风",
            "果实膨大期进展顺利，建议保持当前灌溉策略",
        ],
        "stats": {
            "total_irrigation": 33.6,
            "avg_irrigation": 4.8,
            "trend_distribution": {"better": 3, "same": 3, "worse": 1},
            "override_count": 1,
            "risk_distribution": {"low": 4, "medium": 2, "high": 1, "critical": 0},
        },
        "rag_references": [
            {
                "id": "ref-1",
                "source": "FAO56",
                "chapter": "Chapter 7",
                "page": 123,
                "content": "在果实膨大期，作物系数 Kc 应适当提高...",
                "relevance_score": 0.92,
            }
        ],
        "injected_prompt": "本周注意：连续高温可能导致叶片蒸腾加剧，建议密切监测土壤含水量。",
    }
]


@router.get("")
async def get_all():
    """获取所有周报列表"""
    return create_response({
        "items": MOCK_WEEKLY_SUMMARIES,
        "total": len(MOCK_WEEKLY_SUMMARIES),
    })


@router.get("/latest")
async def get_latest():
    """获取最新周报"""
    if not MOCK_WEEKLY_SUMMARIES:
        raise HTTPException(status_code=404, detail="No weekly summaries found")
    return create_response(MOCK_WEEKLY_SUMMARIES[0])


@router.get("/{week_start}")
async def get_by_week_start(week_start: str):
    """根据周起始日期获取周报"""
    for summary in MOCK_WEEKLY_SUMMARIES:
        if summary["week_start"] == week_start:
            return create_response(summary)
    raise HTTPException(status_code=404, detail=f"Weekly summary not found for week: {week_start}")


# ============================================================================
# 新增端点
# ============================================================================

@router.post("/generate", response_model=WeeklySummaryResult)
async def generate_weekly_summary(request: WeeklyGenerateRequest):
    """
    生成周报

    基于指定周内的 Episode 记录生成周摘要，包括：
    - 灌溉统计 (日均、最大、最小、Override 比例)
    - 长势趋势分布 (好转/平稳/下降天数)
    - 发现的规律
    - 风险触发条件
    - 关键洞察
    - 用于注入 System Prompt 的 prompt_block

    Args:
        request: WeeklyGenerateRequest (week_start, week_end)

    Returns:
        WeeklySummaryResult: 完整的周摘要
    """
    try:
        result = await weekly_summary_service.generate_weekly_summary(
            week_start=request.week_start,
            week_end=request.week_end
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成周报失败: {str(e)}")


@router.get("/prompt-block/latest")
async def get_latest_prompt_block():
    """
    获取最新的 prompt_block

    返回最新周摘要中的 prompt_block，用于注入 System Prompt

    Returns:
        prompt_block 字符串
    """
    try:
        prompt_block = await memory_service.get_weekly_prompt_block()

        if prompt_block:
            return create_response({
                "prompt_block": prompt_block
            })
        else:
            return create_response({
                "prompt_block": None,
                "message": "暂无周摘要数据"
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
