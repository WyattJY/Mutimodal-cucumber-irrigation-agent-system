from __future__ import annotations
# Episode Data Service - 读取和处理 Episode 数据
"""
Episode 数据服务

功能:
1. 读取和查询 Episode 数据
2. 计算灌水量和风险等级
3. 用户反馈管理
4. 趋势数据分析

数据源:
- output/responses/*.json (PlantResponse 文件)
- data/storage/episodes.json (Memory Service 的 Episode 存储)
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple, Any
from datetime import datetime
from loguru import logger

# 项目根目录 (相对于 backend/app/services)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
RESPONSES_DIR = OUTPUT_DIR / "responses"
FEEDBACK_DIR = OUTPUT_DIR / "feedback"
DATA_DIR = PROJECT_ROOT / "data"
MEMORY_EPISODES_FILE = DATA_DIR / "storage" / "episodes.json"
MEMORY_WEEKLY_FILE = DATA_DIR / "storage" / "weekly_summaries.json"
OVERRIDES_DB = DATA_DIR / "storage" / "irrigation_overrides.sqlite3"
OVERRIDES_FILE = DATA_DIR / "storage" / "overrides.json"

# 确保目录存在
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def _load_memory_episodes() -> List[dict]:
    """从 Memory Service 的 episodes.json 加载数据"""
    if not MEMORY_EPISODES_FILE.exists():
        return []
    try:
        with open(MEMORY_EPISODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"加载 memory episodes 失败: {e}")
        return []


def _ensure_overrides_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS irrigation_overrides (
            date TEXT PRIMARY KEY,
            original_value REAL NOT NULL,
            replaced_value REAL NOT NULL,
            reason TEXT NOT NULL,
            confirmation_answers TEXT NOT NULL DEFAULT '{}',
            override_by TEXT NOT NULL DEFAULT 'user',
            override_at TEXT NOT NULL,
            history TEXT NOT NULL DEFAULT '[]'
        )
        """
    )


def _read_overrides_snapshot() -> dict[str, dict]:
    if not OVERRIDES_FILE.exists():
        return {}
    try:
        with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning(f"加载 override 快照失败: {e}")
        return {}


def _write_overrides_snapshot(overrides: dict[str, dict]) -> None:
    OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = OVERRIDES_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)
    tmp_path.replace(OVERRIDES_FILE)


def _load_overrides_from_db() -> dict[str, dict]:
    if not OVERRIDES_DB.exists():
        return {}

    try:
        with sqlite3.connect(str(OVERRIDES_DB)) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_overrides_table(conn)
            rows = conn.execute(
                """
                SELECT date, original_value, replaced_value, reason,
                       confirmation_answers, override_by, override_at, history
                FROM irrigation_overrides
                """
            ).fetchall()
    except Exception as e:
        logger.warning(f"加载 override SQL 记录失败: {e}")
        return {}

    overrides: dict[str, dict] = {}
    for row in rows:
        try:
            confirmation_answers = json.loads(row["confirmation_answers"] or "{}")
        except Exception:
            confirmation_answers = {}
        try:
            history = json.loads(row["history"] or "[]")
        except Exception:
            history = []

        overrides[row["date"]] = {
            "date": row["date"],
            "original_value": row["original_value"],
            "replaced_value": row["replaced_value"],
            "reason": row["reason"],
            "confirmation_answers": confirmation_answers if isinstance(confirmation_answers, dict) else {},
            "override_by": row["override_by"],
            "override_at": row["override_at"],
            "history": history if isinstance(history, list) else [],
        }
    return overrides


def _load_overrides() -> dict[str, dict]:
    """加载人工覆盖记录。"""
    overrides = _load_overrides_from_db()
    if overrides:
        return overrides

    overrides = _read_overrides_snapshot()
    if overrides:
        _save_overrides(overrides)
    return overrides


