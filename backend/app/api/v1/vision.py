from __future__ import annotations
# Vision API - YOLO 视觉分析接口
"""
视觉分析 API
- 图像上传与分割
- 指标提取
- 可视化结果获取
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from datetime import datetime
import io

from app.services.yolo_service import yolo_service

router = APIRouter(prefix="/vision", tags=["vision"])


@router.get("/status")
async def get_status():
    """获取 YOLO 服务状态"""
    return {
        "success": True,
        "data": {
            "model_loaded": yolo_service.is_available,
            "model_type": "YOLO11-seg",
            "tile_inference": True,
            "classes": ["leaf", "terminal", "flower", "fruit"]
        }
    }


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    conf_threshold: float = Query(0.25, ge=0.1, le=0.9)
):
    """
    分析上传的图像

    Args:
        file: 上传的图像文件
        conf_threshold: 置信度阈值 (0.1-0.9)

    Returns:
        分割指标和可视化结果
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    # 读取图像
    contents = await file.read()

    if len(contents) > 20 * 1024 * 1024:  # 20MB 限制
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    try:
        # 获取文件名
        filename = file.filename.rsplit(".", 1)[0] if file.filename else "uploaded"
        filename = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 处理图像
        metrics, vis_bytes = yolo_service.process_bytes(
            contents,
            filename=filename,
            conf_threshold=conf_threshold
        )

        # 生成可视化图像的 base64
        import base64
        vis_base64 = base64.b64encode(vis_bytes).decode('utf-8') if vis_bytes else None

        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "visualization": vis_base64,
                "filename": filename
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/date/{date_str}")
async def analyze_by_date(
    date_str: str,
    use_cache: bool = Query(True)
):
    """
    按日期分析图像

    Args:
        date_str: 日期字符串 (格式: YYYY-MM-DD 或 MMDD)
        use_cache: 是否使用缓存结果

    Returns:
        分割指标
    """
    try:
        # 尝试使用缓存
        if use_cache:
            cached = yolo_service.get_cached_metrics(date_str)
            if cached:
                return {
                    "success": True,
                    "data": {
                        "metrics": cached,
                        "from_cache": True
                    }
                }

        # 处理新图像
        metrics = yolo_service.process_date(date_str)

        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "from_cache": False
            }
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/image/{date_str}")
async def get_segmented_image(
    date_str: str,
    original: bool = Query(False)
):
    """
    获取分割后的图像

    Args:
        date_str: 日期字符串
        original: 是否获取原始图像

    Returns:
        图像 (JPEG)
    """
    from pathlib import Path

    try:
        if original:
            # 返回原始图像
            if "-" in date_str:
                parts = date_str.split("-")
                short_date = f"{parts[1]}{parts[2]}"
            else:
                short_date = date_str

            from app.services.yolo_service import IMAGES_DIR
            for ext in [".JPG", ".jpg", ".jpeg", ".png"]:
                image_path = IMAGES_DIR / f"{short_date}{ext}"
                if image_path.exists():
                    break
            else:
                raise HTTPException(status_code=404, detail="Original image not found")
        else:
            # 返回分割后图像
            image_path = yolo_service.get_segmented_image_path(date_str)
            if not image_path:
                # 尝试先处理
                yolo_service.process_date(date_str)
                image_path = yolo_service.get_segmented_image_path(date_str)

            if not image_path:
                raise HTTPException(status_code=404, detail="Segmented image not found")

        # 读取并返回图像
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename={Path(image_path).name}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{date_str}")
async def get_metrics(date_str: str):
    """
    获取指定日期的指标

    Args:
        date_str: 日期字符串

    Returns:
        分割指标
    """
    try:
        # 尝试获取缓存
        cached = yolo_service.get_cached_metrics(date_str)

        if cached:
            return {
                "success": True,
                "data": cached
            }

        # 处理并返回
        metrics = yolo_service.process_date(date_str)
        return {
            "success": True,
            "data": metrics
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_dates(
    date1: str = Query(...),
    date2: str = Query(...)
):
    """
    对比两个日期的指标

    Args:
        date1: 第一个日期
        date2: 第二个日期

    Returns:
        对比结果
    """
    try:
        # 获取两个日期的指标
        metrics1 = yolo_service.get_cached_metrics(date1)
        metrics2 = yolo_service.get_cached_metrics(date2)

        if not metrics1:
            metrics1 = yolo_service.process_date(date1)
        if not metrics2:
            metrics2 = yolo_service.process_date(date2)

        # 计算变化
        changes = {}
        compare_keys = [
            "leaf_instance_count",
            "flower_instance_count",
            "terminal_instance_count",
            "fruit_instance_count",
            "leaf_average_mask",
            "all_leaf_mask"
        ]

        for key in compare_keys:
            if key in metrics1 and key in metrics2:
                v1 = metrics1[key]
                v2 = metrics2[key]
                changes[key] = {
                    "date1_value": v1,
                    "date2_value": v2,
                    "change": v2 - v1,
                    "change_percent": ((v2 - v1) / v1 * 100) if v1 != 0 else 0
                }

        return {
            "success": True,
            "data": {
                "date1": date1,
                "date2": date2,
                "metrics1": metrics1,
                "metrics2": metrics2,
                "changes": changes
            }
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-dates")
async def get_available_dates():
    """获取所有可用的图像日期"""
    from app.services.yolo_service import IMAGES_DIR, METRICS_DIR

    try:
        # 获取所有图像文件
        image_dates = set()
        for ext in ["*.jpg", "*.JPG", "*.jpeg", "*.png"]:
            for f in IMAGES_DIR.glob(ext):
                image_dates.add(f.stem)

        # 获取所有已处理的指标
        processed_dates = set()
        for f in METRICS_DIR.glob("*_metrics.json"):
            processed_dates.add(f.stem.replace("_metrics", ""))

        return {
            "success": True,
            "data": {
                "available": sorted(list(image_dates)),
                "processed": sorted(list(processed_dates)),
                "total_images": len(image_dates),
                "total_processed": len(processed_dates)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
