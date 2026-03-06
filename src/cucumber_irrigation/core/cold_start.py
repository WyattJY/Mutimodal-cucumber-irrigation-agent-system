"""冷启动数据填充器

解决用户数据不足96天的问题
参考: task1.md P2-02, requirements1.md 2.4节
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


class ColdStartFiller:
    """冷启动数据填充器

    当用户数据不足96天时，使用2023年春茬数据填充
    数据源: data/csv/irrigation_pre.csv
    """

    # TSMixer 输入特征列
    FEATURE_COLUMNS = [
        'temperature',
        'humidity',
        'light',
        'leaf Instance Count',
        'leaf average mask',
        'flower Instance Count',
        'flower Mask Pixel Count',
        'terminal average Mask Pixel Count',
        'fruit Mask average',
        'all leaf mask',
        'Target'
    ]

    def __init__(self, reference_data_path: str):
        """
        初始化填充器

        Args:
            reference_data_path: 参考数据路径 (irrigation_pre.csv)
        """
        self.reference_data_path = reference_data_path
        self.reference_data = self._load_reference_data(reference_data_path)

    def _load_reference_data(self, path: str) -> pd.DataFrame:
        """加载参考数据"""
        if not Path(path).exists():
            raise FileNotFoundError(f"参考数据文件不存在: {path}")

        df = pd.read_csv(path, sep='\t')

        # 标准化日期格式
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('date').reset_index(drop=True)

        return df

    def _map_date_to_reference_year(self, date: str, reference_year: int = 2023) -> str:
        """
        将目标日期映射到参考年份

        Args:
            date: 目标日期 (如 2025-03-14)
            reference_year: 参考年份 (默认 2023)

        Returns:
            映射后的日期 (如 2023-03-14)
        """
        dt = pd.to_datetime(date)
        ref_date = dt.replace(year=reference_year)
        return ref_date.strftime('%Y-%m-%d')

    def fill(
        self,
        user_data: Optional[pd.DataFrame],
        target_date: str,
        today_data: Optional[dict] = None,
        required_length: int = 96
    ) -> pd.DataFrame:
        """
        填充数据到指定长度

        Args:
            user_data: 用户已有数据 (可为空)
            target_date: 目标预测日期 (YYYY-MM-DD)
            today_data: 今日输入数据 (可选)
            required_length: 需要的序列长度 (默认96)

        Returns:
            填充后的完整数据 (required_length 行)

        Algorithm:
            1. 计算需要填充的天数: fill_days = (required_length - 1) - len(user_data)
            2. 将目标日期映射到参考年份: 2025-03-14 → 2023-03-14
            3. 从参考数据中取 ref_date 之前 fill_days 天
            4. 拼接顺序: [填充数据 | 用户数据 | 今日数据]
        """
        # 计算用户数据天数
        user_days = 0 if user_data is None or user_data.empty else len(user_data)

        # 需要填充的天数 (预留1天给今日数据)
        fill_days = (required_length - 1) - user_days

        # 映射到参考年份
        ref_target_date = self._map_date_to_reference_year(target_date)

        # 获取填充数据
        fill_data = self._get_fill_data(ref_target_date, fill_days)

        # 构建结果
        parts = []

        # 1. 填充数据
        if fill_days > 0 and not fill_data.empty:
            parts.append(fill_data[self.FEATURE_COLUMNS].copy())

        # 2. 用户数据
        if user_data is not None and not user_data.empty:
            user_subset = user_data[self.FEATURE_COLUMNS].copy()
            parts.append(user_subset)

        # 3. 今日数据
        if today_data is not None:
            today_df = self._today_dict_to_df(today_data)
            parts.append(today_df)
        else:
            # 如果没有今日数据，用参考数据的对应日期填充
            today_fill = self._get_today_fill(ref_target_date)
            parts.append(today_fill)

        # 合并
        if not parts:
            raise ValueError("无可用数据进行填充")

        result = pd.concat(parts, ignore_index=True)

        # 确保长度正确
        if len(result) < required_length:
            # 如果仍然不足，从头部补充更多参考数据
            additional_days = required_length - len(result)
            earlier_date = self._get_earlier_date(ref_target_date, fill_days + additional_days)
            additional_data = self._get_fill_data(earlier_date, additional_days)
            if not additional_data.empty:
                result = pd.concat(
                    [additional_data[self.FEATURE_COLUMNS], result],
                    ignore_index=True
                )

        if len(result) > required_length:
            # 如果超出，截取最后 required_length 行
            result = result.tail(required_length).reset_index(drop=True)

        return result

    def _get_fill_data(self, ref_date: str, days: int) -> pd.DataFrame:
        """
        获取填充数据

        Args:
            ref_date: 参考日期
            days: 需要的天数

        Returns:
            填充数据 DataFrame
        """
        if days <= 0:
            return pd.DataFrame()

        ref_dt = pd.to_datetime(ref_date)

        # 获取 ref_date 之前的 days 天数据
        # 不包括 ref_date 本身 (因为 ref_date 对应今日)
        end_dt = ref_dt - timedelta(days=1)
        start_dt = end_dt - timedelta(days=days - 1)

        mask = (
            (pd.to_datetime(self.reference_data['date']) >= start_dt) &
            (pd.to_datetime(self.reference_data['date']) <= end_dt)
        )

        fill_data = self.reference_data[mask].sort_values('date')

        # 如果数据不足，从可用数据的最早日期开始取
        if len(fill_data) < days:
            available = self.reference_data.sort_values('date')
            fill_data = available.head(days)

        return fill_data.reset_index(drop=True)

    def _get_today_fill(self, ref_date: str) -> pd.DataFrame:
        """获取今日填充数据"""
        mask = self.reference_data['date'] == ref_date
        if mask.any():
            row = self.reference_data[mask].iloc[0]
            return pd.DataFrame([row[self.FEATURE_COLUMNS]])

        # 如果没有精确匹配，使用最接近的日期
        ref_dt = pd.to_datetime(ref_date)
        dates = pd.to_datetime(self.reference_data['date'])
        closest_idx = (dates - ref_dt).abs().argmin()
        row = self.reference_data.iloc[closest_idx]
        return pd.DataFrame([row[self.FEATURE_COLUMNS]])

    def _today_dict_to_df(self, today_data: dict) -> pd.DataFrame:
        """将今日数据字典转换为 DataFrame"""
        row = {}
        for col in self.FEATURE_COLUMNS:
            if col in today_data:
                row[col] = today_data[col]
            elif col == 'Target':
                row[col] = 0.0  # Target 会被模型预测
            else:
                row[col] = 0.0  # 缺失值填充为0

        return pd.DataFrame([row])

    def _get_earlier_date(self, date: str, days: int) -> str:
        """获取更早的日期"""
        dt = pd.to_datetime(date)
        earlier = dt - timedelta(days=days)
        return earlier.strftime('%Y-%m-%d')

    def get_available_date_range(self) -> tuple[str, str]:
        """获取参考数据的日期范围"""
        dates = self.reference_data['date']
        return dates.min(), dates.max()