def _save_overrides(overrides: dict[str, dict]) -> None:
    """保存人工覆盖记录到本地 SQL 表，并同步审计快照。"""
    OVERRIDES_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(OVERRIDES_DB)) as conn:
        _ensure_overrides_table(conn)
        conn.execute("DELETE FROM irrigation_overrides")
        conn.executemany(
            """
            INSERT INTO irrigation_overrides (
                date, original_value, replaced_value, reason,
                confirmation_answers, override_by, override_at, history
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.get("date") or date,
                    float(row.get("original_value", 0) or 0),
                    float(row.get("replaced_value", 0) or 0),
                    row.get("reason", ""),
                    json.dumps(row.get("confirmation_answers") or {}, ensure_ascii=False),
                    row.get("override_by", "user"),
                    row.get("override_at") or datetime.now().isoformat(),
                    json.dumps(row.get("history") or [], ensure_ascii=False),
                )
                for date, row in sorted(overrides.items())
            ],
        )
        conn.commit()

    _write_overrides_snapshot(overrides)


def _apply_override(data: dict) -> dict:
    """将人工覆盖层叠加到 Episode 数据上。"""
    date = data.get("date")
    if not date:
        return data

    override = _load_overrides().get(date)
    if not override:
        return data

    final_decision = data.get("final_decision") or {}
    final_decision["value"] = override.get("replaced_value")
    final_decision["source"] = "Override"
    final_decision["override_reason"] = override.get("reason")
    data["final_decision"] = final_decision
    data["irrigation_amount"] = override.get("replaced_value")
    data["decision_source"] = "Override"
    data["override_reason"] = override.get("reason")
    data["override_by"] = override.get("override_by", "user")
    data["override_at"] = override.get("override_at")
    data["override_original_value"] = override.get("original_value")
    data["override_confirmation_answers"] = override.get("confirmation_answers") or {}
    return data


def save_override(
    *,
    date: str,
    original_value: float,
    replaced_value: float,
    reason: str,
    confirmation_answers: Optional[dict[str, Any]] = None,
    override_by: str = "user",
) -> dict:
    """持久化人工覆盖记录，并返回叠加后的 Episode。"""
    existing = get_episode_by_date(date)
    if existing is None:
        raise ValueError(f"Episode not found for date: {date}")

    overrides = _load_overrides()
    previous = overrides.get(date)
    history = list(previous.get("history", [])) if previous else []
    if previous:
        history.append({
            "original_value": previous.get("original_value"),
            "replaced_value": previous.get("replaced_value"),
            "reason": previous.get("reason"),
            "confirmation_answers": previous.get("confirmation_answers") or {},
            "override_by": previous.get("override_by"),
            "override_at": previous.get("override_at"),
        })

    overrides[date] = {
        "date": date,
        "original_value": round(float(original_value), 2),
        "replaced_value": round(float(replaced_value), 2),
        "reason": reason,
        "confirmation_answers": confirmation_answers or {},
        "override_by": override_by,
        "override_at": datetime.now().isoformat(),
        "history": history,
    }
    _save_overrides(overrides)

    updated = get_episode_by_date(date)
    return updated or existing


def _load_weekly_summary() -> Optional[dict]:
    """加载最新的周摘要"""
    if not MEMORY_WEEKLY_FILE.exists():
        return None
    try:
        with open(MEMORY_WEEKLY_FILE, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
            if summaries:
                # 返回最新的
                return sorted(summaries, key=lambda x: x.get('week_end', ''), reverse=True)[0]
        return None
    except Exception as e:
        logger.warning(f"加载 weekly summary 失败: {e}")
        return None


def get_weekly_context() -> Optional[str]:
    """获取周摘要上下文 (用于 Working Context L1)"""
    summary = _load_weekly_summary()
    if summary:
        return summary.get('prompt_block')
    return None


def get_all_dates() -> List[str]:
    """获取所有可用日期列表 (合并两个数据源)"""
    dates = set()

    # 从 responses 目录获取
    if RESPONSES_DIR.exists():
        for file in RESPONSES_DIR.glob("*.json"):
            if file.name.startswith("._"):
                continue
            date = file.stem  # e.g., "2024-06-14"
            dates.add(date)

    # 从 memory episodes 获取
    for ep in _load_memory_episodes():
        if ep.get('date'):
            dates.add(ep['date'])

    for date in _load_overrides().keys():
        dates.add(date)

    return sorted(list(dates), reverse=True)


def get_episode_by_date(date: str) -> Optional[dict]:
    """
    根据日期获取 Episode 数据

    数据来源优先级:
    1. output/responses/{date}.json (PlantResponse)
    2. data/storage/episodes.json (Memory Episodes)

    同时注入记忆上下文 (Weekly Summary)
    """
    data = None

    # 1. 先从 responses 目录读取
    file_path = RESPONSES_DIR / f"{date}.json"
    if file_path.exists() and not file_path.name.startswith("._"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    # 2. 如果没找到，从 memory episodes 读取
    if data is None:
        for ep in _load_memory_episodes():
            if ep.get('date') == date:
                data = ep
                break

    if data is None:
        return None

    if "response" not in data and data.get("predictions", {}).get("plant_response"):
        data["response"] = data["predictions"]["plant_response"]

    data = _apply_override(data)

    final_decision = data.get("final_decision") or {}

    # 添加计算字段
    data["irrigation_amount"] = calculate_irrigation(data)
    data["decision_source"] = final_decision.get("source", "TSMixer")
    data["risk_level"] = calculate_risk_level(data)

    # === 注入记忆上下文 (L1 Working Context) ===
    weekly_context = get_weekly_context()
    if weekly_context:
        data["memory_context"] = {
            "weekly_summary": weekly_context,
            "has_memory": True
        }
    else:
        data["memory_context"] = {
            "weekly_summary": None,
            "has_memory": False
        }

    return data


def get_latest_episode() -> Optional[dict]:
    """获取最新的 Episode"""
    dates = get_all_dates()
    if not dates:
        return None
    return get_episode_by_date(dates[0])


def get_episodes(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    trend: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """查询 Episode 列表"""
    dates = get_all_dates()

    # 筛选日期范围
    if start_date:
        dates = [d for d in dates if d >= start_date]
    if end_date:
        dates = [d for d in dates if d <= end_date]

    # 加载所有 Episode
    episodes = []
    for date in dates:
        ep = get_episode_by_date(date)
        if ep:
            # 筛选趋势
            if trend and trend != "all":
                if ep.get("response", {}).get("trend") != trend:
                    continue
            episodes.append(ep)

    total = len(episodes)

    # 分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = episodes[start_idx:end_idx]

    return paginated, total


def get_growth_stats() -> Optional[dict]:
    """获取生长统计数据"""
    stats_path = OUTPUT_DIR / "growth_stats.json"

    if not stats_path.exists():
        return None

    with open(stats_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_irrigation(episode: dict) -> float:
    """根据 Episode 数据计算灌水量 (模拟)"""
    for candidate in (
        episode.get("irrigation_amount"),
        (episode.get("final_decision") or {}).get("value"),
        (episode.get("predictions") or {}).get("tsmixer_raw"),
    ):
        if candidate is None:
            continue
        try:
            return round(float(candidate), 2)
        except (TypeError, ValueError):
            continue

    env = episode.get("env_today", {})
    temp = env.get("temperature", 25)
    humidity = env.get("humidity", 60)
    light = env.get("light", 5000)

    # 简化的灌水量计算公式
    # 实际应该使用 TSMixer 或 FAO56
    base = 3.0
    temp_factor = (temp - 20) * 0.1
    humidity_factor = (70 - humidity) * 0.02
    light_factor = light / 10000 * 0.5

    irrigation = base + temp_factor + humidity_factor + light_factor
    return round(max(0.5, min(10.0, irrigation)), 1)


def calculate_risk_level(episode: dict) -> str:
    """根据 Episode 数据计算风险等级"""
    response = episode.get("response", {})
    abnormalities = response.get("abnormalities", {})

    # 统计异常数量
    severe_count = sum(1 for v in abnormalities.values() if v == "severe")
    moderate_count = sum(1 for v in abnormalities.values() if v == "moderate")
    mild_count = sum(1 for v in abnormalities.values() if v == "mild")

    if severe_count > 0:
        return "critical"
    elif moderate_count >= 2:
        return "high"
    elif moderate_count > 0 or mild_count >= 2:
        return "medium"
    else:
        return "low"


def get_trend_data(days: int = 30) -> dict:
    """获取趋势数据用于图表"""
    dates = get_all_dates()[:days]
    dates.reverse()  # 按时间正序

    irrigation_values = []
    trends = []
    sources = []

    for date in dates:
        ep = get_episode_by_date(date)
        if ep:
            irrigation_values.append(ep.get("irrigation_amount", 0))
            trends.append(ep.get("response", {}).get("trend", "same"))
            sources.append(ep.get("decision_source", "TSMixer"))
        else:
            irrigation_values.append(0)
            trends.append("same")
            sources.append("TSMixer")

    return {
        "dates": dates,
        "irrigation": irrigation_values,
        "trends": trends,
        "sources": sources,
    }


# ============================================================================
# 用户反馈功能
# ============================================================================

def submit_feedback(
    date: str,
    actual_irrigation: Optional[float] = None,
    rating: Optional[int] = None,
    notes: Optional[str] = None
) -> bool:
    """
    提交用户反馈

    Args:
        date: Episode 日期
        actual_irrigation: 实际灌水量
        rating: 评分 (1-5)
        notes: 备注

    Returns:
        是否提交成功
    """
    try:
        feedback_file = FEEDBACK_DIR / f"{date}.json"

        # 加载现有反馈或创建新的
        if feedback_file.exists():
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback = json.load(f)
        else:
            feedback = {
                "date": date,
                "created_at": datetime.now().isoformat(),
                "history": []
            }

        # 添加新反馈
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "actual_irrigation": actual_irrigation,
            "rating": rating,
            "notes": notes
        }
        feedback["history"].append(new_entry)
        feedback["updated_at"] = datetime.now().isoformat()
        feedback["latest"] = new_entry

        # 保存
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

        logger.info(f"反馈已保存: {date}")
        return True

    except Exception as e:
        logger.error(f"保存反馈失败: {e}")
        return False


def get_feedback(date: str) -> Optional[dict]:
    """
    获取指定日期的反馈

    Args:
        date: Episode 日期

    Returns:
        反馈数据
    """
    try:
        feedback_file = FEEDBACK_DIR / f"{date}.json"

        if feedback_file.exists():
            with open(feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    except Exception as e:
        logger.error(f"获取反馈失败: {e}")
        return None


def get_all_feedback(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    has_actual: bool = False
) -> List[dict]:
    """
    获取所有反馈

    Args:
        start_date: 开始日期
        end_date: 结束日期
        has_actual: 只返回有实际灌水量的反馈

    Returns:
        反馈列表
    """
    try:
        feedbacks = []

        for file in FEEDBACK_DIR.glob("*.json"):
            date = file.stem

            # 日期过滤
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue

            with open(file, 'r', encoding='utf-8') as f:
                feedback = json.load(f)

            # 过滤有实际灌水量的
            if has_actual:
                latest = feedback.get("latest", {})
                if not latest.get("actual_irrigation"):
                    continue

            feedbacks.append(feedback)

        return sorted(feedbacks, key=lambda x: x.get("date", ""), reverse=True)

    except Exception as e:
        logger.error(f"获取反馈列表失败: {e}")
        return []


def get_feedback_stats() -> dict:
    """
    获取反馈统计

    Returns:
        统计数据
    """
    try:
        feedbacks = get_all_feedback()

        total = len(feedbacks)
        with_actual = 0
        total_rating = 0
        rating_count = 0
        irrigation_diffs = []

        for fb in feedbacks:
            latest = fb.get("latest", {})

            if latest.get("actual_irrigation"):
                with_actual += 1

                # 计算预测与实际的差异
                date = fb.get("date")
                episode = get_episode_by_date(date)
                if episode:
                    predicted = episode.get("irrigation_amount", 0)
                    actual = latest["actual_irrigation"]
                    irrigation_diffs.append(abs(predicted - actual))

            if latest.get("rating"):
                total_rating += latest["rating"]
                rating_count += 1

        avg_rating = total_rating / rating_count if rating_count > 0 else 0
        avg_diff = sum(irrigation_diffs) / len(irrigation_diffs) if irrigation_diffs else 0

        return {
            "total_feedback": total,
            "with_actual_irrigation": with_actual,
            "average_rating": round(avg_rating, 2),
            "rating_count": rating_count,
            "average_prediction_diff": round(avg_diff, 2)
        }

    except Exception as e:
        logger.error(f"获取反馈统计失败: {e}")
        return {}
