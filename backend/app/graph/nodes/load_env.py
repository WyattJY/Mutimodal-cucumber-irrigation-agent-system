"""
Load environment data and resolve images for the target date.

Wraps: prediction_service._get_or_save_image, _find_yesterday_data, _normalize_date
"""
from __future__ import annotations

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

from app.observability.decorators import traced_node

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
YOLO_METRICS_DIR = PROJECT_ROOT / "output" / "yolo_metrics"


def _normalize_date(date: str) -> str:
    if len(date) == 4 and date.isdigit():
        return f"2024-{date[:2]}-{date[2:]}"
    if len(date) == 8 and date.isdigit():
        return f"{date[:4]}-{date[4:6]}-{date[6:]}"
    return date


def _date_to_filename(date: str) -> str:
    parts = date.split("-")
    if len(parts) == 3:
        return f"{parts[1]}{parts[2]}"
    return date


def _find_image(date: str, image_path=None, image_base64=None):
    """Find or save image for a date, return (path, base64)."""
    if image_base64:
        filename = f"{_date_to_filename(date)}.jpg"
        save_path = IMAGES_DIR / filename
        try:
            image_data = base64.b64decode(image_base64)
            with open(save_path, 'wb') as f:
                f.write(image_data)
            return str(save_path), image_base64
        except Exception as e:
            logger.error(f"保存图片失败: {e}")

    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return image_path, base64.b64encode(image_data).decode('utf-8')

    date_prefix = _date_to_filename(date)
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        potential_path = IMAGES_DIR / f"{date_prefix}{ext}"
        if potential_path.exists():
            with open(potential_path, 'rb') as f:
                image_data = f.read()
            return str(potential_path), base64.b64encode(image_data).decode('utf-8')

    return None, None


def _find_yesterday(date: str):
    """Find yesterday's image and YOLO metrics, return (path, b64, yolo, is_cold_start)."""
    try:
        current_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return None, None, None, True

    for days_back in range(1, 4):
        yesterday = current_date - timedelta(days=days_back)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        image_path, image_b64 = _find_image(yesterday_str)

        if image_path:
            metrics_file = YOLO_METRICS_DIR / f"{_date_to_filename(yesterday_str)}.json"
            yolo_metrics = None
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    yolo_metrics = json.load(f)
            return image_path, image_b64, yolo_metrics, False

    return None, None, None, True


@traced_node("load_env")
def run(state: dict) -> dict:
    """Load env data, resolve today/yesterday images, detect cold start."""
    date = _normalize_date(state["date"])
    logger.info(f"[load_env] 开始加载: {date}")

    image_today_path, image_today_b64 = _find_image(
        date,
        state.get("image_path"),
        state.get("image_base64")
    )

    if not image_today_path:
        return {
            "date": date,
            "is_cold_start": True,
            "error": f"找不到日期 {date} 的图片",
            "warnings": [f"找不到日期 {date} 的图片，进入冷启动模式"],
            "node_trace": [{"node": "load_env", "status": "warn", "detail": "no_image"}],
        }

    image_yesterday_path, image_yesterday_b64, yolo_yesterday, is_cold_start = _find_yesterday(date)

    env_data = state.get("env_data") or {
        "temperature": 25.0,
        "humidity": 70.0,
        "light": 50000.0,
        "date": date,
    }

    warnings = []
    if is_cold_start:
        warnings = ["冷启动模式：没有历史数据进行对比分析"]

    return {
        "date": date,
        "image_today_path": image_today_path,
        "image_today_b64": image_today_b64,
        "image_yesterday_path": image_yesterday_path,
        "image_yesterday_b64": image_yesterday_b64,
        "yolo_yesterday": yolo_yesterday,
        "is_cold_start": is_cold_start,
        "env_data": env_data,
        "warnings": warnings,
        "node_trace": [{"node": "load_env", "status": "ok", "cold_start": is_cold_start}],
    }
