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
from pathlib import Path
from typing import Optional, List, Tuple
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
            date = file.stem  # e.g., "2024-06-14"
            dates.add(date)

    # 从 memory episodes 获取
    for ep in _load_memory_episodes():
        if ep.get('date'):
            dates.add(ep['date'])

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
    if file_path.exists():
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

    # 添加计算字段
    data["irrigation_amount"] = calculate_irrigation(data)
    data["decision_source"] = data.get("final_decision", {}).get("source", "TSMixer")
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

    for date in dates:
        ep = get_episode_by_date(date)
        if ep:
            irrigation_values.append(ep.get("irrigation_amount", 0))
            trends.append(ep.get("response", {}).get("trend", "same"))
        else:
            irrigation_values.append(0)
            trends.append("same")

    return {
        "dates": dates,
        "irrigation": irrigation_values,
        "trends": trends,
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
