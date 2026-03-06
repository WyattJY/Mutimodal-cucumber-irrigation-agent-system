"""文献上传 API

P7-02: 文献上传 API
支持用户上传自定义文献到用户专属集合
"""

import os
import shutil
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import uuid

from loguru import logger


@dataclass
class LiteratureMetadata:
    """文献元数据"""
    literature_id: str
    title: str
    author: Optional[str] = None
    category: str = "general"  # irrigation/cucumber/general
    file_name: str = ""
    file_size: int = 0
    file_format: str = ""
    chunk_count: int = 0
    upload_time: str = ""
    is_indexed: bool = False
    source_type: str = "user"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "literature_id": self.literature_id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_format": self.file_format,
            "chunk_count": self.chunk_count,
            "upload_time": self.upload_time,
            "is_indexed": self.is_indexed,
            "source_type": self.source_type
        }


@dataclass
class UploadConfig:
    """上传配置"""
    upload_dir: str = "data/user_literature"
    max_file_size: int = 50 * 1024 * 1024  # 50 MB
    supported_formats: List[str] = field(
        default_factory=lambda: [".pdf", ".txt", ".md"]
    )
    auto_index: bool = True  # 上传后自动索引


class LiteratureUploadService:
    """用户文献上传服务

    功能:
    - 文件上传与验证
    - 元数据管理
    - 自动分块与索引 (可选)
    - 文献列表与删除
    """

    def __init__(
        self,
        config: Optional[UploadConfig] = None,
        indexer=None,
        mongo_client=None
    ):
        """
        初始化上传服务

        Args:
            config: 上传配置
            indexer: 索引器实例 (用于自动索引)
            mongo_client: MongoDB 客户端
        """
        self.config = config or UploadConfig()
        self._indexer = indexer
        self._mongo_client = mongo_client
        self._metadata_collection = None

        # 确保上传目录存在
        Path(self.config.upload_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"LiteratureUploadService 初始化, 上传目录: {self.config.upload_dir}")

    def _get_metadata_collection(self):
        """获取元数据集合"""
        if self._metadata_collection is not None:
            return self._metadata_collection

        if self._mongo_client is not None:
            try:
                db = self._mongo_client["cucumber_irrigation"]
                self._metadata_collection = db["user_literature_metadata"]
                return self._metadata_collection
            except Exception as e:
                logger.warning(f"MongoDB 连接失败: {e}")

        # 回退到文件存储
        return None

    def upload(
        self,
        file_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        category: str = "general"
    ) -> str:
        """
        上传文献到用户集合

        Args:
            file_path: 文件路径
            title: 标题 (默认使用文件名)
            author: 作者
            category: 类别 (irrigation/cucumber/general)

        Returns:
            literature_id

        Raises:
            ValueError: 文件格式不支持或文件过大
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)

        # 验证文件
        self._validate_file(path)

        # 生成文献 ID
        literature_id = self._generate_literature_id()

        # 复制文件到上传目录
        dest_path = self._copy_to_upload_dir(path, literature_id)

        # 创建元数据
        metadata = LiteratureMetadata(
            literature_id=literature_id,
            title=title or path.stem,
            author=author,
            category=category,
            file_name=path.name,
            file_size=path.stat().st_size,
            file_format=path.suffix.lower().lstrip('.'),
            upload_time=datetime.now().isoformat(),
            source_type="user"
        )

        # 保存元数据
        self._save_metadata(metadata)

        logger.info(f"文献上传成功: {metadata.title} (ID: {literature_id})")

        # 自动索引
        if self.config.auto_index and self._indexer:
            try:
                chunk_count = self._indexer.index_literature(
                    str(dest_path),
                    literature_id,
                    metadata.to_dict()
                )
                metadata.chunk_count = chunk_count
                metadata.is_indexed = True
                self._save_metadata(metadata)
                logger.info(f"文献索引完成: {chunk_count} 个分块")
            except Exception as e:
                logger.warning(f"自动索引失败: {e}")

        return literature_id

    def list_user_literature(self) -> List[LiteratureMetadata]:
        """列出用户上传的文献"""
        collection = self._get_metadata_collection()

        if collection is not None:
            # 从 MongoDB 读取
            try:
                docs = collection.find({"source_type": "user"})
                return [
                    LiteratureMetadata(**{
                        k: v for k, v in doc.items() if k != "_id"
                    })
                    for doc in docs
                ]
            except Exception as e:
                logger.warning(f"MongoDB 查询失败: {e}")

        # 从文件读取
        return self._list_from_files()

    def get_literature(self, literature_id: str) -> Optional[LiteratureMetadata]:
        """获取文献详情"""
        collection = self._get_metadata_collection()

        if collection is not None:
            try:
                doc = collection.find_one({"literature_id": literature_id})
                if doc:
                    return LiteratureMetadata(**{
                        k: v for k, v in doc.items() if k != "_id"
                    })
            except Exception as e:
                logger.warning(f"MongoDB 查询失败: {e}")

        # 从文件读取
        return self._get_from_file(literature_id)

    def delete(self, literature_id: str) -> bool:
        """
        删除用户文献

        Args:
            literature_id: 文献 ID

        Returns:
            是否删除成功

        Note:
            仅能删除用户集合中的文献，不影响系统文献
        """
        metadata = self.get_literature(literature_id)

        if metadata is None:
            logger.warning(f"文献不存在: {literature_id}")
            return False

        if metadata.source_type != "user":
            logger.warning(f"无法删除系统文献: {literature_id}")
            return False

        # 删除文件
        file_path = Path(self.config.upload_dir) / f"{literature_id}.{metadata.file_format}"
        if file_path.exists():
            file_path.unlink()

        # 删除元数据
        collection = self._get_metadata_collection()
        if collection is not None:
            try:
                collection.delete_one({"literature_id": literature_id})
            except Exception as e:
                logger.warning(f"MongoDB 删除失败: {e}")

        # 删除本地元数据文件
        meta_path = Path(self.config.upload_dir) / f"{literature_id}.json"
        if meta_path.exists():
            meta_path.unlink()

        # 删除索引
        if self._indexer:
            try:
                self._indexer.delete_literature(literature_id)
            except Exception as e:
                logger.warning(f"索引删除失败: {e}")

        logger.info(f"文献删除成功: {literature_id}")
        return True

    def _validate_file(self, path: Path):
        """验证文件"""
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        # 检查格式
        if path.suffix.lower() not in self.config.supported_formats:
            raise ValueError(
                f"不支持的文件格式: {path.suffix}. "
                f"支持: {self.config.supported_formats}"
            )

        # 检查大小
        if path.stat().st_size > self.config.max_file_size:
            raise ValueError(
                f"文件过大: {path.stat().st_size / 1024 / 1024:.2f} MB. "
                f"最大: {self.config.max_file_size / 1024 / 1024:.2f} MB"
            )

    def _generate_literature_id(self) -> str:
        """生成文献 ID"""
        return f"user_{uuid.uuid4().hex[:12]}"

    def _copy_to_upload_dir(self, source: Path, literature_id: str) -> Path:
        """复制文件到上传目录"""
        dest = Path(self.config.upload_dir) / f"{literature_id}{source.suffix}"
        shutil.copy2(source, dest)
        return dest

    def _save_metadata(self, metadata: LiteratureMetadata):
        """保存元数据"""
        collection = self._get_metadata_collection()

        if collection is not None:
            try:
                collection.update_one(
                    {"literature_id": metadata.literature_id},
                    {"$set": metadata.to_dict()},
                    upsert=True
                )
                return
            except Exception as e:
                logger.warning(f"MongoDB 保存失败: {e}")

        # 保存到文件
        self._save_to_file(metadata)

    def _save_to_file(self, metadata: LiteratureMetadata):
        """保存元数据到文件"""
        import json

        meta_path = Path(self.config.upload_dir) / f"{metadata.literature_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

    def _list_from_files(self) -> List[LiteratureMetadata]:
        """从文件读取元数据列表"""
        import json

        result = []
        upload_dir = Path(self.config.upload_dir)

        for meta_file in upload_dir.glob("*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result.append(LiteratureMetadata(**data))
            except Exception as e:
                logger.warning(f"读取元数据失败: {meta_file}: {e}")

        return result

    def _get_from_file(self, literature_id: str) -> Optional[LiteratureMetadata]:
        """从文件读取元数据"""
        import json

        meta_path = Path(self.config.upload_dir) / f"{literature_id}.json"

        if not meta_path.exists():
            return None

        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return LiteratureMetadata(**data)
        except Exception as e:
            logger.warning(f"读取元数据失败: {meta_path}: {e}")
            return None
