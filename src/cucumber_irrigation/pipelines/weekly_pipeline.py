"""每周总结管道

生成周摘要和 prompt_block
参考: task1.md P5-02, requirements1.md 4.5节, 8.3节
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger

from ..models import (
    Episode, WeeklySummary, TrendStats, IrrigationStats,
    AnomalyEvent, OverrideSummary
)
from ..memory import (
    EpisodeStore, WeeklySummaryStore, KnowledgeRetriever
)
from ..services import RAGService, LLMService


@dataclass
class WeeklyPipelineConfig:
    """周管道配置"""
    enable_rag: bool = True
    enable_llm_insights: bool = True
    max_prompt_block_tokens: int = 800


@dataclass
class WeeklyPipelineResult:
    """周管道结果"""
    week_start: str
    week_end: str
    summary: WeeklySummary
    prompt_block_tokens: int
    knowledge_references: List[dict]


class WeeklyPipeline:
    """每周总结管道

    流程:
    1. 获取近 7 天 Episodes
    2. 聚合统计
    3. 知识库检索 (Q7)
    4. LLM 生成 key_insights (Q7)
    5. 生成 prompt_block
    6. Token 检查与压缩
    7. 存储 WeeklySummary
    """

    def __init__(
        self,
        episode_store: EpisodeStore,
        weekly_store: WeeklySummaryStore,
        rag_service: Optional[RAGService] = None,
        llm_service: Optional[LLMService] = None,
        config: Optional[WeeklyPipelineConfig] = None
    ):
        """
        初始化管道

        Args:
            episode_store: Episode 存储
            weekly_store: WeeklySummary 存储
            rag_service: RAG 服务
            llm_service: LLM 服务
            config: 配置
        """
        self.episode_store = episode_store
        self.weekly_store = weekly_store
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.config = config or WeeklyPipelineConfig()

    def run(
        self,
        week_end_date: Optional[str] = None,
        season: str = ""
    ) -> WeeklyPipelineResult:
        """
        执行周总结流程

        Args:
            week_end_date: 周结束日期 (默认今天)
            season: 季节标识

        Returns:
            WeeklyPipelineResult
        """
        # 计算周日期范围
        if week_end_date:
            end_date = datetime.strptime(week_end_date, "%Y-%m-%d")
        else:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=6)
        week_start = start_date.strftime("%Y-%m-%d")
        week_end = end_date.strftime("%Y-%m-%d")

        logger.info(f"开始周总结: {week_start} ~ {week_end}")

        # Step 1: 获取近 7 天 Episodes
        episodes = self._get_week_episodes(week_start, week_end)
        logger.debug(f"获取到 {len(episodes)} 个 Episodes")

        # Step 2: 聚合统计
        trend_stats = self._aggregate_trend_stats(episodes)
        irrigation_stats = self._aggregate_irrigation_stats(episodes)
        anomaly_events = self._aggregate_anomaly_events(episodes)
        override_summary = self._aggregate_overrides(episodes)
        dominant_stage = self._get_dominant_stage(episodes)

        logger.debug(f"统计完成: trend={trend_stats.dominant_trend}, avg_irrigation={irrigation_stats.daily_avg:.2f}")

        # Step 3: 知识库检索 (Q7)
        knowledge_refs = []
        if self.config.enable_rag and self.rag_service:
            knowledge_refs = self._retrieve_weekly_knowledge(
                dominant_stage, anomaly_events
            )

        # Step 4: 生成 key_insights
        if self.config.enable_llm_insights and self.llm_service:
            key_insights = self._generate_insights_with_llm(
                episodes, trend_stats, irrigation_stats,
                anomaly_events, knowledge_refs
            )
        else:
            key_insights = self._generate_insights_simple(
                trend_stats, irrigation_stats, anomaly_events
            )

        # Step 5-6: 创建 WeeklySummary (自动生成和压缩 prompt_block)
        summary = WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            season=season,
            trend_stats=trend_stats,
            irrigation_stats=irrigation_stats,
            anomaly_events=anomaly_events,
            override_summary=override_summary,
            key_insights=key_insights,
            knowledge_references=[
                {"doc_id": r.doc_id, "source": r.source}
                for r in knowledge_refs
            ] if knowledge_refs else []
        )

        # Step 7: 存储 (WeeklySummaryStore.save 会自动生成 prompt_block)
        self.weekly_store.save(summary)
        logger.info(f"周总结已存储: prompt_block_tokens={summary.prompt_block_tokens}")

        return WeeklyPipelineResult(
            week_start=week_start,
            week_end=week_end,
            summary=summary,
            prompt_block_tokens=summary.prompt_block_tokens,
            knowledge_references=summary.knowledge_references
        )

    def _get_week_episodes(
        self,
        week_start: str,
        week_end: str
    ) -> List[Episode]:
        """获取一周的 Episodes"""
        return self.episode_store.get_by_date_range(week_start, week_end)

    def _aggregate_trend_stats(self, episodes: List[Episode]) -> TrendStats:
        """聚合趋势统计"""
        better = same = worse = 0

        for ep in episodes:
            pr = ep.predictions.plant_response
            if isinstance(pr, dict):
                trend = pr.get("trend", "same")
            else:
                trend = "same"

            if trend == "better":
                better += 1
            elif trend == "worse":
                worse += 1
            else:
                same += 1

        # 确定主导趋势
        if better > worse and better > same:
            dominant = "better"
        elif worse > better and worse > same:
            dominant = "worse"
        else:
            dominant = "same"

        return TrendStats(
            better_days=better,
            same_days=same,
            worse_days=worse,
            dominant_trend=dominant
        )

    def _aggregate_irrigation_stats(self, episodes: List[Episode]) -> IrrigationStats:
        """聚合灌溉统计"""
        values = [
            ep.final_decision.value
            for ep in episodes
            if ep.final_decision.value > 0
        ]

        if not values:
            return IrrigationStats()

        total = sum(values)
        daily_avg = total / len(values)
        max_val = max(values)
        min_val = min(values)

        # 判断趋势 (前半周 vs 后半周)
        mid = len(values) // 2
        if mid > 0 and len(values) > mid:
            first_half_avg = sum(values[:mid]) / mid
            second_half_avg = sum(values[mid:]) / (len(values) - mid)
            if second_half_avg > first_half_avg * 1.1:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return IrrigationStats(
            total=total,
            daily_avg=daily_avg,
            max_value=max_val,
            min_value=min_val,
            trend=trend
        )

    def _aggregate_anomaly_events(self, episodes: List[Episode]) -> List[AnomalyEvent]:
        """聚合异常事件"""
        events = []

        for ep in episodes:
            if ep.anomalies.out_of_range:
                events.append(AnomalyEvent(
                    date=ep.date,
                    anomaly_type="out_of_range",
                    severity="moderate"
                ))

            if ep.anomalies.trend_conflict:
                severity = ep.anomalies.trend_conflict_severity
                if severity in ("severe", "SEVERE"):
                    sev = "severe"
                elif severity in ("moderate", "MODERATE"):
                    sev = "moderate"
                else:
                    sev = "minor"
                events.append(AnomalyEvent(
                    date=ep.date,
                    anomaly_type="trend_conflict",
                    severity=sev
                ))

            if ep.anomalies.env_anomaly:
                events.append(AnomalyEvent(
                    date=ep.date,
                    anomaly_type=ep.anomalies.env_anomaly_type or "env_anomaly",
                    severity="moderate"
                ))

        return events

    def _aggregate_overrides(self, episodes: List[Episode]) -> OverrideSummary:
        """聚合覆盖统计"""
        override_count = 0
        total_delta = 0.0
        reasons = []

        for ep in episodes:
            if ep.final_decision.source == "override":
                override_count += 1
                if ep.predictions.tsmixer_raw:
                    delta = ep.final_decision.value - ep.predictions.tsmixer_raw
                    total_delta += delta
                if ep.final_decision.override_reason:
                    reasons.append(ep.final_decision.override_reason)

        return OverrideSummary(
            count=override_count,
            total_delta=total_delta,
            reasons=reasons[:3]  # 只保留前3个理由
        )

    def _get_dominant_stage(self, episodes: List[Episode]) -> Optional[str]:
        """获取主要生育期"""
        stages = {}
        for ep in episodes:
            stage = ep.predictions.growth_stage
            if stage:
                stages[stage] = stages.get(stage, 0) + 1

        if stages:
            return max(stages, key=stages.get)
        return None

    def _retrieve_weekly_knowledge(
        self,
        dominant_stage: Optional[str],
        anomaly_events: List[AnomalyEvent]
    ) -> list:
        """检索周度知识"""
        results = []

        # 生育期知识
        if dominant_stage and self.rag_service:
            stage_results = self.rag_service.search_for_growth_stage(
                dominant_stage, top_k=2
            )
            results.extend(stage_results)

        # 异常相关知识
        severe_anomalies = [e for e in anomaly_events if e.severity == "severe"]
        if severe_anomalies and self.rag_service:
            for anomaly in severe_anomalies[:2]:
                anomaly_results = self.rag_service.search_for_anomaly(
                    anomaly_type=anomaly.anomaly_type,
                    growth_stage=dominant_stage
                )
                results.extend(anomaly_results[:1])

        return results

    def _generate_insights_with_llm(
        self,
        episodes: List[Episode],
        trend_stats: TrendStats,
        irrigation_stats: IrrigationStats,
        anomaly_events: List[AnomalyEvent],
        knowledge_refs: list
    ) -> List[str]:
        """使用 LLM 生成 key_insights"""
        if not self.llm_service:
            logger.warning("LLM 服务未配置，使用简单生成")
            return self._generate_insights_simple(
                trend_stats, irrigation_stats, anomaly_events
            )

        # 准备 Episodes 摘要
        episodes_summary = []
        for ep in episodes:
            pr = ep.predictions.plant_response
            trend = pr.get("trend", "same") if isinstance(pr, dict) else "same"
            episodes_summary.append({
                "date": ep.date,
                "irrigation": ep.final_decision.value,
                "trend": trend
            })

        # 准备知识库引用
        knowledge_refs_dict = []
        if knowledge_refs:
            for ref in knowledge_refs:
                if hasattr(ref, 'content'):
                    knowledge_refs_dict.append({
                        "source": getattr(ref, 'source', 'FAO56'),
                        "snippet": ref.content[:200] if ref.content else ""
                    })

        # 调用 LLM
        try:
            insights = self.llm_service.generate_weekly_insights(
                episodes_summary=episodes_summary,
                trend_stats={
                    "better_days": trend_stats.better_days,
                    "same_days": trend_stats.same_days,
                    "worse_days": trend_stats.worse_days,
                    "dominant_trend": trend_stats.dominant_trend
                },
                irrigation_stats={
                    "total": irrigation_stats.total,
                    "daily_avg": irrigation_stats.daily_avg,
                    "trend": irrigation_stats.trend
                },
                anomaly_events=[
                    {"date": e.date, "anomaly_type": e.anomaly_type, "severity": e.severity}
                    for e in anomaly_events
                ],
                knowledge_refs=knowledge_refs_dict
            )
            logger.info(f"LLM 生成 {len(insights)} 条洞察")
            return insights

        except Exception as e:
            logger.error(f"LLM 生成洞察失败: {e}")
            return self._generate_insights_simple(
                trend_stats, irrigation_stats, anomaly_events
            )

    def _generate_insights_simple(
        self,
        trend_stats: TrendStats,
        irrigation_stats: IrrigationStats,
        anomaly_events: List[AnomalyEvent]
    ) -> List[str]:
        """简单生成 key_insights"""
        insights = []

        # 趋势洞察
        trend_map = {"better": "好转", "same": "平稳", "worse": "下降"}
        trend_cn = trend_map.get(trend_stats.dominant_trend, "未知")
        insights.append(f"本周长势{trend_cn} ({trend_stats.better_days}好/{trend_stats.same_days}平/{trend_stats.worse_days}差)")

        # 灌溉洞察
        irr_trend_map = {"increasing": "上升", "stable": "稳定", "decreasing": "下降"}
        irr_trend_cn = irr_trend_map.get(irrigation_stats.trend, "稳定")
        insights.append(f"灌水量{irr_trend_cn}，日均 {irrigation_stats.daily_avg:.1f} L/m²")

        # 异常洞察
        severe_count = len([e for e in anomaly_events if e.severity == "severe"])
        if severe_count > 0:
            insights.append(f"本周发生 {severe_count} 次严重异常，需持续关注")
        elif anomaly_events:
            insights.append(f"本周 {len(anomaly_events)} 次轻微异常")

        return insights
