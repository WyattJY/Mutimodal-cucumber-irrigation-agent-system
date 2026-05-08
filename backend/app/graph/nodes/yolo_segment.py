"""
YOLO segmentation node — wraps existing yolo_service singleton.
"""
from __future__ import annotations

import json
from pathlib import Path
from loguru import logger

from app.services.yolo_service import yolo_service
from app.models.schemas import YoloMetrics
from app.observability.decorators import traced_node

YOLO_METRICS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "yolo_metrics"


def _date_to_filename(date: str) -> str:
    parts = date.split("-")
    if len(parts) == 3:
        return f"{parts[1]}{parts[2]}"
    return date


def _get_default_yolo_metrics() -> dict:
    return {
        "leaf Instance Count": 8.0,
        "leaf average mask": 5000.0,
        "flower Instance Count": 2.0,
        "flower Mask Pixel Count": 1000.0,
        "terminal average Mask Pixel Count": 500.0,
        "fruit Mask average": 300.0,
        "all leaf mask": 40000.0,
    }


@traced_node("yolo_segment")
def run(state: dict) -> dict:
    """Run YOLO instance segmentation on today's image."""
    date = state["date"]
    image_path = state.get("image_today_path")
    skip = state.get("options", {}).get("skip_yolo", False)

    if skip or not image_path:
        logger.info("[yolo_segment] 跳过 YOLO")
        defaults = _get_default_yolo_metrics()
        return {
            "yolo_today": defaults,
            "yolo_metrics": YoloMetrics.from_raw(defaults).model_dump(),
            "node_trace": [{"node": "yolo_segment", "status": "skipped"}],
        }

    try:
        metrics_file = YOLO_METRICS_DIR / f"{_date_to_filename(date)}.json"
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            logger.info(f"[yolo_segment] 使用缓存指标: {metrics_file.name}")
            return {
                "yolo_today": cached,
                "yolo_metrics": YoloMetrics.from_raw(cached).model_dump(),
                "node_trace": [{"node": "yolo_segment", "status": "cached"}],
            }

        if not yolo_service.is_available:
            logger.warning("[yolo_segment] YOLO 服务不可用，使用默认指标")
            defaults = _get_default_yolo_metrics()
            return {
                "yolo_today": defaults,
                "yolo_metrics": YoloMetrics.from_raw(defaults).model_dump(),
                "warnings": ["YOLO 服务不可用，使用默认指标"],
                "node_trace": [{"node": "yolo_segment", "status": "fallback"}],
            }

        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        metrics, _ = yolo_service.process_bytes(
            image_bytes,
            filename=_date_to_filename(date)
        )

        YOLO_METRICS_DIR.mkdir(parents=True, exist_ok=True)
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        logger.info(f"[yolo_segment] 完成: {len(metrics)} 项指标")
        return {
            "yolo_today": metrics,
            "yolo_metrics": YoloMetrics.from_raw(metrics).model_dump(),
            "node_trace": [{"node": "yolo_segment", "status": "ok"}],
        }

    except Exception as e:
        logger.error(f"[yolo_segment] 失败: {e}")
        defaults = _get_default_yolo_metrics()
        return {
            "yolo_today": defaults,
            "yolo_metrics": YoloMetrics.from_raw(defaults).model_dump(),
            "error": f"YOLO failed: {e}",
            "warnings": [f"YOLO 推理失败: {e}"],
            "node_trace": [{"node": "yolo_segment", "status": "error", "detail": str(e)}],
        }
