"""数据库服务

支持同实例分库访问
参考: task1.md P4-01, requirements1.md 6.1节
"""

from typing import Optional
from pymongo import MongoClient
from loguru import logger


class DBService:
    """MongoDB 数据库服务

    数据库架构:
    - greenhouse_db (只读访问): FAO56 文献片段
    - cucumber_irrigation (业务库): 决策记录、周摘要等

    单例模式确保连接复用
    """

    _instance: Optional["DBService"] = None
    _client: Optional[MongoClient] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017",
        business_db: str = "cucumber_irrigation",
        knowledge_db: str = "greenhouse_db"
    ):
        """
        初始化数据库服务

        Args:
            mongo_uri: MongoDB 连接 URI
            business_db: 业务数据库名
            knowledge_db: 知识库数据库名 (只读)
        """
        if self._client is not None:
            return

        self.mongo_uri = mongo_uri
        self.business_db_name = business_db
        self.knowledge_db_name = knowledge_db

        try:
            self._client = MongoClient(mongo_uri)
            # 测试连接
            self._client.admin.command('ping')
            logger.info(f"MongoDB 连接成功: {mongo_uri}")
        except Exception as e:
            logger.warning(f"MongoDB 连接失败: {e}，将使用本地文件存储")
            self._client = None

    @property
    def client(self) -> Optional[MongoClient]:
        """获取 MongoDB 客户端"""
        return self._client

    @property
    def business_db(self):
        """获取业务数据库"""
        if self._client is None:
            return None
        return self._client[self.business_db_name]

    @property
    def knowledge_db(self):
        """获取知识库数据库 (只读)"""
        if self._client is None:
            return None
        return self._client[self.knowledge_db_name]

    # === 业务库集合 ===

    @property
    def episodes(self):
        """L2 每日决策记录集合"""
        if self.business_db is None:
            return None
        return self.business_db["episodes"]

    @property
    def weekly_summaries(self):
        """L3 周摘要集合"""
        if self.business_db is None:
            return None
        return self.business_db["weekly_summaries"]

    @property
    def overrides(self):
        """人工覆盖记录集合"""
        if self.business_db is None:
            return None
        return self.business_db["overrides"]

    @property
    def learning_events(self):
        """学习事件集合"""
        if self.business_db is None:
            return None
        return self.business_db["learning_events"]

    # === 知识库集合 (只读) ===

    @property
    def literature_chunks(self):
        """FAO56 文献片段集合 (只读)"""
        if self.knowledge_db is None:
            return None
        return self.knowledge_db["literature_chunks"]

    # === 索引管理 ===

    def ensure_indexes(self):
        """创建必要的索引"""
        if self._client is None:
            logger.warning("MongoDB 未连接，跳过索引创建")
            return

        try:
            # episodes 索引
            if self.episodes is not None:
                self.episodes.create_index("date", unique=True)
                self.episodes.create_index("season")
                self.episodes.create_index([
                    ("predictions.growth_stage", 1),
                    ("anomalies.env_anomaly_type", 1)
                ])
                logger.debug("episodes 索引创建完成")

            # weekly_summaries 索引
            if self.weekly_summaries is not None:
                self.weekly_summaries.create_index("week_start", unique=True)
                self.weekly_summaries.create_index("season")
                logger.debug("weekly_summaries 索引创建完成")

            # overrides 索引
            if self.overrides is not None:
                self.overrides.create_index("date")
                self.overrides.create_index([("reason", "text")])
                logger.debug("overrides 索引创建完成")

            # learning_events 索引
            if self.learning_events is not None:
                self.learning_events.create_index("date")
                self.learning_events.create_index("event_type")
                logger.debug("learning_events 索引创建完成")

            logger.info("所有索引创建完成")

        except Exception as e:
            logger.error(f"索引创建失败: {e}")

    # === 健康检查 ===

    def is_connected(self) -> bool:
        """检查数据库连接状态"""
        if self._client is None:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False

    def get_stats(self) -> dict:
        """获取数据库统计信息"""
        stats = {
            "connected": self.is_connected(),
            "business_db": self.business_db_name,
            "knowledge_db": self.knowledge_db_name,
            "collections": {}
        }

        if self.is_connected():
            try:
                if self.episodes is not None:
                    stats["collections"]["episodes"] = self.episodes.count_documents({})
                if self.weekly_summaries is not None:
                    stats["collections"]["weekly_summaries"] = self.weekly_summaries.count_documents({})
                if self.overrides is not None:
                    stats["collections"]["overrides"] = self.overrides.count_documents({})
                if self.literature_chunks is not None:
                    stats["collections"]["literature_chunks"] = self.literature_chunks.count_documents({})
            except Exception as e:
                stats["error"] = str(e)

        return stats

    # === 清理 ===

    def close(self):
        """关闭数据库连接"""
        if self._client is not None:
            self._client.close()
            self._client = None
            DBService._instance = None
            logger.info("MongoDB 连接已关闭")

    @classmethod
    def reset(cls):
        """重置单例 (测试用)"""
        if cls._client is not None:
            cls._client.close()
        cls._client = None
        cls._instance = None
