from __future__ import annotations
"""L3 周摘要存储

周摘要的存储与检索，包含 prompt_block 生成和压缩
参考: task1.md P3-05, requirements1.md 4.5节
"""

from typing import Optional, List
from datetime import datetime
import json
import os

from ..models.weekly_summary import WeeklySummary, AnomalyEvent
from ..utils.token_counter import TokenCounter


class WeeklySummaryStore:
    """L3 周摘要存储

    支持两种存储后端:
    1. MongoDB (生产环境)
    2. JSON 文件 (开发/测试环境)

    主要功能:
    - 保存周摘要
    - 获取最新周摘要
    - prompt_block 生成与压缩
    """

    # prompt_block 最大 token 数
    MAX_PROMPT_BLOCK_TOKENS = 800

    def __init__(
        self,
        mongo_client=None,
        db_name: str = "cucumber_irrigation",
        collection_name: str = "weekly_summaries",
        json_path: Optional[str] = None,
        token_counter: Optional[TokenCounter] = None
    ):
        """
        初始化存储

        Args:
            mongo_client: MongoDB 客户端 (可选)
            db_name: 数据库名
            collection_name: 集合名
            json_path: JSON 文件路径 (用于文件存储模式)
            token_counter: Token 计数器
        """
        self.mongo_client = mongo_client
        self.db_name = db_name
        self.collection_name = collection_name
        self.json_path = json_path
        self.token_counter = token_counter or TokenCounter()

        # 根据配置选择存储后端
        if mongo_client:
            self.db = mongo_client[db_name]
            self.collection = self.db[collection_name]
            self._ensure_indexes()
            self._storage_mode = "mongodb"
        else:
            self._storage_mode = "json"
            self._json_cache: List[dict] = []
            if json_path:
                self._load_json()

    def _ensure_indexes(self):
        """创建 MongoDB 索引"""
        if self._storage_mode == "mongodb":
            self.collection.create_index("week_start", unique=True)
            self.collection.create_index("season")
            self.collection.create_index("created_at")

    def _load_json(self):
        """加载 JSON 文件"""
        if self.json_path and os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._json_cache = json.load(f)
        else:
            self._json_cache = []

    def _save_json(self):
        """保存到 JSON 文件"""
        if self.json_path:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self._json_cache, f, ensure_ascii=False, indent=2)

    def generate_prompt_block(self, summary: WeeklySummary) -> str:
        """
        生成 prompt_block

        优先级:
        1. key_insights (必须保留)
        2. dominant_trend + irrigation_trend
        3. anomaly_events 摘要
        4. override_summary

        Args:
            summary: 周摘要对象

        Returns:
            生成的 prompt_block
        """
        parts = []

        # 标题
        header = f"## 上周经验 ({summary.week_start} ~ {summary.week_end})"
        parts.append(header)

        # 趋势概述
        trend_text = self._format_trends(summary)
        if trend_text:
            parts.append(trend_text)

        # 关键洞察
        if summary.key_insights:
            parts.append("关键洞察:")
            for insight in summary.key_insights:
                parts.append(f"- {insight}")

        # 异常事件
        anomaly_text = self._format_anomalies(summary.anomaly_events)
        if anomaly_text:
            parts.append(anomaly_text)

        # 覆盖总结
        override_text = self._format_override(summary.override_summary)
        if override_text:
            parts.append(override_text)

        return "\n".join(parts)

    def _format_trends(self, summary: WeeklySummary) -> str:
        """格式化趋势信息"""
        parts = []

        # 长势趋势
        trend_map = {
            "better": "向好",
            "same": "平稳",
            "worse": "恶化"
        }
        trend_cn = trend_map.get(summary.trend_stats.dominant_trend, "未知")
        parts.append(f"长势趋势: {trend_cn}")

        # 灌溉趋势
        irr_trend_map = {
            "increasing": "上升",
            "stable": "稳定",
            "decreasing": "下降"
        }
        irr_trend_cn = irr_trend_map.get(summary.irrigation_stats.trend, "稳定")
        parts.append(f"灌溉趋势: {irr_trend_cn} (日均 {summary.irrigation_stats.daily_avg:.1f} L/m²)")

        return " | ".join(parts)

    def _format_anomalies(self, events: List[AnomalyEvent]) -> str:
        """格式化异常事件"""
        if not events:
            return ""

        severe_events = [e for e in events if e.severity == "severe"]
        if severe_events:
            texts = [f"{e.date}: {e.anomaly_type}" for e in severe_events[:3]]
            return f"重要异常: {', '.join(texts)}"

        if events:
            return f"本周异常 {len(events)} 次"

        return ""

    def _format_override(self, override) -> str:
        """格式化覆盖总结"""
        if override.count == 0:
            return ""
        return f"人工覆盖 {override.count} 次，调整量 {override.total_delta:+.1f} L/m²"

    def compress_prompt_block(
        self,
        summary: WeeklySummary,
        max_tokens: int = None
    ) -> tuple[str, int]:
        """
        压缩 prompt_block 到预算内

        超限压缩策略:
        1. 删除 override_summary
        2. 只保留 severe 级别异常
        3. 只保留前3条 key_insights
        4. 如仍超限，只保留第1条

        Args:
            summary: 周摘要对象
            max_tokens: 最大 token 数

        Returns:
            (压缩后的 prompt_block, token 数)
        """
        max_tokens = max_tokens or self.MAX_PROMPT_BLOCK_TOKENS

        # 生成完整 prompt_block
        prompt_block = self.generate_prompt_block(summary)
        tokens = self.token_counter.count(prompt_block)

        if tokens <= max_tokens:
            return prompt_block, tokens

        # 压缩策略 1: 删除 override_summary
        compressed_summary = WeeklySummary(
            week_start=summary.week_start,
            week_end=summary.week_end,
            season=summary.season,
            trend_stats=summary.trend_stats,
            irrigation_stats=summary.irrigation_stats,
            anomaly_events=summary.anomaly_events,
            override_summary=None,  # 删除
            key_insights=summary.key_insights,
            knowledge_references=summary.knowledge_references
        )
        # 重新格式化不含 override
        prompt_block = self._generate_without_override(compressed_summary)
        tokens = self.token_counter.count(prompt_block)

        if tokens <= max_tokens:
            return prompt_block, tokens

        # 压缩策略 2: 只保留 severe 异常
        severe_events = [e for e in summary.anomaly_events if e.severity == "severe"]
        prompt_block = self._generate_compressed(
            summary,
            key_insights=summary.key_insights,
            anomaly_events=severe_events,
            include_override=False
        )
        tokens = self.token_counter.count(prompt_block)

        if tokens <= max_tokens:
            return prompt_block, tokens

        # 压缩策略 3: 只保留前3条 key_insights
        prompt_block = self._generate_compressed(
            summary,
            key_insights=summary.key_insights[:3],
            anomaly_events=[],
            include_override=False
        )
        tokens = self.token_counter.count(prompt_block)

        if tokens <= max_tokens:
            return prompt_block, tokens

        # 压缩策略 4: 只保留第1条 key_insight
        prompt_block = self._generate_minimal(summary)
        tokens = self.token_counter.count(prompt_block)

        return prompt_block, tokens

    def _generate_without_override(self, summary: WeeklySummary) -> str:
        """生成不含 override 的 prompt_block"""
        parts = [f"## 上周经验 ({summary.week_start} ~ {summary.week_end})"]

        trend_text = self._format_trends(summary)
        if trend_text:
            parts.append(trend_text)

        if summary.key_insights:
            parts.append("关键洞察:")
            for insight in summary.key_insights:
                parts.append(f"- {insight}")

        anomaly_text = self._format_anomalies(summary.anomaly_events)
        if anomaly_text:
            parts.append(anomaly_text)

        return "\n".join(parts)

    def _generate_compressed(
        self,
        summary: WeeklySummary,
        key_insights: List[str],
        anomaly_events: List[AnomalyEvent],
        include_override: bool = False
    ) -> str:
        """生成压缩版 prompt_block"""
        parts = [f"## 上周经验 ({summary.week_start} ~ {summary.week_end})"]

        trend_text = self._format_trends(summary)
        if trend_text:
            parts.append(trend_text)

        if key_insights:
            parts.append("关键洞察:")
            for insight in key_insights:
                parts.append(f"- {insight}")

        anomaly_text = self._format_anomalies(anomaly_events)
        if anomaly_text:
            parts.append(anomaly_text)

        if include_override:
            override_text = self._format_override(summary.override_summary)
            if override_text:
                parts.append(override_text)

        return "\n".join(parts)

    def _generate_minimal(self, summary: WeeklySummary) -> str:
        """生成最小版 prompt_block (只含第一条 insight)"""
        parts = [f"## 上周经验 ({summary.week_start} ~ {summary.week_end})"]

        if summary.key_insights:
            parts.append(f"- {summary.key_insights[0]}")

        return "\n".join(parts)

    def save(self, summary: WeeklySummary) -> str:
        """
        保存周摘要

        自动生成和压缩 prompt_block

        Args:
            summary: 周摘要对象

        Returns:
            保存的周摘要 ID (week_start)
        """
        now = datetime.now().isoformat()

        # 生成并压缩 prompt_block
        prompt_block, tokens = self.compress_prompt_block(summary)
        summary.prompt_block = prompt_block
        summary.prompt_block_tokens = tokens

        # 设置时间戳
        if not summary.created_at:
            summary.created_at = now
        summary.updated_at = now

        data = summary.to_dict()

        if self._storage_mode == "mongodb":
            self.collection.update_one(
                {"week_start": summary.week_start},
                {"$set": data},
                upsert=True
            )
        else:
            existing_idx = None
            for i, ws in enumerate(self._json_cache):
                if ws.get("week_start") == summary.week_start:
                    existing_idx = i
                    break

            if existing_idx is not None:
                self._json_cache[existing_idx] = data
            else:
                self._json_cache.append(data)

            self._save_json()

        return summary.week_start

    def get_latest(self) -> Optional[WeeklySummary]:
        """
        获取最新周摘要

        Returns:
            最新的 WeeklySummary，不存在返回 None
        """
        if self._storage_mode == "mongodb":
            data = self.collection.find_one(
                {},
                sort=[("week_start", -1)]
            )
            if data:
                data.pop("_id", None)
                return WeeklySummary.from_dict(data)
            return None
        else:
            if not self._json_cache:
                return None
            sorted_cache = sorted(
                self._json_cache,
                key=lambda x: x.get("week_start", ""),
                reverse=True
            )
            return WeeklySummary.from_dict(sorted_cache[0])

    def get_by_week(self, week_start: str) -> Optional[WeeklySummary]:
        """
        按周起始日期获取摘要

        Args:
            week_start: 周起始日期 (YYYY-MM-DD)

        Returns:
            WeeklySummary 对象
        """
        if self._storage_mode == "mongodb":
            data = self.collection.find_one({"week_start": week_start})
            if data:
                data.pop("_id", None)
                return WeeklySummary.from_dict(data)
            return None
        else:
            for ws in self._json_cache:
                if ws.get("week_start") == week_start:
                    return WeeklySummary.from_dict(ws)
            return None

    def get_recent(self, weeks: int = 4) -> List[WeeklySummary]:
        """
        获取最近 N 周摘要

        Args:
            weeks: 周数

        Returns:
            WeeklySummary 列表，按日期降序
        """
        if self._storage_mode == "mongodb":
            cursor = self.collection.find().sort("week_start", -1).limit(weeks)
            summaries = []
            for data in cursor:
                data.pop("_id", None)
                summaries.append(WeeklySummary.from_dict(data))
            return summaries
        else:
            sorted_cache = sorted(
                self._json_cache,
                key=lambda x: x.get("week_start", ""),
                reverse=True
            )
            return [WeeklySummary.from_dict(ws) for ws in sorted_cache[:weeks]]

    def get_by_season(self, season: str) -> List[WeeklySummary]:
        """
        按季节获取所有周摘要

        Args:
            season: 季节标识 (如 spring_2025)

        Returns:
            该季节所有周摘要
        """
        if self._storage_mode == "mongodb":
            cursor = self.collection.find({"season": season}).sort("week_start", 1)
            summaries = []
            for data in cursor:
                data.pop("_id", None)
                summaries.append(WeeklySummary.from_dict(data))
            return summaries
        else:
            matches = [
                ws for ws in self._json_cache
                if ws.get("season") == season
            ]
            return [WeeklySummary.from_dict(ws) for ws in sorted(
                matches, key=lambda x: x.get("week_start", "")
            )]

    def count(self) -> int:
        """获取总记录数"""
        if self._storage_mode == "mongodb":
            return self.collection.count_documents({})
        else:
            return len(self._json_cache)

    def delete(self, week_start: str) -> bool:
        """
        删除指定周摘要

        Args:
            week_start: 周起始日期

        Returns:
            是否删除成功
        """
        if self._storage_mode == "mongodb":
            result = self.collection.delete_one({"week_start": week_start})
            return result.deleted_count > 0
        else:
            for i, ws in enumerate(self._json_cache):
                if ws.get("week_start") == week_start:
                    self._json_cache.pop(i)
                    self._save_json()
                    return True
            return False

    def clear(self):
        """清空所有记录 (测试用)"""
        if self._storage_mode == "mongodb":
            self.collection.delete_many({})
        else:
            self._json_cache = []
            if self.json_path and os.path.exists(self.json_path):
                os.remove(self.json_path)
