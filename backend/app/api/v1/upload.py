from __future__ import annotations
# Upload API Router
"""
数据上传 API
- 环境数据上传 (CSV)
- 图像上传
- YOLO 处理触发
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
import json

router = APIRouter()

# 项目路径 (cucumber-irrigation/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
CSV_DIR = DATA_DIR / "csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
SEGMENTED_DIR = OUTPUT_DIR / "segmented_images"
METRICS_DIR = OUTPUT_DIR / "yolo_metrics"

# 确保目录存在
for d in [IMAGES_DIR, CSV_DIR, SEGMENTED_DIR, METRICS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Debug: 打印路径
print(f"[Upload] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[Upload] IMAGES_DIR: {IMAGES_DIR}")
print(f"[Upload] IMAGES_DIR exists: {IMAGES_DIR.exists()}")


def create_response(data, success=True, error=None):
    """创建统一响应格式"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    date: str = Form(...),
    process_yolo: bool = Form(True)
):
    """
    上传图像并可选择进行 YOLO 处理

    Args:
        file: 图像文件
        date: 日期 (格式: 2024-06-14 或 0614)
        process_yolo: 是否立即进行 YOLO 分割处理
    """
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
        )

    # 解析日期
    if "-" in date:
        parts = date.split("-")
        short_date = f"{parts[1]}{parts[2]}"
    else:
        short_date = date

    # 确定扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        ext = ".jpg"

    # 保存文件
    save_path = IMAGES_DIR / f"{short_date}{ext}"

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    result = {
        "filename": save_path.name,
        "path": str(save_path),
        "date": date,
        "size": os.path.getsize(save_path)
    }

    # YOLO 处理
    if process_yolo:
        try:
            from app.services.yolo_service import yolo_service
            metrics = yolo_service.process_image(str(save_path))
            result["yolo_metrics"] = metrics
            result["segmented_image"] = metrics.get("visualization_path")
        except Exception as e:
            result["yolo_error"] = str(e)
            result["yolo_metrics"] = None

    return create_response(result)


@router.post("/env")
async def upload_env_data(file: UploadFile = File(...)):
    """
    上传环境数据 CSV

    CSV 格式要求:
    date,temperature,humidity,light,solar_radiation,...
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    save_path = CSV_DIR / "env_uploaded.csv"

    try:
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # 解析 CSV 统计
        import csv
        lines = content.decode("utf-8").strip().split("\n")
        reader = csv.DictReader(lines)
        rows = list(reader)

        # 验证必要列
        required_cols = ["date", "temperature", "humidity"]
        missing = [c for c in required_cols if c not in reader.fieldnames]

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing}"
            )

        return create_response({
            "filename": file.filename,
            "rows": len(rows),
            "columns": reader.fieldnames,
            "date_range": {
                "start": rows[0]["date"] if rows else None,
                "end": rows[-1]["date"] if rows else None
            },
            "saved_to": str(save_path)
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {e}")


@router.post("/irrigation")
async def upload_irrigation_data(file: UploadFile = File(...)):
    """上传灌水数据 CSV"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    save_path = CSV_DIR / "irrigation_uploaded.csv"

    try:
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        return create_response({
            "filename": file.filename,
            "saved_to": str(save_path)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")


@router.get("/images")
async def list_images():
    """列出所有已上传的图像"""
    images = []

    for ext in ["*.jpg", "*.JPG", "*.jpeg", "*.png"]:
        for f in IMAGES_DIR.glob(ext):
            # 检查是否有对应的分割结果
            seg_path = SEGMENTED_DIR / f"{f.stem}_segmented.jpg"
            metrics_path = METRICS_DIR / f"{f.stem}_metrics.json"

            images.append({
                "filename": f.name,
                "date": f.stem,
                "size": f.stat().st_size,
                "has_segmentation": seg_path.exists(),
                "has_metrics": metrics_path.exists()
            })

    # 按日期排序
    images.sort(key=lambda x: x["date"])

    return create_response({
        "images": images,
        "total": len(images)
    })


@router.get("/images/{date}/original")
async def get_original_image(date: str):
    """获取原始图像"""
    if "-" in date:
        parts = date.split("-")
        short_date = f"{parts[1]}{parts[2]}"
    else:
        short_date = date

    for ext in [".jpg", ".JPG", ".jpeg", ".png"]:
        path = IMAGES_DIR / f"{short_date}{ext}"
        if path.exists():
            return FileResponse(
                path,
                media_type="image/jpeg",
                filename=path.name
            )

    raise HTTPException(status_code=404, detail=f"Image not found for date: {date}")


@router.get("/images/{date}/segmented")
async def get_segmented_image(date: str):
    """获取分割后的图像"""
    if "-" in date:
        parts = date.split("-")
        short_date = f"{parts[1]}{parts[2]}"
    else:
        short_date = date

    seg_path = SEGMENTED_DIR / f"{short_date}_segmented.jpg"

    if seg_path.exists():
        return FileResponse(
            seg_path,
            media_type="image/jpeg",
            filename=seg_path.name
        )

    raise HTTPException(
        status_code=404,
        detail=f"Segmented image not found for date: {date}. Run YOLO processing first."
    )


@router.get("/images/{date}/metrics")
async def get_image_metrics(date: str):
    """获取图像的 YOLO 分析指标"""
    if "-" in date:
        parts = date.split("-")
        short_date = f"{parts[1]}{parts[2]}"
    else:
        short_date = date

    metrics_path = METRICS_DIR / f"{short_date}_metrics.json"

    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        return create_response(metrics)

    raise HTTPException(
        status_code=404,
        detail=f"Metrics not found for date: {date}. Run YOLO processing first."
    )


@router.post("/process/{date}")
async def process_image_yolo(date: str):
    """手动触发 YOLO 处理"""
    if "-" in date:
        parts = date.split("-")
        short_date = f"{parts[1]}{parts[2]}"
    else:
        short_date = date

    # 查找图像
    image_path = None
    for ext in [".jpg", ".JPG", ".jpeg", ".png"]:
        path = IMAGES_DIR / f"{short_date}{ext}"
        if path.exists():
            image_path = path
            break

    if not image_path:
        raise HTTPException(status_code=404, detail=f"Image not found for date: {date}")

    try:
        from app.services.yolo_service import yolo_service
        metrics = yolo_service.process_image(str(image_path))
        return create_response(metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YOLO processing failed: {e}")


@router.post("/batch-process")
async def batch_process_yolo():
    """批量处理所有图像"""
    try:
        from app.services.yolo_service import yolo_service
        results = yolo_service.batch_process()

        success_count = sum(1 for r in results if r["success"])

        return create_response({
            "processed": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "results": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {e}")
