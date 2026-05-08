"""
Finalize node — determine final irrigation amount, save Episode and PlantResponse.

Two variants:
- run(): normal finalization
- run_emergency(): severe anomaly path (clamp prediction, add warnings)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.services.memory_service import memory_service
from app.models.schemas import PredictionSource
from app.observability.decorators import traced_node

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESPONSES_DIR = PROJECT_ROOT / "output" / "responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# Episode model import (optional)
try:
    import sys
    SRC_DIR = PROJECT_ROOT.parent / "src"
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    from cucumber_irrigation.models.episode import (
        Episode, EpisodeInputs, EpisodePredictions,
        EpisodeAnomalies, FinalDecision,
    )
    EPISODE_MODEL_AVAILABLE = True
except ImportError:
    EPISODE_MODEL_AVAILABLE = False


async def _save_plant_response(date, plant_response, yolo_today, yolo_yesterday,
                                env_data, image_today_path, image_yesterday_path) -> str:
    """Save PlantResponse JSON to output/responses/."""
    try:
        response_data = {
            "date": date,
            "created_at": datetime.now().isoformat(),
            "prompt_version": "v2_graph",
            "image_today": image_today_path,
            "image_yesterday": image_yesterday_path,
            "yolo_today": yolo_today,
            "yolo_yesterday": yolo_yesterday,
            "env_today": env_data,
            "response": plant_response,
            "is_cold_start": plant_response.get("is_cold_start", False) if plant_response else False,
        }
        save_path = RESPONSES_DIR / f"{date}.json"
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
        return str(save_path)
    except Exception as e:
        logger.error(f"保存 PlantResponse 失败: {e}")
        return ""


async def _create_episode(date, env_data, yolo_today, tsmixer_prediction,
                           plant_response, sanity_check, final_value, source, is_cold_start):
    """Create and save Episode to memory store."""
    try:
        if EPISODE_MODEL_AVAILABLE:
            episode = Episode(
                date=date,
                inputs=EpisodeInputs(environment=env_data, yolo_metrics=yolo_today),
                predictions=EpisodePredictions(
                    tsmixer_raw=tsmixer_prediction,
                    plant_response=plant_response or {},
                    sanity_check=sanity_check or {},
                    growth_stage=plant_response.get("growth_stage") if plant_response else None,
                ),
                anomalies=EpisodeAnomalies(),
                final_decision=FinalDecision(value=final_value, source=source),
            )
            return await memory_service.save_episode(episode)
        else:
            episode_data = {
                "date": date,
                "inputs": {"environment": env_data, "yolo_metrics": yolo_today},
                "predictions": {
                    "tsmixer_raw": tsmixer_prediction,
                    "plant_response": plant_response or {},
                    "sanity_check": sanity_check or {},
                    "is_cold_start": is_cold_start,
                },
                "final_decision": {"value": final_value, "source": source},
                "created_at": datetime.now().isoformat(),
            }
            return await memory_service.save_episode(episode_data)
    except Exception as e:
        logger.error(f"创建 Episode 失败: {e}")
        return None


@traced_node("finalize")
async def run(state: dict) -> dict:
    """Normal finalization: determine final value, save results."""
    date = state["date"]
    tsmixer_prediction = state.get("tsmixer_prediction", 5.0)
    sanity_check = state.get("sanity_check")
    sanity_passed = state.get("sanity_passed", True)
    plant_response = state.get("plant_response")
    env_data = state.get("env_data", {})
    yolo_today = state.get("yolo_today", {})
    is_cold_start = state.get("is_cold_start", False)
    options = state.get("options", {})

    # Determine final irrigation amount
    if sanity_check and not sanity_passed:
        final_value = sanity_check.get("adjusted_value", tsmixer_prediction)
        source = PredictionSource.SANITY_ADJUSTED.value
    else:
        final_value = tsmixer_prediction
        source = PredictionSource.TSMIXER.value

    warnings = []
    if not sanity_passed and sanity_check:
        warnings.append(
            f"SanityCheck 调整: {tsmixer_prediction:.2f} → {final_value:.2f}"
        )

    # Save PlantResponse
    response_saved_path = None
    if options.get("save_response", True) and plant_response:
        response_saved_path = await _save_plant_response(
            date, plant_response, yolo_today,
            state.get("yolo_yesterday"),
            env_data,
            state.get("image_today_path"),
            state.get("image_yesterday_path"),
        )

    # Save Episode
    episode_id = None
    if options.get("save_episode", True):
        episode_id = await _create_episode(
            date, env_data, yolo_today, tsmixer_prediction,
            plant_response, sanity_check,
            final_value, source, is_cold_start,
        )

    logger.info(f"[finalize] 最终灌水量: {final_value:.2f} L/m², source={source}")
    return {
        "irrigation_amount": final_value,
        "prediction_source": source,
        "episode_id": episode_id,
        "response_saved_path": response_saved_path,
        "warnings": warnings,
        "node_trace": [{"node": "finalize", "status": "ok", "value": round(final_value, 2), "source": source}],
    }


@traced_node("finalize_emergency")
async def run_emergency(state: dict) -> dict:
    """Emergency finalization for severe anomalies — clamp prediction to safe range."""
    date = state["date"]
    tsmixer_prediction = state.get("tsmixer_prediction", 5.0)
    anomaly_result = state.get("anomaly_result", {})
    plant_response = state.get("plant_response")
    env_data = state.get("env_data", {})
    yolo_today = state.get("yolo_today", {})
    is_cold_start = state.get("is_cold_start", False)
    options = state.get("options", {})

    # Clamp to safe range
    final_value = max(1.0, min(tsmixer_prediction, 10.0))
    source = PredictionSource.FALLBACK.value

    warnings = [
        f"严重异常触发紧急路径: 灌水量从 {tsmixer_prediction:.2f} 钳位至 {final_value:.2f} L/m²",
    ]

    a1 = anomaly_result.get("a1_range", {})
    a3 = anomaly_result.get("a3_environment", {})
    if a1.get("triggered"):
        warnings.append(f"[A1] {a1.get('detail', '')}")
    if a3.get("triggered"):
        warnings.append(f"[A3] {a3.get('detail', '')}")

    # Still save results
    response_saved_path = None
    if options.get("save_response", True) and plant_response:
        response_saved_path = await _save_plant_response(
            date, plant_response, yolo_today,
            state.get("yolo_yesterday"),
            env_data,
            state.get("image_today_path"),
            state.get("image_yesterday_path"),
        )

    episode_id = None
    if options.get("save_episode", True):
        episode_id = await _create_episode(
            date, env_data, yolo_today, tsmixer_prediction,
            plant_response, None,
            final_value, source, is_cold_start,
        )

    logger.warning(f"[finalize_emergency] 紧急灌水量: {final_value:.2f} L/m²")
    return {
        "irrigation_amount": final_value,
        "prediction_source": source,
        "episode_id": episode_id,
        "response_saved_path": response_saved_path,
        "warnings": warnings,
        "suggestions": ["建议人工检查温室环境和灌溉设备"],
        "node_trace": [{"node": "finalize_emergency", "status": "ok", "value": round(final_value, 2)}],
    }
