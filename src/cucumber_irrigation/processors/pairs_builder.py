from __future__ import annotations
"""日期配对构建器"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger


@dataclass
class DayPair:
    """日期配对"""
    date: str                              # 今日日期 YYYY-MM-DD
    image_today: str                       # 今日图像路径
    image_yesterday: str                   # 昨日图像路径
    yolo_today: Optional[dict] = None      # 今日 YOLO 指标
    yolo_yesterday: Optional[dict] = None  # 昨日 YOLO 指标
    env_today: Optional[dict] = None       # 今日环境数据
    csv_matched: bool = True               # CSV 是否匹配

    def to_dict(self) -> dict:
        return asdict(self)


class PairsBuilder:
    """配对构建器"""

    # CSV 列名映射
    YOLO_COLS = [
        "leaf Instance Count",
        "leaf average mask",
        "flower Instance Count",
        "flower Mask Pixel Count",
        "terminal average Mask Pixel Count",
        "fruit Mask average",
        "all leaf mask"
    ]

    ENV_COLS = ["temperature", "humidity", "light"]

    def __init__(self, images_dir: str, csv_path: str):
        """
        初始化配对构建器

        Args:
            images_dir: 图像目录路径
            csv_path: CSV 文件路径
        """
        self.images_dir = Path(images_dir)
        self.csv_path = Path(csv_path)
        self.df = self._load_csv()
        self.image_dates = self._scan_images()

    def _load_csv(self) -> pd.DataFrame:
        """加载 CSV 文件"""
        if not self.csv_path.exists():
            logger.warning(f"CSV 文件不存在: {self.csv_path}")
            return pd.DataFrame()

        df = pd.read_csv(self.csv_path, sep='\t')
        # 标准化日期格式
        df['date_std'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.set_index('date_std')
        return df

    def _scan_images(self) -> dict[str, str]:
        """
        扫描图像目录，获取日期->路径映射

        Returns:
            {日期: 图像路径} 字典
        """
        images = {}
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            for path in self.images_dir.glob(ext):
                date_str = self._parse_image_date(path.name)
                if date_str:
                    images[date_str] = str(path)

        logger.info(f"扫描到 {len(images)} 张图像")
        return images

    def _parse_image_date(self, filename: str) -> Optional[str]:
        """
        解析图像文件名为日期

        Args:
            filename: 文件名，如 0315.jpg

        Returns:
            日期字符串 YYYY-MM-DD，解析失败返回 None
        """
        # 匹配 MMDD 格式
        match = re.match(r'^(\d{2})(\d{2})\.(jpg|jpeg|png)$', filename, re.IGNORECASE)
        if not match:
            return None

        month, day = int(match.group(1)), int(match.group(2))

        # 假设年份为 2024
        try:
            date = datetime(2024, month, day)
            return date.strftime('%Y-%m-%d')
        except ValueError:
            return None

    def _get_yolo_data(self, date: str) -> Optional[dict]:
        """获取指定日期的 YOLO 数据"""
        if date not in self.df.index:
            return None

        row = self.df.loc[date]
        return {col: float(row[col]) if pd.notna(row[col]) else None
                for col in self.YOLO_COLS}

    def _get_env_data(self, date: str) -> Optional[dict]:
        """获取指定日期的环境数据"""
        if date not in self.df.index:
            return None

        row = self.df.loc[date]
        return {col: float(row[col]) if pd.notna(row[col]) else None
                for col in self.ENV_COLS}

    def build_pairs(self) -> list[DayPair]:
        """
        构建所有配对

        规则：
        1. 以图像日期为准
        2. 只有连续两天都有图像才构建配对
        3. CSV 数据可能缺失，标记 csv_matched

        Returns:
            DayPair 列表
        """
        pairs = []
        sorted_dates = sorted(self.image_dates.keys())

        for i, today in enumerate(sorted_dates):
            # 计算昨天的日期
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            yesterday = (today_dt - timedelta(days=1)).strftime('%Y-%m-%d')

            # 检查昨天是否有图像
            if yesterday not in self.image_dates:
                logger.debug(f"跳过 {today}: 前一天 {yesterday} 无图像")
                continue

            # 获取数据
            yolo_today = self._get_yolo_data(today)
            yolo_yesterday = self._get_yolo_data(yesterday)
            env_today = self._get_env_data(today)

            csv_matched = yolo_today is not None

            pair = DayPair(
                date=today,
                image_today=self.image_dates[today],
                image_yesterday=self.image_dates[yesterday],
                yolo_today=yolo_today,
                yolo_yesterday=yolo_yesterday,
                env_today=env_today,
                csv_matched=csv_matched
            )
            pairs.append(pair)

        logger.info(f"构建了 {len(pairs)} 个配对")
        return pairs

    def get_missing_dates(self) -> list[str]:
        """获取图像缺失的日期"""
        if not self.image_dates:
            return []

        sorted_dates = sorted(self.image_dates.keys())
        start = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        end = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')

        missing = []
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            if date_str not in self.image_dates:
                missing.append(date_str)
            current += timedelta(days=1)

        return missing

    def get_skipped_pairs(self) -> list[dict]:
        """获取因日期不连续而跳过的配对"""
        skipped = []
        sorted_dates = sorted(self.image_dates.keys())

        for today in sorted_dates:
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            yesterday = (today_dt - timedelta(days=1)).strftime('%Y-%m-%d')

            if yesterday not in self.image_dates:
                # 不是第一天的情况才算跳过
                if today != sorted_dates[0]:
                    skipped.append({
                        "date": today,
                        "reason": f"前一天 {yesterday} 无图像"
                    })

        return skipped

    def save_pairs_index(self, output_path: str):
        """
        保存配对索引到 JSON 文件

        Args:
            output_path: 输出文件路径
        """
        pairs = self.build_pairs()
        missing = self.get_missing_dates()
        skipped = self.get_skipped_pairs()

        index_data = {
            "created_at": datetime.now().isoformat(),
            "images_dir": str(self.images_dir),
            "csv_path": str(self.csv_path),
            "total_images": len(self.image_dates),
            "total_pairs": len(pairs),
            "missing_dates": missing,
            "skipped_pairs": skipped,
            "pairs": [p.to_dict() for p in pairs]
        }

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        logger.success(f"配对索引已保存: {output_path}")
