"""
Anomaly detection node — three-tier check.

A1: Range check (irrigation outside [0.1, 15.0] L/m²)
A2: Trend-irrigation conflict
A3: Environmental anomaly (high humidity, high temp, low light)
"""
from __future__ import annotations

from loguru import logger

from app.observability.decorators import traced_node


def _check_a1_range(prediction: float) -> dict:
    """A1: Is prediction within reasonable range?"""
    if prediction < 0.1:
        return {"triggered": True, "severity": "severe", "detail": f"预测值 {prediction:.2f} 低于下限 0.1"}
    if prediction > 15.0:
        return {"triggered": True, "severity": "severe", "detail": f"预测值 {prediction:.2f} 超过上限 15.0"}
    if prediction < 1.0 or prediction > 12.0:
        return {"triggered": True, "severity": "moderate", "detail": f"预测值 {prediction:.2f} 接近边界"}
    return {"triggered": False, "severity": "none", "detail": ""}


def _check_a2_trend_conflict(prediction: float, plant_response: dict) -> dict:
    """A2: Does prediction direction match plant trend?"""
    if not plant_response:
        return {"triggered": False, "severity": "none", "detail": ""}

    trend = plant_response.get("trend")
    if not trend:
        return {"triggered": False, "severity": "none", "detail": ""}

    if trend == "worse" and prediction < 4.5:
        return {
            "triggered": True,
            "severity": "moderate",
            "detail": f"长势恶化但灌水量偏低 ({prediction:.2f} L/m²)",
        }
    if trend == "better" and prediction > 8.0:
        return {
            "triggered": True,
            "severity": "mild",
            "detail": f"长势好转但灌水量偏高 ({prediction:.2f} L/m²)",
        }
    return {"triggered": False, "severity": "none", "detail": ""}


def _check_a3_environment(env_data: dict) -> dict:
    """A3: Environmental anomaly detection."""
    issues = []
    temp = env_data.get("temperature", 25)
    humidity = env_data.get("humidity", 70)
    light = env_data.get("light", 50000)

    if temp > 35:
        issues.append(f"高温 {temp}°C (>35°C)")
    if humidity > 85:
        issues.append(f"高湿 {humidity}% (>85%)")
    if light < 2000:
        issues.append(f"弱光 {light} lux (<2000)")

    if issues:
        severity = "severe" if len(issues) >= 2 else "moderate"
        return {"triggered": True, "severity": severity, "detail": "; ".join(issues)}
    return {"triggered": False, "severity": "none", "detail": ""}


def _max_severity(*severities: str) -> str:
    order = {"none": 0, "mild": 1, "moderate": 2, "severe": 3}
    max_val = max(order.get(s, 0) for s in severities)
    return {0: "none", 1: "mild", 2: "moderate", 3: "severe"}[max_val]


@traced_node("anomaly_detect")
def run(state: dict) -> dict:
    """Run three-tier anomaly detection."""
    prediction = state.get("tsmixer_prediction", 5.0)
    plant_response = state.get("plant_response")
    env_data = state.get("env_data", {})

    a1 = _check_a1_range(prediction)
    a2 = _check_a2_trend_conflict(prediction, plant_response)
    a3 = _check_a3_environment(env_data)

    has_anomaly = a1["triggered"] or a2["triggered"] or a3["triggered"]
    severity = _max_severity(a1["severity"], a2["severity"], a3["severity"])

    anomaly_result = {
        "a1_range": a1,
        "a2_trend_conflict": a2,
        "a3_environment": a3,
        "has_anomaly": has_anomaly,
        "severity": severity,
    }

    warnings = []
    if a1["triggered"]:
        warnings.append(f"[A1] {a1['detail']}")
    if a2["triggered"]:
        warnings.append(f"[A2] {a2['detail']}")
    if a3["triggered"]:
        warnings.append(f"[A3] {a3['detail']}")

    logger.info(f"[anomaly_detect] has_anomaly={has_anomaly}, severity={severity}")
    return {
        "anomaly_result": anomaly_result,
        "has_anomaly": has_anomaly,
        "anomaly_severity": severity,
        "warnings": warnings,
        "node_trace": [{"node": "anomaly_detect", "status": "ok", "has_anomaly": has_anomaly, "severity": severity}],
    }
