from __future__ import annotations
"""L2 Episodic Log 存储

每日决策记录的存储与检索
参考: task1.md P3-04, requirements1.md 4.4节
"""

from typing import Optional, List
from datetime import datetime, timedelta
import json
import os

from ..models.episode import Episode


class EpisodeStore:
    """L2 Episodic Log 存储

    支持两种存储后端:
    1. MongoDB (生产环境)
    2. JSON 文件 (开发/测试环境)

    主要功能:
    - 保存每日决策记录
    - 按日期检索
    - 获取最近 N 天记录
    - 检索相似异常案例
    """

    def __init__(
        self,
        mongo_client=None,
        db_name: str = "cucumber_irrigation",
        collection_name: str = "episodes",
        json_path: Optional[str] = None
    ):
        """
        初始化存储

        Args:
            mongo_client: MongoDB 客户端 (可选)
            db_name: 数据库名
            collection_name: 集合名
            json_path: JSON 文件路径 (用于文件存储模式)
        """
        self.mongo_client = mongo_client
        self.db_name = db_name
        self.collection_name = collection_name
        self.json_path = json_path

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
            # 日期唯一索引
            self.collection.create_index("date", unique=True)
            # 复合索引用于异常检索
            self.collection.create_index([
                ("predictions.growth_stage", 1),
                ("anomalies.env_anomaly_type", 1)
            ])
            # 时间索引
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

    def save(self, episode: Episode) -> str:
        """
        保存 Episode

        Args:
            episode: Episode 对象

        Returns:
            保存的 episode ID (日期)
        """
        now = datetime.now().isoformat()

        # 设置时间戳
        if not episode.created_at:
            episode.created_at = now
        episode.updated_at = now

        data = episode.to_dict()

        if self._storage_mode == "mongodb":
            # MongoDB upsert
            self.collection.update_one(
                {"date": episode.date},
                {"$set": data},
                upsert=True
            )
        else:
            # JSON 存储
            existing_idx = None
            for i, ep in enumerate(self._json_cache):
                if ep.get("date") == episode.date:
                    existing_idx = i
                    break

            if existing_idx is not None:
                self._json_cache[existing_idx] = data
            else:
                self._json_cache.append(data)

            self._save_json()

        return episode.date

    def get_by_date(self, date: str) -> Optional[Episode]:
        """
        按日期获取 Episode

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            Episode 对象，不存在返回 None
        """
        if self._storage_mode == "mongodb":
            data = self.collection.find_one({"date": date})
            if data:
                data.pop("_id", None)
                return Episode.from_dict(data)
            return None
        else:
            for ep in self._json_cache:
                if ep.get("date") == date:
                    return Episode.from_dict(ep)
            return None

    def get_recent(self, days: int = 7) -> List[Episode]:
        """
        获取最近 N 天的 Episodes

        Args:
            days: 天数

        Returns:
            Episode 列表，按日期降序
        """
        if self._storage_mode == "mongodb":
            cursor = self.collection.find().sort("date", -1).limit(days)
            episodes = []
            for data in cursor:
                data.pop("_id", None)
                episodes.append(Episode.from_dict(data))
            return episodes
        else:
            # JSON 模式：按日期排序后取最近 N 条
            sorted_cache = sorted(
                self._json_cache,
                key=lambda x: x.get("date", ""),
                reverse=True
            )
            return [Episode.from_dict(ep) for ep in sorted_cache[:days]]

    def get_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Episode]:
        """
        按日期范围获取 Episodes

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            Episode 列表
        """
        if self._storage_mode == "mongodb":
            cursor = self.collection.find({
                "date": {"$gte": start_date, "$lte": end_date}
            }).sort("date", 1)
            episodes = []
            for data in cursor:
                data.pop("_id", None)
                episodes.append(Episode.from_dict(data))
            return episodes
        else:
            episodes = []
            for ep in self._json_cache:
                date = ep.get("date", "")
                if start_date <= date <= end_date:
                    episodes.append(Episode.from_dict(ep))
            return sorted(episodes, key=lambda x: x.date)

    def search_similar_anomaly(
        self,
        anomaly_type: str,
        growth_stage: str,
        limit: int = 5
    ) -> List[Episode]:
        """
        检索相似异常案例

        Args:
            anomaly_type: 异常类型 (high_temp, low_humidity 等)
            growth_stage: 生育期
            limit: 返回数量限制

        Returns:
            相似案例列表
        """
        if self._storage_mode == "mongodb":
            # 优先匹配生育期 + 异常类型
            cursor = self.collection.find({
                "predictions.growth_stage": growth_stage,
                "anomalies.env_anomaly_type": anomaly_type
            }).sort("date", -1).limit(limit)

            episodes = []
            for data in cursor:
                data.pop("_id", None)
                episodes.append(Episode.from_dict(data))

            # 如果结果不足，放宽条件只匹配异常类型
            if len(episodes) < limit:
                cursor = self.collection.find({
                    "anomalies.env_anomaly_type": anomaly_type
                }).sort("date", -1).limit(limit - len(episodes))

                for data in cursor:
                    data.pop("_id", None)
                    ep = Episode.from_dict(data)
                    if ep.date not in [e.date for e in episodes]:
                        episodes.append(ep)

            return episodes
        else:
            # JSON 模式
            exact_matches = []
            type_matches = []

            for ep_data in self._json_cache:
                ep_growth = ep_data.get("predictions", {}).get("growth_stage")
                ep_anomaly = ep_data.get("anomalies", {}).get("env_anomaly_type")

                if ep_anomaly == anomaly_type:
                    if ep_growth == growth_stage:
                        exact_matches.append(ep_data)
                    else:
                        type_matches.append(ep_data)

            # 合并结果
            result_data = exact_matches[:limit]
            remaining = limit - len(result_data)
            if remaining > 0:
                result_data.extend(type_matches[:remaining])

            return [Episode.from_dict(ep) for ep in result_data]

    def search_by_growth_stage(
        self,
        growth_stage: str,
        limit: int = 10
    ) -> List[Episode]:
        """
        按生育期检索

        Args:
            growth_stage: 生育期
            limit: 返回数量限制

        Returns:
            Episode 列表
        """
        if self._storage_mode == "mongodb":
            cursor = self.collection.find({
                "predictions.growth_stage": growth_stage
            }).sort("date", -1).limit(limit)

            episodes = []
            for data in cursor:
                data.pop("_id", None)
                episodes.append(Episode.from_dict(data))
            return episodes
        else:
            matches = [
                ep for ep in self._json_cache
                if ep.get("predictions", {}).get("growth_stage") == growth_stage
            ]
            return [Episode.from_dict(ep) for ep in matches[:limit]]

    def get_with_feedback(self, limit: int = 20) -> List[Episode]:
        """
        获取有用户反馈的 Episodes

        Args:
            limit: 返回数量限制

        Returns:
            有反馈的 Episode 列表
        """
        if self._storage_mode == "mongodb":
            cursor = self.collection.find({
                "$or": [
                    {"user_feedback.actual_irrigation": {"$ne": None}},
                    {"user_feedback.rating": {"$ne": None}}
                ]
            }).sort("date", -1).limit(limit)

            episodes = []
            for data in cursor:
                data.pop("_id", None)
                episodes.append(Episode.from_dict(data))
            return episodes
        else:
            matches = []
            for ep in self._json_cache:
                feedback = ep.get("user_feedback", {})
                if feedback.get("actual_irrigation") or feedback.get("rating"):
                    matches.append(ep)
            return [Episode.from_dict(ep) for ep in matches[:limit]]

    def count(self) -> int:
        """获取总记录数"""
        if self._storage_mode == "mongodb":
            return self.collection.count_documents({})
        else:
            return len(self._json_cache)

    def delete(self, date: str) -> bool:
        """
        删除指定日期的 Episode

        Args:
            date: 日期

        Returns:
            是否删除成功
        """
        if self._storage_mode == "mongodb":
            result = self.collection.delete_one({"date": date})
            return result.deleted_count > 0
        else:
            for i, ep in enumerate(self._json_cache):
                if ep.get("date") == date:
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
