"""Multimodal feature construction for YOLO11n-FCHL + TSMixer.

The resume claim is an 11-dimensional sequence:
3 environmental features + 7 YOLO visual phenotype features + 1 historical
irrigation feature, expanded to a 96-day TSMixer window.
"""
from __future__ import annotations

from typing import Iterable


ENV_FEATURES = ("temperature", "humidity", "light")
YOLO_FEATURES = (
    "leaf Instance Count",
    "leaf average mask",
    "flower Instance Count",
    "flower Mask Pixel Count",
    "terminal average Mask Pixel Count",
    "fruit Mask average",
    "all leaf mask",
)
FEATURE_NAMES = (*ENV_FEATURES, *YOLO_FEATURES, "history_irrigation")
WINDOW_SIZE = 96


def _number(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_feature_vector(
    env_data: dict | None,
    yolo_metrics: dict | None,
    history_irrigation: float | int | None = None,
) -> list[float]:
    env_data = env_data or {}
    yolo_metrics = yolo_metrics or {}
    vector = [_number(env_data.get(name)) for name in ENV_FEATURES]
    vector.extend(_number(yolo_metrics.get(name)) for name in YOLO_FEATURES)
    vector.append(_number(history_irrigation))
    return vector


def build_feature_window(
    env_data: dict | None,
    yolo_metrics: dict | None,
    history_irrigation: Iterable[float] | None = None,
    window_size: int = WINDOW_SIZE,
) -> list[list[float]]:
    history = list(history_irrigation or [])
    last_irrigation = history[-1] if history else 0.0
    current = build_feature_vector(env_data, yolo_metrics, last_irrigation)

    window: list[list[float]] = []
    for idx in range(window_size):
        irrigation_value = history[idx - window_size] if len(history) >= window_size - idx else last_irrigation
        row = current[:-1] + [_number(irrigation_value)]
        window.append(row)
    return window


def describe_feature_contract() -> dict:
    return {
        "feature_count": len(FEATURE_NAMES),
        "window_size": WINDOW_SIZE,
        "feature_names": list(FEATURE_NAMES),
        "modalities": {
            "environment": list(ENV_FEATURES),
            "vision_yolo11n_fchl": list(YOLO_FEATURES),
            "history": ["history_irrigation"],
        },
    }
