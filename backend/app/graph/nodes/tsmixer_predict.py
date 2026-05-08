"""
Build 96-day input window and run TSMixer prediction.

Wraps: tsmixer_service.build_features + tsmixer_service.predict
"""
from __future__ import annotations

from loguru import logger

from app.services.tsmixer_service import tsmixer_service
from app.observability.decorators import traced_node


@traced_node("tsmixer_predict")
def run(state: dict) -> dict:
    """Build feature window and run TSMixer inference."""
    date = state["date"]
    env_data = state.get("env_data", {})
    yolo_today = state.get("yolo_today", {})
    skip = state.get("options", {}).get("skip_tsmixer", False)

    if skip:
        logger.info("[tsmixer_predict] 跳过 TSMixer")
        return {
            "tsmixer_prediction": 5.0,
            "warnings": ["TSMixer 已跳过，使用默认灌水量 5.0 L/m²"],
            "node_trace": [{"node": "tsmixer_predict", "status": "skipped"}],
        }

    try:
        if not tsmixer_service.is_available:
            logger.warning("[tsmixer_predict] TSMixer 不可用，使用默认值")
            return {
                "tsmixer_prediction": 5.0,
                "warnings": ["TSMixer 服务不可用，使用默认灌水量"],
                "node_trace": [{"node": "tsmixer_predict", "status": "fallback"}],
            }

        features = tsmixer_service.build_features(
            env_data=env_data,
            yolo_metrics=yolo_today,
            target_date=date,
        )

        result = tsmixer_service.predict(features)

        if isinstance(result, dict):
            prediction = float(result.get("predicted_value", 5.0))
        else:
            prediction = float(result)

        logger.info(f"[tsmixer_predict] 预测值: {prediction:.2f} L/m²")
        return {
            "tsmixer_prediction": prediction,
            "node_trace": [{"node": "tsmixer_predict", "status": "ok", "value": round(prediction, 2)}],
        }

    except Exception as e:
        logger.error(f"[tsmixer_predict] 失败: {e}")
        return {
            "tsmixer_prediction": 5.0,
            "error": f"TSMixer failed: {e}",
            "warnings": [f"TSMixer 预测失败: {e}，使用默认值"],
            "node_trace": [{"node": "tsmixer_predict", "status": "error", "detail": str(e)}],
        }
