from __future__ import annotations
# Override API Router

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.services.episode_service import get_episode_by_date

router = APIRouter()


class OverrideRequest(BaseModel):
    date: str
    original_value: float
    replaced_value: float
    reason: str
    confirmation_answers: Optional[dict] = None


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("")
async def submit_override(data: OverrideRequest):
    """提交 Override"""
    # 验证日期存在
    episode = get_episode_by_date(data.date)
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode not found for date: {data.date}")

    # 验证替代值范围
    if data.replaced_value < 0.1 or data.replaced_value > 20:
        raise HTTPException(status_code=400, detail="Replaced value must be between 0.1 and 20 L/m²")

    # 验证理由长度
    if len(data.reason) < 10:
        raise HTTPException(status_code=400, detail="Reason must be at least 10 characters")

    # 更新 Episode (实际应保存到文件或数据库)
    episode["irrigation_amount"] = data.replaced_value
    episode["decision_source"] = "Override"
    episode["override_reason"] = data.reason
    episode["override_by"] = "user"
    episode["override_at"] = datetime.now().isoformat()

    # 实际项目中应该将 override 保存到文件
    # save_override(data.date, episode)

    return create_response(episode)
