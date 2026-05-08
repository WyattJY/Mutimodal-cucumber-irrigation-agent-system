"""
LLM PlantResponse generation node.

Wraps: llm_service.generate_plant_response
"""
from __future__ import annotations

from loguru import logger

from app.services.llm_service import llm_service
from app.observability.decorators import traced_node


@traced_node("plant_response")
async def run(state: dict) -> dict:
    """Generate PlantResponse via LLM Vision model."""
    image_today_b64 = state.get("image_today_b64")
    image_yesterday_b64 = state.get("image_yesterday_b64")
    yolo_today = state.get("yolo_today", {})
    yolo_yesterday = state.get("yolo_yesterday")
    env_data = state.get("env_data", {})
    is_cold_start = state.get("is_cold_start", False)
    skip = state.get("options", {}).get("skip_llm", False)

    if skip:
        logger.info("[plant_response] 跳过 LLM PlantResponse")
        return {
            "plant_response": None,
            "node_trace": [{"node": "plant_response", "status": "skipped"}],
        }

    if not image_today_b64:
        logger.warning("[plant_response] 无今日图片，跳过")
        return {
            "plant_response": None,
            "warnings": ["无法生成 PlantResponse：缺少今日图片"],
            "node_trace": [{"node": "plant_response", "status": "skipped", "detail": "no_image"}],
        }

    try:
        result = await llm_service.generate_plant_response(
            image_today_b64=image_today_b64,
            image_yesterday_b64=image_yesterday_b64,
            yolo_today=yolo_today,
            yolo_yesterday=yolo_yesterday,
            env_data=env_data,
            is_cold_start=is_cold_start,
        )

        response_dict = result.model_dump() if result else None
        trend = response_dict.get("trend") if response_dict else None

        logger.info(f"[plant_response] 完成: trend={trend}")
        return {
            "plant_response": response_dict,
            "node_trace": [{"node": "plant_response", "status": "ok", "trend": trend}],
        }

    except Exception as e:
        logger.error(f"[plant_response] 失败: {e}")
        return {
            "plant_response": None,
            "error": f"PlantResponse failed: {e}",
            "warnings": [f"PlantResponse 生成失败: {e}"],
            "node_trace": [{"node": "plant_response", "status": "error", "detail": str(e)}],
        }
