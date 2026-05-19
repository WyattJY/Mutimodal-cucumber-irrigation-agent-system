#!/usr/bin/env python3
"""Seed August-October 2024 validation demo data for local UI demos."""

from __future__ import annotations

import csv
import json
import math
import shutil
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data" / "csv" / "irrigation_pre.csv"
STORAGE_DIR = PROJECT_ROOT / "data" / "storage"
DEMO_STORAGE_DIR = PROJECT_ROOT / "data" / "demo_storage"
RESPONSES_DIR = PROJECT_ROOT / "output" / "responses"
WEEKLY_STORAGE_DIR = PROJECT_ROOT / "data" / "weekly_storage"
DEMO_IMAGES_DIR = PROJECT_ROOT / "demo_cases" / "images"
DATA_IMAGES_DIR = PROJECT_ROOT / "data" / "images"
SEGMENTED_IMAGES_DIR = PROJECT_ROOT / "output" / "segmented_images"
YOLO_METRICS_DIR = PROJECT_ROOT / "output" / "yolo_metrics"
DASHBOARD_TODAY_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "images"
    / "0420.jpg"
)
DASHBOARD_YESTERDAY_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "images"
    / "0419.jpg"
)
SOURCE_IMAGE = DASHBOARD_TODAY_IMAGE
DEMO_SAMPLE_IMAGE = "cucumber_monitor_original_0420.jpg"


def parse_date(value: str) -> date:
    year, month, day = [int(part) for part in value.replace("/", "-").split("-")]
    return date(year, month, day)


