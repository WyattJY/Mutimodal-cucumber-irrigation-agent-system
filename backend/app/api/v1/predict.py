from __future__ import annotations
# Predict API - 灌水量预测接口
"""
预测 API

功能:
1. POST /daily - 完整的每日预测流程 (YOLO + TSMixer + LLM)
2. POST / - 简单预测 (使用已有的 YOLO 指标)
3. POST /with-image - 上传图像并预测
4. GET /response/{date} - 获取指定日期的 PlantResponse
5. GET /episode/{date} - 获取指定日期的 Episode
6. GET /responses - 列出 PlantResponse 文件
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import json

from app.services.yolo_service import yolo_service
from app.services.tsmixer_service import tsmixer_service
from app.services.prediction_service import prediction_service
from app.services.memory_service import memory_service
from app.models.schemas import (
    DailyPredictRequest, DailyPredictResult, PredictOptions
)

router = APIRouter(prefix="/predict", tags=["predict"])


class EnvData(BaseModel):
    """环境数据"""
    temperature: float = 25.0  # 日均温度 (°C)
    humidity: float = 70.0     # 日均湿度 (%)
    light: float = 50000.0     # 日均光照 (lux)
    date: Optional[str] = None # 预测日期 (YYYY-MM-DD)


class PredictRequest(BaseModel):
    """预测请求"""
    env_data: EnvData
    yolo_metrics: Optional[dict] = None  # 可选的 YOLO 指标 (如果已经提取过)


@router.get("/status")
async def get_status():
    """获取预测服务状态"""
    return {
        "success": True,
        "data": {
            "yolo_available": yolo_service.is_available,
            "tsmixer_available": tsmixer_service.is_available,
            "feature_count": 11,
            "sequence_length": 96
        }
    }


@router.post("/")
async def predict(request: PredictRequest):
    """
    执行灌水量预测 (使用已有的 YOLO 指标)

    Args:
        request: 预测请求

    Returns:
        预测结果
    """
    try:
        env_data = request.env_data.model_dump()
        yolo_metrics = request.yolo_metrics or {}

        # 如果没有 YOLO 指标，使用默认值
        if not yolo_metrics:
            yolo_metrics = {
                "leaf_instance_count": 10,
                "leaf_average_mask": 1000.0,
                "flower_instance_count": 5,
                "flower_mask_pixel_count": 500,
                "terminal_average_mask": 300.0,
                "fruit_mask_average": 400.0,
                "all_leaf_mask": 10000
            }

        # 构建特征
        features = tsmixer_service.build_features(
            env_data=env_data,
            yolo_metrics=yolo_metrics,
            target_date=env_data.get('date')
        )

        # 预测
        result = tsmixer_service.predict(features, return_confidence=True)

        return {
            "success": True,
            "data": {
                "prediction": result,
                "input_summary": {
                    "temperature": env_data.get('temperature'),
                    "humidity": env_data.get('humidity'),
                    "light": env_data.get('light'),
                    "date": env_data.get('date') or datetime.now().strftime('%Y-%m-%d'),
                    "leaf_count": yolo_metrics.get('leaf_instance_count'),
                    "flower_count": yolo_metrics.get('flower_instance_count')
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/with-image")
async def predict_with_image(
    file: UploadFile = File(...),
    temperature: float = Form(25.0),
    humidity: float = Form(70.0),
    light: float = Form(50000.0),
    date: Optional[str] = Form(None)
):
    """
    上传图像并执行灌水量预测

    1. 使用 YOLO 分析图像提取视觉指标
    2. 结合环境数据构建特征
    3. 使用 TSMixer 预测灌水量

    Args:
        file: 植物图像
        temperature: 日均温度 (°C)
        humidity: 日均湿度 (%)
        light: 日均光照 (lux)
        date: 预测日期

    Returns:
        预测结果
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    try:
        # 读取图像
        contents = await file.read()

        if len(contents) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 20MB)")

        # 获取文件名
        filename = file.filename.rsplit(".", 1)[0] if file.filename else "uploaded"
        filename = f"predict_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # YOLO 分析
        yolo_metrics, vis_bytes = yolo_service.process_bytes(
            contents,
            filename=filename
        )

        # 构建环境数据
        env_data = {
            "temperature": temperature,
            "humidity": humidity,
            "light": light,
            "date": date or datetime.now().strftime('%Y-%m-%d')
        }

        # 构建特征
        features = tsmixer_service.build_features(
            env_data=env_data,
            yolo_metrics=yolo_metrics,
            target_date=env_data['date']
        )

        # 预测
        prediction = tsmixer_service.predict(features, return_confidence=True)

        # 生成可视化图像的 base64
        import base64
        vis_base64 = base64.b64encode(vis_bytes).decode('utf-8') if vis_bytes else None

        return {
            "success": True,
            "data": {
                "prediction": prediction,
                "yolo_metrics": yolo_metrics,
                "visualization": vis_base64,
                "input_summary": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "light": light,
                    "date": env_data['date'],
                    "leaf_count": yolo_metrics.get('leaf_instance_count'),
                    "flower_count": yolo_metrics.get('flower_instance_count'),
                    "fruit_count": yolo_metrics.get('fruit_instance_count')
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/feature-importance")
async def get_feature_importance():
    """获取特征重要性"""
    return {
        "success": True,
        "data": tsmixer_service.get_feature_importance()
    }


@router.post("/batch")
async def batch_predict(dates: List[str]):
    """
    批量预测多个日期

    Args:
        dates: 日期列表 (格式: YYYY-MM-DD)

    Returns:
        预测结果列表
    """
    results = []

    for date_str in dates:
        try:
            # 尝试获取当天的 YOLO 指标
            yolo_metrics = yolo_service.get_cached_metrics(date_str)

            if not yolo_metrics:
                # 使用默认值
                yolo_metrics = {
                    "leaf_instance_count": 10,
                    "leaf_average_mask": 1000.0,
                    "flower_instance_count": 5,
                    "flower_mask_pixel_count": 500,
                    "terminal_average_mask": 300.0,
                    "fruit_mask_average": 400.0,
                    "all_leaf_mask": 10000
                }

            # 使用默认环境数据
            env_data = {
                "temperature": 25.0,
                "humidity": 70.0,
                "light": 50000.0,
                "date": date_str
            }

            features = tsmixer_service.build_features(
                env_data=env_data,
                yolo_metrics=yolo_metrics,
                target_date=date_str
            )

            prediction = tsmixer_service.predict(features)

            results.append({
                "date": date_str,
                "success": True,
                "prediction": prediction
            })

        except Exception as e:
            results.append({
                "date": date_str,
                "success": False,
                "error": str(e)
            })

    return {
        "success": True,
        "data": results
    }


# ============================================================================
# 新增端点: 完整每日预测流程
# ============================================================================

@router.post("/daily", response_model=DailyPredictResult)
async def predict_daily(request: DailyPredictRequest):
    """
    执行完整的每日预测流程

    流程:
    1. 保存/获取图片
    2. YOLO 推理
    3. 查找昨日图片 (冷启动检测)
    4. TSMixer 预测
    5. 生育期检测
    6. RAG 检索 (可选)
    7. 构建 Working Context
    8. 生成 PlantResponse
    9. SanityCheck (可选)
    10. 创建 Episode
    11. 保存结果

    Args:
        request: DailyPredictRequest

    Returns:
        DailyPredictResult: 完整的预测结果
    """
    try:
        result = await prediction_service.predict_daily(
            date=request.date,
            image_base64=request.image_base64,
            env_data=request.env_data,
            options=request.options
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.get("/response/{date}")
async def get_plant_response(date: str):
    """
    获取指定日期的 PlantResponse

    Args:
        date: 日期 (YYYY-MM-DD 或 MMDD)

    Returns:
        PlantResponse 数据
    """
    try:
        response = await prediction_service.get_plant_response(date)

        if response:
            return {
                "success": True,
                "data": response
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"未找到日期 {date} 的 PlantResponse"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episode/{date}")
async def get_episode(date: str):
    """
    获取指定日期的 Episode

    Args:
        date: 日期 (YYYY-MM-DD)

    Returns:
        Episode 数据
    """
    try:
        episode = await memory_service.get_episode(date)

        if episode:
            episode_data = episode.to_dict() if hasattr(episode, 'to_dict') else episode
            return {
                "success": True,
                "data": episode_data
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"未找到日期 {date} 的 Episode"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/responses")
async def list_plant_responses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    列出 PlantResponse 文件

    Args:
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)

    Returns:
        PlantResponse 文件列表
    """
    try:
        responses = await prediction_service.list_plant_responses(
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "data": responses,
            "total": len(responses)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodes")
async def list_episodes(
    days: int = 7
):
    """
    获取最近的 Episodes

    Args:
        days: 天数 (默认 7)

    Returns:
        Episode 列表
    """
    try:
        episodes = await memory_service.get_recent_episodes(days)

        episodes_data = [
            ep.to_dict() if hasattr(ep, 'to_dict') else ep
            for ep in episodes
        ]

        return {
            "success": True,
            "data": episodes_data,
            "total": len(episodes_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
