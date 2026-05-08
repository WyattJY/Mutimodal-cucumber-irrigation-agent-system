"""环境数据输入处理器

支持 CSV 文件读取和前端实时输入
参考: task1.md P2-01
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

from ..models import EnvInput


class EnvInputHandler:
    """环境数据输入处理器

    支持两种输入来源:
    - CSV 文件: 批量/历史数据读取
    - 前端输入: 实时数据解析
    """

    # CSV 列名映射 (原始列名 -> 标准列名)
    COLUMN_MAPPING = {
        "temperature": "temperature",
        "humidity": "humidity",
        "light": "light",
        "date": "date",
        # 兼容可能的其他列名格式
        "temp": "temperature",
        "hum": "humidity",
        "illuminance": "light"
    }

    def __init__(self, csv_path: Optional[str] = None):
        """
        初始化处理器

        Args:
            csv_path: CSV 文件路径 (可选)
        """
        self.csv_path = csv_path
        self._csv_data: Optional[pd.DataFrame] = None

        if csv_path and Path(csv_path).exists():
            self._load_csv(csv_path)

    def _load_csv(self, csv_path: str) -> None:
        """加载 CSV 文件"""
        self._csv_data = pd.read_csv(csv_path)

        # 标准化日期列
        if 'date' in self._csv_data.columns:
            self._csv_data['date'] = pd.to_datetime(
                self._csv_data['date']
            ).dt.strftime('%Y-%m-%d')

    def from_csv(self, date: str) -> EnvInput:
        """
        从 CSV 读取指定日期的环境数据

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            EnvInput 对象

        Raises:
            ValueError: 如果 CSV 未加载或日期不存在
        """
        if self._csv_data is None:
            raise ValueError("CSV 数据未加载，请先提供 csv_path")

        # 标准化输入日期格式
        try:
            date_normalized = pd.to_datetime(date).strftime('%Y-%m-%d')
        except Exception:
            date_normalized = date

        # 查找日期对应的行
        mask = self._csv_data['date'] == date_normalized
        if not mask.any():
            raise ValueError(f"CSV 中不存在日期: {date}")

        row = self._csv_data[mask].iloc[0]

        return EnvInput(
            date=date_normalized,
            temperature=float(row['temperature']),
            humidity=float(row['humidity']),
            light=float(row['light']),
            source="csv",
            # 可选 YOLO 指标
            leaf_instance_count=self._get_optional(row, 'leaf Instance Count'),
            leaf_average_mask=self._get_optional(row, 'leaf average mask'),
            flower_instance_count=self._get_optional(row, 'flower Instance Count'),
            flower_mask_pixel_count=self._get_optional(row, 'flower Mask Pixel Count'),
            terminal_average_mask=self._get_optional(row, 'terminal average Mask Pixel Count'),
            fruit_mask_average=self._get_optional(row, 'fruit Mask average'),
            all_leaf_mask=self._get_optional(row, 'all leaf mask')
        )

    def _get_optional(self, row: pd.Series, column: str) -> Optional[float]:
        """安全获取可选列值"""
        if column in row.index:
            val = row[column]
            if pd.notna(val):
                return float(val)
        return None

    def from_frontend(
        self,
        date: str,
        temperature: float,
        humidity: float,
        light: float,
        **yolo_metrics
    ) -> EnvInput:
        """
        从前端输入构建环境数据

        Args:
            date: 日期字符串 (YYYY-MM-DD)
            temperature: 温度 (°C)
            humidity: 湿度 (%)
            light: 光照 (lux)
            **yolo_metrics: 可选的 YOLO 指标

        Returns:
            EnvInput 对象
        """
        return EnvInput.from_frontend(
            date=date,
            temperature=temperature,
            humidity=humidity,
            light=light,
            **yolo_metrics
        )

    def validate(self, env: EnvInput) -> Tuple[bool, List[str]]:
        """
        验证环境数据

        Args:
            env: EnvInput 对象

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = env.validate()
        return len(errors) == 0, errors

    def get_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        """获取 CSV 数据的日期范围"""
        if self._csv_data is None:
            return None, None

        dates = self._csv_data['date']
        return dates.min(), dates.max()

    def get_env_history(
        self,
        end_date: str,
        days: int = 3
    ) -> List[dict]:
        """
        获取指定日期之前 N 天的环境数据历史

        Args:
            end_date: 结束日期
            days: 天数

        Returns:
            环境数据列表 (按日期升序)
        """
        if self._csv_data is None:
            return []

        end_dt = pd.to_datetime(end_date)
        start_dt = end_dt - pd.Timedelta(days=days - 1)

        mask = (
            (pd.to_datetime(self._csv_data['date']) >= start_dt) &
            (pd.to_datetime(self._csv_data['date']) <= end_dt)
        )

        history = []
        for _, row in self._csv_data[mask].sort_values('date').iterrows():
            history.append({
                'date': row['date'],
                'temperature': float(row['temperature']),
                'humidity': float(row['humidity']),
                'light': float(row['light'])
            })

        return history

    def has_data_for_date(self, date: str) -> bool:
        """检查是否有指定日期的数据"""
        if self._csv_data is None:
            return False

        try:
            date_normalized = pd.to_datetime(date).strftime('%Y-%m-%d')
            return (self._csv_data['date'] == date_normalized).any()
        except Exception:
            return False