def as_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = (row.get(key) or "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def stage_for_day(day: date) -> str:
    if day < date(2024, 9, 6):
        return "flowering"
    if day < date(2024, 11, 16):
        return "fruiting"
    return "harvest"


def trend_for_row(row: dict[str, str], prev: dict[str, str] | None) -> str:
    if prev is None:
        return "same"
    leaf_now = as_float(row, "all leaf mask")
    leaf_prev = as_float(prev, "all leaf mask")
    fruit_now = as_float(row, "fruit Mask average")
    fruit_prev = as_float(prev, "fruit Mask average")
    if leaf_prev <= 0:
        return "same"
    leaf_delta = (leaf_now - leaf_prev) / leaf_prev
    fruit_delta = fruit_now - fruit_prev
    temp = as_float(row, "temperature")
    humidity = as_float(row, "humidity")
    light = as_float(row, "light")

    if leaf_delta > 0.035 or fruit_delta > 180:
        return "better"
    if leaf_delta < -0.045 or temp < 12 or humidity > 92 or light < 1400:
        return "worse"
    return "same"


def change_label(current: float, previous: float) -> str:
    if previous <= 0:
        return "持平"
    delta = (current - previous) / previous
    if delta > 0.03:
        return "增加"
    if delta < -0.03:
        return "减少"
    return "持平"


def risk_from_env(row: dict[str, str], trend: str) -> tuple[dict[str, str], list[str]]:
    temp = as_float(row, "temperature")
    humidity = as_float(row, "humidity")
    light = as_float(row, "light")
    abnormalities = {
        "wilting": "none",
        "yellowing": "none",
        "pest_damage": "none",
        "other": "未见明显异常，继续结合图像表型和环境数据观察。",
    }
    notes: list[str] = []
    if temp >= 32:
        abnormalities["wilting"] = "mild"
        notes.append(f"日均温度 {temp:.1f}℃ 偏高，午间应关注叶片萎蔫和基质含水。")
    if humidity >= 88:
        abnormalities["other"] = f"湿度 {humidity:.1f}% 偏高，需加强通风，降低霜霉病和灰霉病风险。"
        notes.append(f"湿度 {humidity:.1f}% 偏高，建议优先通风除湿。")
    if light <= 1800:
        abnormalities["yellowing"] = "mild"
        notes.append(f"光照 {light:.0f} lux 偏低，灌水宜保守，避免根区长期过湿。")
    if trend == "worse" and not notes:
        notes.append("长势指标下降，建议复核根区含水、EC 与通风条件。")
    if not notes:
        notes.append("环境和表型处于可控范围，维持小水勤灌和每日巡检。")
    return abnormalities, notes


def build_episode(day: date, row: dict[str, str], prev_row: dict[str, str] | None, index: int) -> dict:
    trend = trend_for_row(row, prev_row)
    stage = stage_for_day(day)
    target = max(0.0, as_float(row, "Target"))
    confidence = 0.74 + min(0.18, abs(as_float(row, "all leaf mask") - as_float(prev_row or {}, "all leaf mask")) / 1_800_000)
    abnormalities, notes = risk_from_env(row, trend)
    prev = prev_row or row

    yolo_today = {
        "leaf Instance Count": as_float(row, "leaf Instance Count"),
        "leaf average mask": as_float(row, "leaf average mask"),
        "flower Instance Count": as_float(row, "flower Instance Count"),
        "flower Mask Pixel Count": as_float(row, "flower Mask Pixel Count"),
        "terminal average Mask Pixel Count": as_float(row, "terminal average Mask Pixel Count"),
        "fruit Mask average": as_float(row, "fruit Mask average"),
        "all leaf mask": as_float(row, "all leaf mask"),
    }
    yolo_yesterday = {
        "leaf Instance Count": as_float(prev, "leaf Instance Count"),
        "leaf average mask": as_float(prev, "leaf average mask"),
        "flower Instance Count": as_float(prev, "flower Instance Count"),
        "flower Mask Pixel Count": as_float(prev, "flower Mask Pixel Count"),
        "terminal average Mask Pixel Count": as_float(prev, "terminal average Mask Pixel Count"),
        "fruit Mask average": as_float(prev, "fruit Mask average"),
        "all leaf mask": as_float(prev, "all leaf mask"),
    }
    env_today = {
        "temperature": round(as_float(row, "temperature"), 2),
        "humidity": round(as_float(row, "humidity"), 2),
        "light": round(as_float(row, "light"), 2),
        "solar_radiation": round(as_float(row, "light"), 2),
    }
    response = {
        "trend": trend,
        "confidence": round(min(confidence, 0.93), 2),
        "evidence": {
            "leaf_observation": (
                f"叶片实例数 {yolo_today['leaf Instance Count']:.1f}，总叶片 mask "
                f"{yolo_today['all leaf mask']:.0f}px，较前一日{change_label(yolo_today['all leaf mask'], yolo_yesterday['all leaf mask'])}。"
            ),
            "flower_observation": f"花朵实例数 {yolo_today['flower Instance Count']:.1f}，用于判断开花和坐果压力。",
            "fruit_observation": f"果实平均 mask {yolo_today['fruit Mask average']:.0f}px，反映果实膨大阶段的水分需求。",
            "terminal_bud_observation": f"顶芽平均 mask {yolo_today['terminal average Mask Pixel Count']:.0f}px，辅助判断生长点活力。",
        },
        "abnormalities": abnormalities,
        "growth_stage": stage,
        "comparison": {
            "leaf_area_change": change_label(yolo_today["all leaf mask"], yolo_yesterday["all leaf mask"]),
            "leaf_count_change": change_label(yolo_today["leaf Instance Count"], yolo_yesterday["leaf Instance Count"]),
            "flower_count_change": change_label(yolo_today["flower Instance Count"], yolo_yesterday["flower Instance Count"]),
            "fruit_count_change": change_label(yolo_today["fruit Mask average"], yolo_yesterday["fruit Mask average"]),
            "overall_vigor_change": {"better": "增加", "same": "持平", "worse": "减少"}[trend],
        },
        "current_state_summary": " ".join(notes),
    }
    episode = {
        "date": day.isoformat(),
        "season": "validation-2024-autumn",
        "day_in_season": index + 1,
        "created_at": "2026-05-17T00:00:00",
        "updated_at": "2026-05-17T00:00:00",
        "prompt_version": "validation-2024-v1",
        "image_today": str(SOURCE_IMAGE) if SOURCE_IMAGE.exists() else None,
        "image_yesterday": str(DASHBOARD_YESTERDAY_IMAGE) if DASHBOARD_YESTERDAY_IMAGE.exists() else None,
        "inputs": {
            "environment": env_today,
            "yolo_metrics": yolo_today,
            "image_path": str(SOURCE_IMAGE) if SOURCE_IMAGE.exists() else None,
        },
        "yolo_today": yolo_today,
        "yolo_yesterday": yolo_yesterday,
        "env_today": env_today,
        "predictions": {
            "tsmixer_raw": round(target, 2),
            "plant_response": response,
            "sanity_check": {
                "passed": trend != "worse" or target <= 4.5,
                "adjustment_reason": "结合 2024 年秋茬验证试验环境与视觉表型自动判断。",
            },
            "growth_stage": stage,
            "growth_stage_confidence": round(min(confidence, 0.93), 2),
        },
        "response": response,
        "anomalies": {
            "out_of_range": env_today["temperature"] < 12 or env_today["temperature"] > 35,
            "trend_conflict": trend == "worse" and target > 5,
            "trend_conflict_severity": "minor" if trend == "worse" and target > 5 else "none",
            "env_anomaly": env_today["humidity"] > 88 or env_today["light"] < 1800,
            "env_anomaly_type": "high_humidity_or_low_light" if env_today["humidity"] > 88 or env_today["light"] < 1800 else None,
        },
        "final_decision": {
            "value": round(target, 2),
            "source": "tsmixer",
            "override_reason": None,
        },
        "irrigation_amount": round(target, 2),
        "decision_source": "TSMixer",
        "user_feedback": {
            "actual_irrigation": None,
            "notes": None,
            "rating": None,
        },
        "rag_doc_ids": [],
        "knowledge_references": [],
        "raw_response": json.dumps(response, ensure_ascii=False, indent=2),
    }
    return episode


def build_weekly_summaries(episodes: list[dict]) -> list[dict]:
    grouped: dict[tuple[date, date], list[dict]] = defaultdict(list)
    for episode in episodes:
        current = date.fromisoformat(episode["date"])
        week_start = current - timedelta(days=current.weekday())
        week_end = week_start + timedelta(days=6)
        grouped[(week_start, week_end)].append(episode)

    summaries: list[dict] = []
    for (week_start, week_end), week_episodes in sorted(grouped.items()):
        values = [float(ep.get("irrigation_amount") or 0) for ep in week_episodes]
        trends = [ep.get("response", {}).get("trend", "same") for ep in week_episodes]
        better = trends.count("better")
        same = trends.count("same")
        worse = trends.count("worse")
        total = sum(values)
        avg = total / len(values) if values else 0
        trend_name = "向好" if better > max(same, worse) else "下降" if worse > same else "平稳"
        irrigation_trend = "上升" if len(values) >= 2 and values[-1] > values[0] else "下降" if len(values) >= 2 and values[-1] < values[0] else "稳定"
        humidity_high = sum(1 for ep in week_episodes if ep.get("env_today", {}).get("humidity", 0) >= 88)
        low_light = sum(1 for ep in week_episodes if ep.get("env_today", {}).get("light", 0) <= 1800)
        insights = [
            f"本周覆盖 {len(week_episodes)} 天验证试验数据，长势以{trend_name}为主，日均灌水 {avg:.2f} L/m²。",
            f"灌水量整体{irrigation_trend}，范围 {min(values):.2f}-{max(values):.2f} L/m²。",
        ]
        if humidity_high or low_light:
            insights.append(f"高湿天数 {humidity_high} 天、低光照天数 {low_light} 天，建议优先通风除湿并保守灌水。")
        else:
            insights.append("环境风险较低，可维持当前灌水节奏并观察果实膨大。")

        summaries.append({
            "week_start": week_start.isoformat(),
            "week_end": min(week_end, date.fromisoformat(episodes[-1]["date"])).isoformat(),
            "season": "validation-2024-autumn",
            "trend_stats": {
                "better_days": better,
                "same_days": same,
                "worse_days": worse,
                "dominant_trend": "better" if better > max(same, worse) else "worse" if worse > same else "same",
            },
            "irrigation_stats": {
                "total": round(total, 2),
                "daily_avg": round(avg, 2),
                "max": round(max(values), 2) if values else 0,
                "min": round(min(values), 2) if values else 0,
                "trend": "increasing" if irrigation_trend == "上升" else "decreasing" if irrigation_trend == "下降" else "stable",
            },
            "anomaly_events": [],
            "override_summary": {"count": 0, "total_delta": 0.0, "reasons": []},
            "key_insights": insights,
            "knowledge_references": [],
            "prompt_block": (
                f"## 上周经验 ({week_start.isoformat()} ~ {min(week_end, date.fromisoformat(episodes[-1]['date'])).isoformat()})\n"
                f"长势趋势: {trend_name} | 灌溉趋势: {irrigation_trend} (日均 {avg:.2f} L/m²)\n"
                "关键洞察:\n- " + "\n- ".join(insights)
            ),
            "prompt_block_tokens": 120,
            "created_at": "2026-05-17T00:00:00",
            "updated_at": "2026-05-17T00:00:00",
        })
    return summaries


def main() -> None:
    rows: list[tuple[date, dict[str, str]]] = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            current = parse_date(row["date"])
            if date(2024, 8, 1) <= current <= date(2024, 10, 31):
                rows.append((current, row))

    if not rows:
        raise SystemExit("No 2024-08 to 2024-10 rows found in irrigation_pre.csv")

    episodes: list[dict] = []
    prev_row: dict[str, str] | None = None
    for index, (current, row) in enumerate(rows):
        episode = build_episode(current, row, prev_row, index)
        episodes.append(episode)
        prev_row = row

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    WEEKLY_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    SEGMENTED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    YOLO_METRICS_DIR.mkdir(parents=True, exist_ok=True)

    for existing_response in RESPONSES_DIR.glob("*.json"):
        if not existing_response.name.startswith("._"):
            existing_response.unlink()

    for stale_path in (
        SEGMENTED_IMAGES_DIR / "1030_segmented.jpg",
        SEGMENTED_IMAGES_DIR / "1031_segmented.jpg",
        YOLO_METRICS_DIR / "1030_metrics.json",
        YOLO_METRICS_DIR / "1031_metrics.json",
    ):
        if stale_path.exists():
            stale_path.unlink()

    for path in (STORAGE_DIR / "episodes.json", DEMO_STORAGE_DIR / "episodes.json"):
        path.write_text(json.dumps(episodes, ensure_ascii=False, indent=2), encoding="utf-8")

    weekly = build_weekly_summaries(episodes)
    for path in (STORAGE_DIR / "weekly_summaries.json", DEMO_STORAGE_DIR / "weekly.json", WEEKLY_STORAGE_DIR / "weekly.json"):
        path.write_text(json.dumps(weekly, ensure_ascii=False, indent=2), encoding="utf-8")

    (STORAGE_DIR / "overrides.json").write_text("{}", encoding="utf-8")
    overrides_db = STORAGE_DIR / "irrigation_overrides.sqlite3"
    if overrides_db.exists():
        with sqlite3.connect(str(overrides_db)) as conn:
            conn.execute("DELETE FROM irrigation_overrides")
            conn.commit()

    for episode in episodes:
        output_payload = {
            key: episode[key]
            for key in (
                "date",
                "created_at",
                "prompt_version",
                "image_today",
                "image_yesterday",
                "yolo_today",
                "yolo_yesterday",
                "env_today",
                "response",
                "raw_response",
                "irrigation_amount",
                "final_decision",
            )
        }
        (RESPONSES_DIR / f"{episode['date']}.json").write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if SOURCE_IMAGE.exists():
        shutil.copy2(SOURCE_IMAGE, DEMO_IMAGES_DIR / DEMO_SAMPLE_IMAGE)
        shutil.copy2(SOURCE_IMAGE, DEMO_IMAGES_DIR / "cucumber_validation_20240826.jpg")
        shutil.copy2(SOURCE_IMAGE, DATA_IMAGES_DIR / "1031.jpg")
    if DASHBOARD_YESTERDAY_IMAGE.exists():
        shutil.copy2(DASHBOARD_YESTERDAY_IMAGE, DATA_IMAGES_DIR / "1030.jpg")

    print(f"Seeded {len(episodes)} validation episodes: {episodes[0]['date']} -> {episodes[-1]['date']}")
    print(f"Seeded {len(weekly)} weekly summaries")


if __name__ == "__main__":
    main()
