from __future__ import annotations
# Weekly Summary Service - 周报生成服务
"""
周报生成服务

职责:
1. 从 Episode 记录生成周摘要
2. 生成 prompt_block 用于注入 System Prompt
3. 生成关键洞察
4. 保存周摘要到记忆系统
"""

import json
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from app.services.memory_service import memory_service
from app.services.llm_service import llm_service
from app.models.schemas import (
    WeeklyGenerateRequest, WeeklySummaryResult, WeeklyStatistics
)


class WeeklySummaryService:
    """周报生成服务"""

    def __init__(self):
        """初始化服务"""
        pass

    async def generate_weekly_summary(
        self,
        week_start: str,
        week_end: str
    ) -> WeeklySummaryResult:
        """
        生成周摘要

        Args:
            week_start: 周开始日期 (YYYY-MM-DD)
            week_end: 周结束日期 (YYYY-MM-DD)

        Returns:
            WeeklySummaryResult: 周摘要结果
        """
        try:
            logger.info(f"开始生成周摘要: {week_start} - {week_end}")

            # 1. 获取该周的 Episodes
            episodes = await memory_service.get_episodes_by_range(week_start, week_end)
            logger.info(f"获取到 {len(episodes)} 条 Episode 记录")

            if not episodes:
                logger.warning(f"周 {week_start} - {week_end} 没有 Episode 记录")
                return self._empty_summary(week_start, week_end)

            # 2. 计算统计数据
            statistics = self._calculate_statistics(episodes)

            # 3. 提取规律和风险触发条件
            patterns = self._extract_patterns(episodes)
            risk_triggers = self._extract_risk_triggers(episodes)

            # 4. 提取 Override 记录
            overrides = self._extract_overrides(episodes)

            # 5. 生成关键洞察
            insights = await self._generate_insights(
                episodes, statistics, patterns, risk_triggers
            )

            # 6. 生成 prompt_block
            prompt_block = self._generate_prompt_block(
                statistics, patterns, risk_triggers, insights
            )

            # 7. 构建结果
            result = WeeklySummaryResult(
                week_start=week_start,
                week_end=week_end,
                patterns=patterns,
                risk_triggers=risk_triggers,
                overrides=overrides,
                statistics=statistics,
                prompt_block=prompt_block,
                insights=insights
            )

            # 8. 保存周摘要
            await self._save_summary(result)

            logger.info(f"周摘要生成完成: {week_start} - {week_end}")
            return result

        except Exception as e:
            logger.error(f"生成周摘要失败: {e}")
            raise

    def _calculate_statistics(self, episodes: list) -> WeeklyStatistics:
        """计算统计数据"""
        irrigation_values = []
        better_days = 0
        same_days = 0
        worse_days = 0
        override_count = 0

        for ep in episodes:
            # 获取灌水量
            if hasattr(ep, 'final_decision'):
                value = getattr(ep.final_decision, 'value', 0) if hasattr(ep.final_decision, 'value') else ep.final_decision.get('value', 0)
                source = getattr(ep.final_decision, 'source', 'tsmixer') if hasattr(ep.final_decision, 'source') else ep.final_decision.get('source', 'tsmixer')
            else:
                value = ep.get('final_decision', {}).get('value', 0)
                source = ep.get('final_decision', {}).get('source', 'tsmixer')

            irrigation_values.append(value)

            if source == 'override':
                override_count += 1

            # 获取趋势
            if hasattr(ep, 'predictions'):
                plant_response = getattr(ep.predictions, 'plant_response', {}) if hasattr(ep.predictions, 'plant_response') else ep.predictions.get('plant_response', {})
            else:
                plant_response = ep.get('predictions', {}).get('plant_response', {})

            trend = plant_response.get('trend') if isinstance(plant_response, dict) else None

            if trend == 'better':
                better_days += 1
            elif trend == 'worse':
                worse_days += 1
            else:
                same_days += 1

        # 计算统计值
        avg_irrigation = sum(irrigation_values) / len(irrigation_values) if irrigation_values else 0
        max_irrigation = max(irrigation_values) if irrigation_values else 0
        min_irrigation = min(irrigation_values) if irrigation_values else 0
        override_rate = override_count / len(episodes) if episodes else 0

        return WeeklyStatistics(
            avg_irrigation=round(avg_irrigation, 2),
            max_irrigation=round(max_irrigation, 2),
            min_irrigation=round(min_irrigation, 2),
            override_rate=round(override_rate, 2),
            better_days=better_days,
            same_days=same_days,
            worse_days=worse_days
        )

    def _extract_patterns(self, episodes: list) -> List[str]:
        """提取规律"""
        patterns = []

        # 分析趋势连续性
        trends = []
        for ep in episodes:
            if hasattr(ep, 'predictions'):
                plant_response = getattr(ep.predictions, 'plant_response', {}) if hasattr(ep.predictions, 'plant_response') else ep.predictions.get('plant_response', {})
            else:
                plant_response = ep.get('predictions', {}).get('plant_response', {})
            trend = plant_response.get('trend') if isinstance(plant_response, dict) else 'same'
            trends.append(trend)

        # 检查连续趋势
        consecutive_same = 0
        max_consecutive_same = 0
        for trend in trends:
            if trend == 'same':
                consecutive_same += 1
                max_consecutive_same = max(max_consecutive_same, consecutive_same)
            else:
                consecutive_same = 0

        if max_consecutive_same >= 3:
            patterns.append(f"连续 {max_consecutive_same} 天长势稳定")

        # 检查灌水量变化规律
        irrigation_values = []
        for ep in episodes:
            if hasattr(ep, 'final_decision'):
                value = getattr(ep.final_decision, 'value', 0) if hasattr(ep.final_decision, 'value') else ep.final_decision.get('value', 0)
            else:
                value = ep.get('final_decision', {}).get('value', 0)
            irrigation_values.append(value)

        if len(irrigation_values) >= 2:
            if all(irrigation_values[i] <= irrigation_values[i+1] for i in range(len(irrigation_values)-1)):
                patterns.append("灌水量呈上升趋势")
            elif all(irrigation_values[i] >= irrigation_values[i+1] for i in range(len(irrigation_values)-1)):
                patterns.append("灌水量呈下降趋势")

        if not patterns:
            patterns.append("本周灌溉模式正常")

        return patterns

    def _extract_risk_triggers(self, episodes: list) -> List[str]:
        """提取风险触发条件"""
        triggers = []

        for ep in episodes:
            date = ep.date if hasattr(ep, 'date') else ep.get('date', '')

            # 检查异常
            if hasattr(ep, 'anomalies'):
                anomalies = ep.anomalies
                if hasattr(anomalies, 'env_anomaly') and anomalies.env_anomaly:
                    anomaly_type = getattr(anomalies, 'env_anomaly_type', '环境异常')
                    triggers.append(f"{date}: {anomaly_type}")
            else:
                anomalies = ep.get('anomalies', {})
                if anomalies.get('env_anomaly'):
                    triggers.append(f"{date}: {anomalies.get('env_anomaly_type', '环境异常')}")

            # 检查长势异常
            if hasattr(ep, 'predictions'):
                plant_response = getattr(ep.predictions, 'plant_response', {}) if hasattr(ep.predictions, 'plant_response') else ep.predictions.get('plant_response', {})
            else:
                plant_response = ep.get('predictions', {}).get('plant_response', {})

            if isinstance(plant_response, dict):
                abnormalities = plant_response.get('abnormalities', {})
                if abnormalities:
                    for key, value in abnormalities.items():
                        if value in ['moderate', 'severe']:
                            triggers.append(f"{date}: {key} 异常 ({value})")

        return triggers[:5]  # 限制返回数量

    def _extract_overrides(self, episodes: list) -> List[dict]:
        """提取 Override 记录"""
        overrides = []

        for ep in episodes:
            if hasattr(ep, 'final_decision'):
                source = getattr(ep.final_decision, 'source', 'tsmixer') if hasattr(ep.final_decision, 'source') else ep.final_decision.get('source', 'tsmixer')
                if source == 'override':
                    overrides.append({
                        'date': ep.date if hasattr(ep, 'date') else ep.get('date', ''),
                        'reason': getattr(ep.final_decision, 'override_reason', '') if hasattr(ep.final_decision, 'override_reason') else ep.final_decision.get('override_reason', '')
                    })
            else:
                if ep.get('final_decision', {}).get('source') == 'override':
                    overrides.append({
                        'date': ep.get('date', ''),
                        'reason': ep.get('final_decision', {}).get('override_reason', '')
                    })

        return overrides

    async def _generate_insights(
        self,
        episodes: list,
        statistics: WeeklyStatistics,
        patterns: List[str],
        risk_triggers: List[str]
    ) -> List[str]:
        """生成关键洞察"""
        try:
            # 构建 episodes 摘要
            episodes_summary = []
            for ep in episodes:
                date = ep.date if hasattr(ep, 'date') else ep.get('date', '')
                if hasattr(ep, 'final_decision'):
                    irrigation = getattr(ep.final_decision, 'value', 0) if hasattr(ep.final_decision, 'value') else ep.final_decision.get('value', 0)
                else:
                    irrigation = ep.get('final_decision', {}).get('value', 0)

                if hasattr(ep, 'predictions'):
                    plant_response = getattr(ep.predictions, 'plant_response', {}) if hasattr(ep.predictions, 'plant_response') else ep.predictions.get('plant_response', {})
                else:
                    plant_response = ep.get('predictions', {}).get('plant_response', {})

                trend = plant_response.get('trend', 'same') if isinstance(plant_response, dict) else 'same'

                episodes_summary.append({
                    'date': date,
                    'irrigation': irrigation,
                    'trend': trend
                })

            # 构建统计
            trend_stats = {
                'better_days': statistics.better_days,
                'same_days': statistics.same_days,
                'worse_days': statistics.worse_days,
                'dominant_trend': 'better' if statistics.better_days > max(statistics.same_days, statistics.worse_days) else (
                    'worse' if statistics.worse_days > statistics.same_days else 'same'
                )
            }

            irrigation_stats = {
                'total': statistics.avg_irrigation * len(episodes),
                'daily_avg': statistics.avg_irrigation,
                'trend': 'stable'
            }

            anomaly_events = [{'date': t.split(':')[0], 'anomaly_type': t.split(':')[1] if ':' in t else t, 'severity': 'moderate'} for t in risk_triggers]

            # 使用 LLM 生成洞察
            insights = await self._call_llm_for_insights(
                episodes_summary, trend_stats, irrigation_stats, anomaly_events
            )

            return insights

        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            return self._fallback_insights(statistics)

    async def _call_llm_for_insights(
        self,
        episodes_summary: list,
        trend_stats: dict,
        irrigation_stats: dict,
        anomaly_events: list
    ) -> List[str]:
        """调用 LLM 生成洞察"""
        try:
            # 使用 src 中的 LLMService (如果可用)
            from cucumber_irrigation.services.llm_service import LLMService as CoreLLMService
            import os

            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                return self._fallback_insights_from_stats(trend_stats, irrigation_stats)

            core_llm = CoreLLMService(api_key=api_key)
            return core_llm.generate_weekly_insights(
                episodes_summary=episodes_summary,
                trend_stats=trend_stats,
                irrigation_stats=irrigation_stats,
                anomaly_events=anomaly_events
            )
        except Exception as e:
            logger.warning(f"LLM 生成洞察失败: {e}")
            return self._fallback_insights_from_stats(trend_stats, irrigation_stats)

    def _fallback_insights(self, statistics: WeeklyStatistics) -> List[str]:
        """回退的简单洞察生成"""
        insights = []

        if statistics.better_days > statistics.worse_days:
            insights.append(f"本周长势良好，好转天数 {statistics.better_days} 天")
        elif statistics.worse_days > statistics.better_days:
            insights.append(f"本周长势需关注，下降天数 {statistics.worse_days} 天")
        else:
            insights.append(f"本周长势稳定，平稳天数 {statistics.same_days} 天")

        insights.append(f"日均灌水 {statistics.avg_irrigation:.1f} L/m²")

        return insights

    def _fallback_insights_from_stats(self, trend_stats: dict, irrigation_stats: dict) -> List[str]:
        """基于统计数据生成回退洞察"""
        insights = []
        trend_map = {"better": "好转", "same": "平稳", "worse": "下降"}
        trend_cn = trend_map.get(trend_stats.get("dominant_trend", "same"), "未知")
        insights.append(f"本周长势{trend_cn}，日均灌水 {irrigation_stats.get('daily_avg', 0):.1f} L/m²")
        return insights

    def _generate_prompt_block(
        self,
        statistics: WeeklyStatistics,
        patterns: List[str],
        risk_triggers: List[str],
        insights: List[str]
    ) -> str:
        """生成用于注入 System Prompt 的摘要块"""
        parts = []

        # 统计摘要
        parts.append(f"过去一周灌水统计: 日均 {statistics.avg_irrigation:.1f} L/m², 范围 {statistics.min_irrigation:.1f}-{statistics.max_irrigation:.1f} L/m²")

        # 趋势分布
        parts.append(f"长势分布: 好转 {statistics.better_days} 天, 平稳 {statistics.same_days} 天, 下降 {statistics.worse_days} 天")

        # 规律
        if patterns:
            parts.append(f"发现规律: {'; '.join(patterns)}")

        # 风险提示
        if risk_triggers:
            parts.append(f"风险事件: {'; '.join(risk_triggers[:3])}")

        # 关键洞察
        if insights:
            parts.append(f"关键洞察: {insights[0]}")

        return "\n".join(parts)

    async def _save_summary(self, result: WeeklySummaryResult):
        """保存周摘要"""
        try:
            summary_data = {
                'week_start': result.week_start,
                'week_end': result.week_end,
                'patterns': result.patterns,
                'risk_triggers': result.risk_triggers,
                'overrides': result.overrides,
                'statistics': result.statistics.model_dump(),
                'prompt_block': result.prompt_block,
                'insights': result.insights,
                'created_at': datetime.now().isoformat()
            }
            await memory_service.save_weekly_summary(summary_data)
            logger.info(f"周摘要已保存: {result.week_start} - {result.week_end}")
        except Exception as e:
            logger.error(f"保存周摘要失败: {e}")

    def _empty_summary(self, week_start: str, week_end: str) -> WeeklySummaryResult:
        """返回空周摘要"""
        return WeeklySummaryResult(
            week_start=week_start,
            week_end=week_end,
            patterns=[],
            risk_triggers=[],
            overrides=[],
            statistics=WeeklyStatistics(
                avg_irrigation=0,
                max_irrigation=0,
                min_irrigation=0,
                override_rate=0,
                better_days=0,
                same_days=0,
                worse_days=0
            ),
            prompt_block="本周暂无数据",
            insights=["本周暂无 Episode 记录"]
        )


# 创建服务单例
weekly_summary_service = WeeklySummaryService()
