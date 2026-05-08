"""增长率统计计算器"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class GrowthStats:
    """全生育期增长率统计"""
    # all_leaf_mask 统计
    all_leaf_mask_start: float
    all_leaf_mask_end: float
    all_leaf_mask_total_growth: float
    all_leaf_mask_daily_avg: float
    all_leaf_mask_daily_std: float

    # 日期范围
    date_start: str
    date_end: str
    total_days: int

    # 阈值（用于 trend 判定）
    threshold_better: float  # > avg + 0.5*std
    threshold_worse: float   # < avg - 0.5*std

    def to_dict(self) -> dict:
        return {
            "created_at": datetime.now().isoformat(),
            "all_leaf_mask": {
                "start_value": self.all_leaf_mask_start,
                "end_value": self.all_leaf_mask_end,
                "total_growth": self.all_leaf_mask_total_growth,
                "daily_avg": self.all_leaf_mask_daily_avg,
                "daily_std": self.all_leaf_mask_daily_std,
                "growth_rate_percent": round(
                    (self.all_leaf_mask_end - self.all_leaf_mask_start)
                    / self.all_leaf_mask_start * 100, 2
                ) if self.all_leaf_mask_start > 0 else 0
            },
            "date_range": {
                "start": self.date_start,
                "end": self.date_end,
                "total_days": self.total_days
            },
            "thresholds": {
                "better": self.threshold_better,
                "worse": self.threshold_worse,
                "description": "better: 日增长 > avg + 0.5*std, worse: 日增长 < avg - 0.5*std"
            }
        }


class StatsCalculator:
    """增长率统计计算器"""

    def __init__(self, csv_path: str):
        """
        初始化统计计算器

        Args:
            csv_path: CSV 文件路径
        """
        self.csv_path = Path(csv_path)
        self.df = self._load_csv()

    def _load_csv(self) -> pd.DataFrame:
        """加载 CSV 文件"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {self.csv_path}")

        df = pd.read_csv(self.csv_path, sep='\t')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        return df

    def calc_growth_stats(self) -> GrowthStats:
        """
        计算全生育期增长率统计

        Returns:
            GrowthStats 统计结果
        """
        col = 'all leaf mask'

        if col not in self.df.columns:
            raise ValueError(f"CSV 中缺少列: {col}")

        values = self.df[col].values
        dates = self.df['date'].values

        # 计算日增长
        daily_growth = np.diff(values)

        # 基本统计
        start_value = float(values[0])
        end_value = float(values[-1])
        total_growth = end_value - start_value
        daily_avg = float(np.mean(daily_growth))
        daily_std = float(np.std(daily_growth))

        # 日期范围
        date_start = pd.Timestamp(dates[0]).strftime('%Y-%m-%d')
        date_end = pd.Timestamp(dates[-1]).strftime('%Y-%m-%d')
        total_days = len(values)

        # 阈值计算
        threshold_better = daily_avg + 0.5 * daily_std
        threshold_worse = daily_avg - 0.5 * daily_std

        stats = GrowthStats(
            all_leaf_mask_start=start_value,
            all_leaf_mask_end=end_value,
            all_leaf_mask_total_growth=total_growth,
            all_leaf_mask_daily_avg=round(daily_avg, 2),
            all_leaf_mask_daily_std=round(daily_std, 2),
            date_start=date_start,
            date_end=date_end,
            total_days=total_days,
            threshold_better=round(threshold_better, 2),
            threshold_worse=round(threshold_worse, 2)
        )

        logger.info(f"增长率统计: 日均增长 {daily_avg:.2f}, 标准差 {daily_std:.2f}")
        logger.info(f"阈值: better > {threshold_better:.2f}, worse < {threshold_worse:.2f}")

        return stats

    def save_stats(self, output_path: str):
        """
        保存统计结果到 JSON 文件

        Args:
            output_path: 输出文件路径
        """
        stats = self.calc_growth_stats()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(stats.to_dict(), f, indent=2, ensure_ascii=False)

        logger.success(f"统计结果已保存: {output_path}")
