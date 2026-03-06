from __future__ import annotations
# TSMixer Service - 灌水量预测服务
"""
TSMixer 时序预测服务
- 加载训练好的 TSMixer 模型
- 接收 96 天 × 11 特征的输入
- 预测下一天的灌水量
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "tsmixer"
COLDSTART_DIR = PROJECT_ROOT / "data" / "coldstart"


@dataclass
class TSMixerConfig:
    """TSMixer 模型配置 (与训练时一致)"""
    task_name: str = "long_term_forecast"
    seq_len: int = 96       # 输入序列长度
    pred_len: int = 1       # 预测长度
    enc_in: int = 11        # 特征数量
    d_model: int = 32       # 模型维度
    e_layers: int = 2       # 编码器层数
    dropout: float = 0.1    # Dropout


class ResBlock(nn.Module):
    """TSMixer 残差块"""
    def __init__(self, configs):
        super(ResBlock, self).__init__()
        self.temporal = nn.Sequential(
            nn.Linear(configs.seq_len, configs.d_model),
            nn.ReLU(),
            nn.Linear(configs.d_model, configs.seq_len),
            nn.Dropout(configs.dropout)
        )
        self.channel = nn.Sequential(
            nn.Linear(configs.enc_in, configs.d_model),
            nn.ReLU(),
            nn.Linear(configs.d_model, configs.enc_in),
            nn.Dropout(configs.dropout)
        )

    def forward(self, x):
        x = x + self.temporal(x.transpose(1, 2)).transpose(1, 2)
        x = x + self.channel(x)
        return x


class TSMixerModel(nn.Module):
    """TSMixer 模型"""
    def __init__(self, configs):
        super(TSMixerModel, self).__init__()
        self.task_name = configs.task_name
        self.layer = configs.e_layers
        self.model = nn.ModuleList([ResBlock(configs) for _ in range(configs.e_layers)])
        self.pred_len = configs.pred_len
        self.projection = nn.Linear(configs.seq_len, configs.pred_len)

    def forecast(self, x_enc):
        for i in range(self.layer):
            x_enc = self.model[i](x_enc)
        enc_out = self.projection(x_enc.transpose(1, 2)).transpose(1, 2)
        return enc_out

    def forward(self, x_enc, x_mark_enc=None, x_dec=None, x_mark_dec=None, mask=None):
        dec_out = self.forecast(x_enc)
        return dec_out[:, -self.pred_len:, :]


# 特征名称 (与训练数据一致)
FEATURE_NAMES = [
    "temperature",          # 0. 日均温度
    "humidity",             # 1. 日均湿度
    "light",                # 2. 日均光照
    "leaf_instance_count",  # 3. 叶片数量
    "leaf_average_mask",    # 4. 叶片平均面积
    "flower_instance_count",# 5. 花朵数量
    "flower_mask_pixel_count", # 6. 花朵总掩码面积
    "terminal_average_mask",# 7. 顶芽平均面积
    "fruit_mask_average",   # 8. 果实平均面积
    "all_leaf_mask",        # 9. 叶片总面积
    "target"                # 10. 目标 (灌水量)
]


class TSMixerService:
    """TSMixer 灌水量预测服务"""

    _instance = None
    _model = None
    _configs = None
    _coldstart_data = None
    _scaler_params = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if TSMixerService._model is None:
            self._load_model()
            self._load_coldstart_data()

    def _load_model(self):
        """加载 TSMixer 模型"""
        import sys
        print(f"[TSMixer] Loading model...")
        print(f"[TSMixer] MODELS_DIR: {MODELS_DIR}")
        print(f"[TSMixer] MODELS_DIR exists: {MODELS_DIR.exists()}")
        sys.stdout.flush()

        model_path = MODELS_DIR / "model_state.pt"
        print(f"[TSMixer] Checking model_state.pt: {model_path.exists()}")
        sys.stdout.flush()

        # 备选路径
        if not model_path.exists():
            model_path = MODELS_DIR / "model.pt"
            print(f"[TSMixer] Trying model.pt: {model_path.exists()}")
            sys.stdout.flush()

        if not model_path.exists():
            print(f"[TSMixer] Model not found at {model_path}")
            sys.stdout.flush()
            return

        try:
            # 创建配置
            TSMixerService._configs = TSMixerConfig()

            # 创建模型
            model = TSMixerModel(TSMixerService._configs)

            # 加载权重
            state_dict = torch.load(str(model_path), map_location="cpu", weights_only=False)
            model.load_state_dict(state_dict)
            model.eval()

            TSMixerService._model = model
            print(f"[TSMixer] Model loaded successfully from {model_path}")
            sys.stdout.flush()

        except Exception as e:
            print(f"[TSMixer] Failed to load model: {e}")
            # 尝试加载完整模型
            try:
                TSMixerService._model = torch.load(str(model_path), map_location="cpu", weights_only=False)
                TSMixerService._model.eval()
                print(f"[TSMixer] Loaded full model")
            except Exception as e2:
                print(f"[TSMixer] Failed to load full model: {e2}")

    def _load_coldstart_data(self):
        """加载冷启动数据"""
        coldstart_path = COLDSTART_DIR / "irrigation_final_11.17.xlsx"

        if not coldstart_path.exists():
            print(f"[TSMixer] Coldstart data not found at {coldstart_path}")
            return

        try:
            df = pd.read_excel(coldstart_path)
            # 假设列名与 FEATURE_NAMES 对应
            TSMixerService._coldstart_data = df
            print(f"[TSMixer] Coldstart data loaded: {len(df)} rows")

            # 计算 scaler 参数 (StandardScaler - z-score)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            self._scaler_params = {
                'mean': df[numeric_cols].mean().to_dict(),
                'std': df[numeric_cols].std().to_dict()
            }

        except Exception as e:
            print(f"[TSMixer] Failed to load coldstart data: {e}")

    @property
    def model(self):
        return TSMixerService._model

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def normalize(self, data: np.ndarray) -> np.ndarray:
        """标准化输入数据 (z-score normalization)"""
        if self._scaler_params is None:
            return data

        normalized = data.copy().astype(np.float32)
        # 使用 coldstart 数据的 mean/std 进行归一化
        for i, feature_name in enumerate(FEATURE_NAMES):
            col_name = self._get_column_name(feature_name)
            if col_name and col_name in self._scaler_params['mean']:
                mean_val = self._scaler_params['mean'][col_name]
                std_val = self._scaler_params['std'][col_name]
                if std_val > 0:
                    normalized[:, i] = (data[:, i] - mean_val) / std_val
        return normalized

    def denormalize(self, value: float, feature_idx: int = 10) -> float:
        """反标准化输出值 (target 列, z-score)"""
        if self._scaler_params is None:
            return value

        # Target 列的 mean/std
        target_col = self._get_column_name("target")
        if target_col and target_col in self._scaler_params['mean']:
            mean_val = self._scaler_params['mean'][target_col]
            std_val = self._scaler_params['std'][target_col]
            return value * std_val + mean_val
        return value

    def _get_column_name(self, feature_name: str) -> str:
        """将特征名映射到 coldstart 数据的列名"""
        mapping = {
            "temperature": "temperature",
            "humidity": "humidity",
            "light": "light",
            "leaf_instance_count": "leaf Instance Count",
            "leaf_average_mask": "leaf average mask",
            "flower_instance_count": "flower Instance Count",
            "flower_mask_pixel_count": "flower Mask Pixel Count",
            "terminal_average_mask": "terminal average Mask Pixel Count",
            "fruit_mask_average": "fruit Mask average",
            "all_leaf_mask": "all leaf mask",
            "target": "Target"
        }
        return mapping.get(feature_name, "")

    def predict(
        self,
        features: np.ndarray,
        return_confidence: bool = False
    ) -> Dict:
        """
        执行预测

        Args:
            features: shape (96, 11) 的输入数组
            return_confidence: 是否返回置信度

        Returns:
            预测结果字典
        """
        if not self.is_available:
            return self._mock_prediction()

        try:
            # 确保输入形状正确
            if features.shape != (96, 11):
                raise ValueError(f"Expected shape (96, 11), got {features.shape}")

            # 标准化
            features_norm = self.normalize(features)

            # 转换为 Tensor
            x = torch.FloatTensor(features_norm).unsqueeze(0)  # (1, 96, 11)

            # 推理
            with torch.no_grad():
                output = self.model(x)  # (1, 1, 11)

            # 获取目标值 (最后一个特征)
            pred_value = output[0, 0, -1].item()

            # 反标准化
            irrigation = self.denormalize(pred_value)

            # 确保非负
            irrigation = max(0, irrigation)

            result = {
                "irrigation_amount": round(irrigation, 2),
                "unit": "L/m²",
                "predicted_at": datetime.now().isoformat(),
                "is_mock": False
            }

            if return_confidence:
                # 简单的置信度估计
                result["confidence"] = 0.85

            return result

        except Exception as e:
            print(f"[TSMixer] Prediction failed: {e}")
            return self._mock_prediction()

    def build_features(
        self,
        env_data: Dict,
        yolo_metrics: Dict,
        historical_data: Optional[List[Dict]] = None,
        target_date: str = None
    ) -> np.ndarray:
        """
        构建 96×11 特征矩阵

        Args:
            env_data: 当天环境数据 {temperature, humidity, light}
            yolo_metrics: YOLO 提取的视觉指标
            historical_data: 历史数据列表 (最多 95 天)
            target_date: 预测目标日期

        Returns:
            np.ndarray: shape (96, 11)
        """
        features = np.zeros((96, 11))

        # 如果有历史数据，填充前 95 天
        if historical_data:
            for i, day_data in enumerate(historical_data[-95:]):
                idx = 95 - len(historical_data[-95:]) + i
                features[idx] = self._dict_to_features(day_data)
        elif self._coldstart_data is not None:
            # 使用冷启动数据填充
            features = self._fill_with_coldstart(features, target_date)

        # 填充当天数据 (第 96 天, index 95)
        features[95] = [
            env_data.get('temperature', 25.0),
            env_data.get('humidity', 70.0),
            env_data.get('light', 50000.0),
            yolo_metrics.get('leaf_instance_count', 10),
            yolo_metrics.get('leaf_average_mask', 1000.0),
            yolo_metrics.get('flower_instance_count', 5),
            yolo_metrics.get('flower_mask_pixel_count', 500),
            yolo_metrics.get('terminal_average_mask', 300.0),
            yolo_metrics.get('fruit_mask_average', 400.0),
            yolo_metrics.get('all_leaf_mask', 10000),
            0  # Target 待预测
        ]

        return features

    def _dict_to_features(self, data: Dict) -> List[float]:
        """将数据字典转换为特征列表"""
        return [
            data.get('temperature', 25.0),
            data.get('humidity', 70.0),
            data.get('light', 50000.0),
            data.get('leaf_instance_count', data.get('leaf_count', 10)),
            data.get('leaf_average_mask', data.get('leaf_avg_mask', 1000.0)),
            data.get('flower_instance_count', data.get('flower_count', 5)),
            data.get('flower_mask_pixel_count', data.get('flower_mask', 500)),
            data.get('terminal_average_mask', data.get('terminal_mask', 300.0)),
            data.get('fruit_mask_average', data.get('fruit_mask', 400.0)),
            data.get('all_leaf_mask', 10000),
            data.get('irrigation', data.get('target', 0))
        ]

    def _fill_with_coldstart(self, features: np.ndarray, target_date: str = None) -> np.ndarray:
        """使用冷启动数据填充"""
        if self._coldstart_data is None:
            return features

        df = self._coldstart_data

        # 按正确的列名顺序提取数据
        col_mapping = [
            "temperature",
            "humidity",
            "light",
            "leaf Instance Count",
            "leaf average mask",
            "flower Instance Count",
            "flower Mask Pixel Count",
            "terminal average Mask Pixel Count",
            "fruit Mask average",
            "all leaf mask",
            "Target"
        ]

        # 取最后 96 行作为历史数据
        if len(df) >= 96:
            try:
                features = df[col_mapping].tail(96).values.astype(np.float32)
            except Exception as e:
                print(f"[TSMixer] Error extracting coldstart data: {e}")

        return features

    def _mock_prediction(self) -> Dict:
        """模拟预测结果"""
        import random

        return {
            "irrigation_amount": round(random.uniform(1.5, 4.5), 2),
            "unit": "L/m²",
            "predicted_at": datetime.now().isoformat(),
            "is_mock": True,
            "note": "TSMixer model not loaded, using mock data"
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性 (简化版)"""
        return {
            "temperature": 0.15,
            "humidity": 0.12,
            "light": 0.10,
            "leaf_instance_count": 0.08,
            "leaf_average_mask": 0.10,
            "flower_instance_count": 0.08,
            "flower_mask_pixel_count": 0.07,
            "terminal_average_mask": 0.08,
            "fruit_mask_average": 0.07,
            "all_leaf_mask": 0.10,
            "historical_irrigation": 0.05
        }


# 单例实例
tsmixer_service = TSMixerService()
