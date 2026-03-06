from __future__ import annotations
"""时序窗口构建器

构建 TSMixer 所需的 96步×11特征 输入矩阵
参考: task1.md P2-03, requirements1.md 2.1-2.3节
"""

import pandas as pd
import numpy as np
from typing import Optional

from .cold_start import ColdStartFiller


# TSMixer 输入特征列 (顺序与训练时一致)
FEATURE_COLUMNS = [
    'temperature',                    # 日均温度
    'humidity',                       # 日均湿度
    'light',                          # 日均光照
    'leaf Instance Count',            # 叶片实例数量
    'leaf average mask',              # 叶片平均掩码
    'flower Instance Count',          # 花朵实例数量
    'flower Mask Pixel Count',        # 花朵掩码像素
    'terminal average Mask Pixel Count',  # 顶芽平均掩码
    'fruit Mask average',             # 果实平均掩码
    'all leaf mask',                  # 全部叶片掩码
    'Target'                          # 历史灌水量
]


class WindowBuilder:
    """时序窗口构建器

    构建 TSMixer 所需的输入矩阵:
    - 序列长度: 96 步 (天)
    - 特征维度: 11 个特征
    - 输出形状: [96, 11]
    """

    def __init__(
        self,
        cold_start_filler: ColdStartFiller,
        seq_len: int = 96,
        feature_columns: list[str] = None
    ):
        """
        初始化窗口构建器

        Args:
            cold_start_filler: 冷启动填充器
            seq_len: 序列长度 (默认96)
            feature_columns: 特征列 (默认使用标准列)
        """
        self.cold_start_filler = cold_start_filler
        self.seq_len = seq_len
        self.feature_columns = feature_columns or FEATURE_COLUMNS

    def build(
        self,
        data: Optional[pd.DataFrame],
        target_date: str,
        today_data: Optional[dict] = None
    ) -> np.ndarray:
        """
        构建时序窗口

        Args:
            data: 历史数据 (可为空)
            target_date: 目标日期 (YYYY-MM-DD)
            today_data: 今日输入数据 (可选)

        Returns:
            shape [seq_len, num_features] 的输入矩阵
        """
        # 使用冷启动填充器填充数据
        filled_data = self.cold_start_filler.fill(
            user_data=data,
            target_date=target_date,
            today_data=today_data,
            required_length=self.seq_len
        )

        # 确保特征列存在
        for col in self.feature_columns:
            if col not in filled_data.columns:
                filled_data[col] = 0.0

        # 提取特征矩阵
        window = filled_data[self.feature_columns].values.astype(np.float32)

        # 验证形状
        assert window.shape == (self.seq_len, len(self.feature_columns)), \
            f"窗口形状错误: 期望 ({self.seq_len}, {len(self.feature_columns)}), " \
            f"实际 {window.shape}"

        return window

    def build_from_csv(
        self,
        csv_path: str,
        target_date: str,
        today_data: Optional[dict] = None
    ) -> np.ndarray:
        """
        从 CSV 文件构建窗口

        Args:
            csv_path: CSV 文件路径
            target_date: 目标日期
            today_data: 今日输入数据

        Returns:
            shape [seq_len, num_features] 的输入矩阵
        """
        # 加载用户数据
        user_data = self._load_csv(csv_path)

        # 筛选目标日期之前的数据
        if user_data is not None and not user_data.empty:
            target_dt = pd.to_datetime(target_date)
            mask = pd.to_datetime(user_data['date']) < target_dt
            user_data = user_data[mask].sort_values('date')

            # 只取最近的 seq_len - 1 天
            if len(user_data) > self.seq_len - 1:
                user_data = user_data.tail(self.seq_len - 1)

        return self.build(user_data, target_date, today_data)

    def _load_csv(self, csv_path: str) -> Optional[pd.DataFrame]:
        """加载 CSV 数据"""
        try:
            df = pd.read_csv(csv_path, sep='\t')
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            return df
        except Exception:
            return None

    def get_feature_names(self) -> list[str]:
        """获取特征列名"""
        return self.feature_columns.copy()

    def get_window_info(self) -> dict:
        """获取窗口配置信息"""
        return {
            "seq_len": self.seq_len,
            "num_features": len(self.feature_columns),
            "feature_columns": self.feature_columns,
            "output_shape": [self.seq_len, len(self.feature_columns)]
        }
