"""TSMixer 预测服务

封装 TSMixer 模型的推理流程
参考: task1.md P4-02
"""

from typing import Optional, Tuple
from pathlib import Path
import pickle
import os

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from loguru import logger


# 特征列 (11列)
FEATURE_COLUMNS = [
    'temperature',
    'humidity',
    'light',
    'leaf Instance Count',
    'leaf Area',
    'flower Instance Count',
    'flower Area',
    'fruit Instance Count',
    'fruit Area',
    'other Instance Count',
    'Target'  # 灌水量
]


class TSMixerService:
    """TSMixer 预测服务

    流程:
    1. 调用 WindowBuilder 构建 96 步窗口
    2. 加载/创建 StandardScaler
    3. 标准化输入
    4. 模型推理
    5. 逆标准化 Target 列
    6. 返回预测灌水量 (L/m²)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        scaler_path: Optional[str] = None,
        training_data_path: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        初始化服务

        Args:
            model_path: 模型文件路径 (.pt)
            scaler_path: Scaler 文件路径 (.pkl)
            training_data_path: 训练数据路径 (用于创建 Scaler)
            device: 推理设备 (cpu/cuda)
        """
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.training_data_path = training_data_path
        self.device = device

        self._model = None
        self._scaler = None
        self._initialized = False

        # 默认路径
        if model_path is None:
            self.model_path = str(Path(__file__).parent.parent.parent.parent.parent / "Irrigation" / "model.pt")
        if training_data_path is None:
            self.training_data_path = str(
                Path(__file__).parent.parent.parent.parent.parent / "Irrigation" / "data" / "Irrigation" / "irrigation_final_11.17.xlsx"
            )

    def _lazy_init(self):
        """延迟初始化模型和 Scaler"""
        if self._initialized:
            return

        # 加载模型
        self._load_model()

        # 加载或创建 Scaler
        self._load_or_create_scaler()

        self._initialized = True

    def _load_model(self):
        """加载 TSMixer 模型"""
        try:
            import torch

            if os.path.exists(self.model_path):
                # 使用 weights_only=False 加载包含自定义类的模型
                self._model = torch.load(
                    self.model_path,
                    map_location=self.device,
                    weights_only=False
                )
                self._model.eval()
                logger.info(f"TSMixer 模型加载成功: {self.model_path}")
            else:
                logger.warning(f"模型文件不存在: {self.model_path}")
                self._model = None
        except ImportError:
            logger.warning("PyTorch 未安装，TSMixer 服务不可用")
            self._model = None
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self._model = None

    def _load_or_create_scaler(self):
        """加载或创建 StandardScaler"""
        # 尝试加载已保存的 Scaler
        if self.scaler_path and os.path.exists(self.scaler_path):
            try:
                with open(self.scaler_path, 'rb') as f:
                    self._scaler = pickle.load(f)
                logger.info(f"Scaler 加载成功: {self.scaler_path}")
                return
            except Exception as e:
                logger.warning(f"Scaler 加载失败: {e}")

        # 从训练数据创建 Scaler
        if os.path.exists(self.training_data_path):
            try:
                self._create_scaler_from_training_data()
            except Exception as e:
                logger.error(f"Scaler 创建失败: {e}")
                self._scaler = None
        else:
            logger.warning(f"训练数据不存在: {self.training_data_path}")
            self._scaler = None

    def _create_scaler_from_training_data(self):
        """从训练数据创建 Scaler"""
        df = pd.read_excel(self.training_data_path, header=0)

        # 使用与 IrrigationLoader 相同的训练数据范围
        train_end = 1495  # 训练集结束位置

        # 提取特征列
        cols_data = df.columns[1:]  # 跳过 date 列
        train_data = df[cols_data].iloc[:train_end]

        # 创建并拟合 Scaler
        self._scaler = StandardScaler()
        self._scaler.fit(train_data.values)

        logger.info(f"Scaler 创建成功，训练数据形状: {train_data.shape}")

        # 可选：保存 Scaler
        if self.scaler_path:
            try:
                os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)
                with open(self.scaler_path, 'wb') as f:
                    pickle.dump(self._scaler, f)
                logger.info(f"Scaler 已保存: {self.scaler_path}")
            except Exception as e:
                logger.warning(f"Scaler 保存失败: {e}")

    def predict(
        self,
        window: pd.DataFrame,
        return_confidence: bool = False
    ) -> Tuple[float, Optional[float]]:
        """
        执行预测

        Args:
            window: 96 步 × 11 特征的输入窗口
            return_confidence: 是否返回置信度

        Returns:
            (预测灌水量, 置信度) 或 预测灌水量
        """
        self._lazy_init()

        if self._model is None:
            logger.warning("模型未加载，返回默认值")
            return (5.0, 0.5) if return_confidence else 5.0

        if self._scaler is None:
            logger.warning("Scaler 未加载，返回默认值")
            return (5.0, 0.5) if return_confidence else 5.0

        try:
            import torch

            # 确保列顺序正确
            if len(window.columns) == 11:
                data = window.values
            else:
                # 尝试按 FEATURE_COLUMNS 排序
                data = window[FEATURE_COLUMNS].values

            # 标准化
            data_scaled = self._scaler.transform(data)

            # 转换为 tensor
            x = torch.FloatTensor(data_scaled).unsqueeze(0).to(self.device)

            # 创建时间标记 (简化版)
            x_mark = torch.zeros(1, 96, 4).to(self.device)

            # 推理
            with torch.no_grad():
                output = self._model(x, x_mark, None, None)

            # 提取预测值
            pred_scaled = output[:, -1, -1].cpu().numpy()[0]

            # 逆标准化 Target 列
            target_idx = -1  # Target 是最后一列
            pred = pred_scaled * self._scaler.scale_[target_idx] + self._scaler.mean_[target_idx]

            # 范围约束
            pred = float(np.clip(pred, 0.1, 15.0))

            if return_confidence:
                # 简单的置信度估算 (基于预测值是否在合理范围内)
                confidence = 0.8 if 1.0 <= pred <= 10.0 else 0.6
                return pred, confidence

            return pred

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return (5.0, 0.5) if return_confidence else 5.0

    def predict_from_raw(
        self,
        user_data: pd.DataFrame,
        target_date: str,
        today_data: Optional[dict] = None,
        cold_start_filler=None
    ) -> Tuple[float, Optional[float]]:
        """
        从原始数据预测

        Args:
            user_data: 用户历史数据
            target_date: 目标日期
            today_data: 今日数据
            cold_start_filler: 冷启动填充器

        Returns:
            (预测灌水量, 置信度)
        """
        from ..core.window_builder import WindowBuilder

        # 构建窗口
        window_builder = WindowBuilder(cold_start_filler=cold_start_filler)
        window = window_builder.build(
            user_data=user_data,
            target_date=target_date,
            today_data=today_data
        )

        return self.predict(window, return_confidence=True)

    def is_available(self) -> bool:
        """检查服务是否可用"""
        self._lazy_init()
        return self._model is not None and self._scaler is not None

    def get_model_info(self) -> dict:
        """获取模型信息"""
        self._lazy_init()
        return {
            "model_path": self.model_path,
            "model_loaded": self._model is not None,
            "scaler_loaded": self._scaler is not None,
            "device": self.device,
            "feature_columns": FEATURE_COLUMNS,
            "input_shape": (96, 11)
        }
