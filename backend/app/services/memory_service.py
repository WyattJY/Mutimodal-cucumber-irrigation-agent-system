from __future__ import annotations
# Memory Service - 记忆层封装
"""
记忆层统一封装

职责:
1. 管理 Episode 存储 (L2)
2. 管理 Weekly Summary 存储 (L3)
3. 构建 Working Context (L1)
4. 提供记忆查询接口

支持两种存储后端:
- JSON 文件 (默认)
- MongoDB (可选)
"""

import os
import sys
import json
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

# 添加 src 目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 导入核心模块
try:
    from cucumber_irrigation.memory.episode_store import EpisodeStore
    from cucumber_irrigation.memory.weekly_summary_store import WeeklySummaryStore
    from cucumber_irrigation.models.episode import (
        Episode, EpisodeInputs, EpisodePredictions,
        EpisodeAnomalies, FinalDecision
    )
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"核心记忆模块导入失败: {e}")
    CORE_MODULES_AVAILABLE = False


class MemoryService:
    """
    记忆层统一封装

    提供:
    - Episode CRUD 操作 (L2)
    - Weekly Summary 操作 (L3)
    - Working Context 构建 (L1)
    """

    def __init__(
        self,
        storage_path: str = None,
        use_mongodb: bool = False,
        mongo_uri: str = None
    ):
        """
        初始化记忆服务

        Args:
            storage_path: JSON 存储目录路径
            use_mongodb: 是否使用 MongoDB
            mongo_uri: MongoDB 连接 URI
        """
        self.storage_path = storage_path or str(PROJECT_ROOT / "data" / "storage")
        self.use_mongodb = use_mongodb
        self.mongo_uri = mongo_uri

        # 确保存储目录存在
        os.makedirs(self.storage_path, exist_ok=True)

        # 初始化存储
        self._init_stores()

    def _init_stores(self):
        """初始化存储后端"""
        if not CORE_MODULES_AVAILABLE:
            logger.warning("核心记忆模块不可用，使用简化的本地存储")
            self._use_simple_storage = True
            self._episodes_file = os.path.join(self.storage_path, "episodes.json")
            self._weekly_file = os.path.join(self.storage_path, "weekly_summaries.json")
            return

        self._use_simple_storage = False

        if self.use_mongodb and self.mongo_uri:
            try:
                from pymongo import MongoClient
                mongo_client = MongoClient(self.mongo_uri)
                self.episode_store = EpisodeStore(
                    mongo_client=mongo_client,
                    db_name="cucumber_irrigation",
                    collection_name="episodes"
                )
                self.weekly_store = WeeklySummaryStore(
                    mongo_client=mongo_client,
                    db_name="cucumber_irrigation",
                    collection_name="weekly_summaries"
                )
                logger.info("使用 MongoDB 存储后端")
            except Exception as e:
                logger.warning(f"MongoDB 初始化失败，回退到 JSON 存储: {e}")
                self._init_json_stores()
        else:
            self._init_json_stores()

    def _init_json_stores(self):
        """初始化 JSON 存储"""
        episodes_path = os.path.join(self.storage_path, "episodes.json")
        weekly_path = os.path.join(self.storage_path, "weekly_summaries.json")

        self.episode_store = EpisodeStore(json_path=episodes_path)
        self.weekly_store = WeeklySummaryStore(json_path=weekly_path)
        logger.info(f"使用 JSON 文件存储: {self.storage_path}")

    # =========================================================================
    # L2: Episode 操作
    # =========================================================================

    async def save_episode(self, episode: "Episode") -> str:
        """
        保存 Episode

        Args:
            episode: Episode 对象

        Returns:
            保存的 episode ID (日期)
        """
        if self._use_simple_storage:
            return self._save_episode_simple(episode)

        try:
            return self.episode_store.save(episode)
        except Exception as e:
            logger.error(f"保存 Episode 失败: {e}")
            raise

    async def get_episode(self, date: str) -> Optional["Episode"]:
        """
        获取指定日期的 Episode

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            Episode 对象，不存在返回 None
        """
        if self._use_simple_storage:
            return self._get_episode_simple(date)

        try:
            return self.episode_store.get_by_date(date)
        except Exception as e:
            logger.error(f"获取 Episode 失败: {e}")
            return None

    async def get_recent_episodes(self, days: int = 7) -> List["Episode"]:
        """
        获取最近 N 天的 Episodes

        Args:
            days: 天数

        Returns:
            Episode 列表，按日期降序
        """
        if self._use_simple_storage:
            return self._get_recent_episodes_simple(days)

        try:
            return self.episode_store.get_recent(days)
        except Exception as e:
            logger.error(f"获取最近 Episodes 失败: {e}")
            return []

    async def get_episodes_by_range(
        self,
        start_date: str,
        end_date: str
    ) -> List["Episode"]:
        """
        按日期范围获取 Episodes

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Episode 列表
        """
        if self._use_simple_storage:
            return self._get_episodes_by_range_simple(start_date, end_date)

        try:
            return self.episode_store.get_by_date_range(start_date, end_date)
        except Exception as e:
            logger.error(f"获取日期范围 Episodes 失败: {e}")
            return []

    async def update_episode(self, date: str, updates: dict) -> bool:
        """
        更新 Episode

        Args:
            date: 日期
            updates: 更新内容

        Returns:
            是否更新成功
        """
        try:
            episode = await self.get_episode(date)
            if not episode:
                return False

            # 应用更新
            for key, value in updates.items():
                if hasattr(episode, key):
                    setattr(episode, key, value)

            episode.updated_at = datetime.now().isoformat()
            await self.save_episode(episode)
            return True
        except Exception as e:
            logger.error(f"更新 Episode 失败: {e}")
            return False

    # =========================================================================
    # L3: Weekly Summary 操作
    # =========================================================================

    async def save_weekly_summary(self, summary: dict) -> str:
        """
        保存周摘要

        Args:
            summary: 周摘要数据

        Returns:
            保存的摘要 ID
        """
        if self._use_simple_storage:
            return self._save_weekly_simple(summary)

        try:
            return self.weekly_store.save(summary)
        except Exception as e:
            logger.error(f"保存周摘要失败: {e}")
            raise

    async def get_latest_weekly_summary(self) -> Optional[dict]:
        """
        获取最新的周摘要

        Returns:
            周摘要数据，不存在返回 None
        """
        if self._use_simple_storage:
            return self._get_latest_weekly_simple()

        try:
            return self.weekly_store.get_latest()
        except Exception as e:
            logger.error(f"获取最新周摘要失败: {e}")
            return None

    async def get_weekly_prompt_block(self) -> Optional[str]:
        """
        获取用于注入 Prompt 的周摘要块

        Returns:
            prompt_block 字符串，不存在返回 None
        """
        try:
            summary = await self.get_latest_weekly_summary()
            if summary:
                return summary.get("prompt_block")
            return None
        except Exception as e:
            logger.error(f"获取周摘要 prompt_block 失败: {e}")
            return None

    # =========================================================================
    # L1: Working Context 构建
    # =========================================================================

    def build_working_context(
        self,
        system_prompt: str,
        today_input: dict,
        weekly_context: Optional[str] = None,
        rag_results: Optional[List[str]] = None
    ) -> dict:
        """
        构建工作上下文 (L1)

        Args:
            system_prompt: 系统提示词
            today_input: 今日输入数据
            weekly_context: 周摘要上下文
            rag_results: RAG 检索结果

        Returns:
            工作上下文字典
        """
        context = {
            "system_prompt": system_prompt,
            "today_input": today_input,
            "weekly_context": weekly_context,
            "rag_results": rag_results or [],
            "built_at": datetime.now().isoformat()
        }

        # 构建完整的 system prompt
        full_system = system_prompt

        if weekly_context:
            full_system += f"\n\n<recent_experience>\n{weekly_context}\n</recent_experience>"

        if rag_results:
            rag_text = "\n".join(rag_results)
            full_system += f"\n\n<knowledge_base>\n{rag_text}\n</knowledge_base>"

        context["full_system_prompt"] = full_system

        return context

    # =========================================================================
    # 简化存储实现 (当核心模块不可用时)
    # =========================================================================

    def _load_json_file(self, filepath: str) -> list:
        """加载 JSON 文件"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_json_file(self, filepath: str, data: list):
        """保存 JSON 文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_episode_simple(self, episode) -> str:
        """简化的 Episode 保存"""
        episodes = self._load_json_file(self._episodes_file)

        data = episode.to_dict() if hasattr(episode, 'to_dict') else episode
        data['updated_at'] = datetime.now().isoformat()

        # 查找是否存在
        existing_idx = None
        for i, ep in enumerate(episodes):
            if ep.get('date') == data.get('date'):
                existing_idx = i
                break

        if existing_idx is not None:
            episodes[existing_idx] = data
        else:
            data['created_at'] = datetime.now().isoformat()
            episodes.append(data)

        self._save_json_file(self._episodes_file, episodes)
        return data.get('date', '')

    def _get_episode_simple(self, date: str):
        """简化的 Episode 获取"""
        episodes = self._load_json_file(self._episodes_file)
        for ep in episodes:
            if ep.get('date') == date:
                if CORE_MODULES_AVAILABLE:
                    return Episode.from_dict(ep)
                return ep
        return None

    def _get_recent_episodes_simple(self, days: int):
        """简化的最近 Episodes 获取"""
        episodes = self._load_json_file(self._episodes_file)
        sorted_eps = sorted(episodes, key=lambda x: x.get('date', ''), reverse=True)
        result = sorted_eps[:days]
        if CORE_MODULES_AVAILABLE:
            return [Episode.from_dict(ep) for ep in result]
        return result

    def _get_episodes_by_range_simple(self, start_date: str, end_date: str):
        """简化的日期范围 Episodes 获取"""
        episodes = self._load_json_file(self._episodes_file)
        result = [
            ep for ep in episodes
            if start_date <= ep.get('date', '') <= end_date
        ]
        sorted_result = sorted(result, key=lambda x: x.get('date', ''))
        if CORE_MODULES_AVAILABLE:
            return [Episode.from_dict(ep) for ep in sorted_result]
        return sorted_result

    def _save_weekly_simple(self, summary: dict) -> str:
        """简化的周摘要保存"""
        summaries = self._load_json_file(self._weekly_file)

        summary['created_at'] = datetime.now().isoformat()
        summaries.append(summary)

        self._save_json_file(self._weekly_file, summaries)
        return summary.get('week_start', '')

    def _get_latest_weekly_simple(self) -> Optional[dict]:
        """简化的最新周摘要获取"""
        summaries = self._load_json_file(self._weekly_file)
        if summaries:
            sorted_summaries = sorted(
                summaries,
                key=lambda x: x.get('week_end', ''),
                reverse=True
            )
            return sorted_summaries[0]
        return None


# 创建服务单例
memory_service = MemoryService()
