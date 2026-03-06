from __future__ import annotations
# Settings API - 配置管理接口
"""
配置管理 API

端点:
- GET /settings - 获取当前配置
- PUT /settings - 更新用户配置
- POST /settings/test - 测试 API 连接
- DELETE /settings - 重置为默认配置
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings, user_config, get_active_openai_config
from app.services.llm_service import llm_service


router = APIRouter(prefix="/settings", tags=["settings"])


class LLMConfigUpdate(BaseModel):
    """LLM 配置更新请求"""
    use_custom_config: bool = False
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None


class SettingsResponse(BaseModel):
    """配置响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """
    获取当前配置

    Response:
    - use_custom_config: 是否使用自定义配置
    - has_custom_key: 是否已设置自定义 API Key
    - active_model: 当前激活的模型
    - active_base_url: 当前激活的 Base URL
    - default_model: 默认模型
    """
    active_config = get_active_openai_config()

    return SettingsResponse(
        success=True,
        data={
            "use_custom_config": user_config.use_custom_config,
            "has_custom_key": bool(user_config.openai_api_key),
            "custom_base_url": user_config.openai_base_url,
            "custom_model": user_config.openai_model,
            "active_model": active_config["model"],
            "active_base_url": active_config["base_url"],
            "default_model": settings.default_openai_model,
            "default_base_url": settings.default_openai_base_url,
        }
    )


@router.put("/", response_model=SettingsResponse)
async def update_settings(config: LLMConfigUpdate):
    """
    更新用户配置

    Request Body:
    - use_custom_config: 是否使用自定义配置
    - openai_api_key: 自定义 API Key (可选)
    - openai_base_url: 自定义 Base URL (可选)
    - openai_model: 自定义模型 (可选)
    """
    try:
        user_config.update(
            use_custom_config=config.use_custom_config,
            openai_api_key=config.openai_api_key,
            openai_base_url=config.openai_base_url,
            openai_model=config.openai_model,
        )

        return SettingsResponse(
            success=True,
            data={
                "message": "配置已更新",
                "active_config": get_active_openai_config()
            }
        )
    except Exception as e:
        return SettingsResponse(
            success=False,
            error=str(e)
        )


@router.post("/test", response_model=SettingsResponse)
async def test_llm_connection():
    """
    测试 LLM API 连接

    使用当前激活的配置测试连接
    """
    result = await llm_service.test_connection()

    return SettingsResponse(
        success=result["success"],
        data=result
    )


@router.delete("/", response_model=SettingsResponse)
async def reset_settings():
    """
    重置为默认配置

    清除所有用户自定义配置
    """
    user_config.clear()

    return SettingsResponse(
        success=True,
        data={
            "message": "配置已重置为默认值",
            "active_config": get_active_openai_config()
        }
    )
