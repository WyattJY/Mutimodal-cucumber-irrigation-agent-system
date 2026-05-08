from __future__ import annotations
"""环境输入数据模型

支持 CSV 读取和前端输入两种来源
参考: task1.md P1-03
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import date
import json


@dataclass
class EnvInput:
    """环境输入数据

    支持两种输入来源:
    - csv: 从历史 CSV 文件读取
    - frontend: 从前端实时输入
    """
    date: str
    temperature: float      # 温度 (°C), 范围: [-10, 50]
    humidity: float         # 湿度 (%), 范围: [0, 100]
    light: float            # 光照 (lux), 范围: [0, 200000]
    source: Literal["csv", "frontend"] = "csv"

    # 可选: YOLO 指标 (如果前端同时提供)
    leaf_instance_count: Optional[float] = None
    leaf_average_mask: Optional[float] = None
    flower_instance_count: Optional[float] = None
    flower_mask_pixel_count: Optional[float] = None
    terminal_average_mask: Optional[float] = None
    fruit_mask_average: Optional[float] = None
    all_leaf_mask: Optional[float] = None

    def __post_init__(self):
        """数据验证"""
        errors = self.validate()
        if errors:
            raise ValueError(f"EnvInput 数据验证失败: {errors}")

    def validate(self) -> list[str]:
        """
        验证环境数据

        Returns:
            错误信息列表 (空列表表示验证通过)
        """
        errors = []

        # 温度验证
        if not -10 <= self.temperature <= 50:
            errors.append(f"温度超出范围 [-10, 50]: {self.temperature}")

        # 湿度验证
        if not 0 <= self.humidity <= 100:
            errors.append(f"湿度超出范围 [0, 100]: {self.humidity}")

        # 光照验证
        if not 0 <= self.light <= 200000:
            errors.append(f"光照超出范围 [0, 200000]: {self.light}")

        return errors

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "date": self.date,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "light": self.light,
            "source": self.source
        }

        # 添加可选的 YOLO 指标
        if self.leaf_instance_count is not None:
            result["leaf_instance_count"] = self.leaf_instance_count
        if self.leaf_average_mask is not None:
            result["leaf_average_mask"] = self.leaf_average_mask
        if self.flower_instance_count is not None:
            result["flower_instance_count"] = self.flower_instance_count
        if self.flower_mask_pixel_count is not None:
            result["flower_mask_pixel_count"] = self.flower_mask_pixel_count
        if self.terminal_average_mask is not None:
            result["terminal_average_mask"] = self.terminal_average_mask
        if self.fruit_mask_average is not None:
            result["fruit_mask_average"] = self.fruit_mask_average
        if self.all_leaf_mask is not None:
            result["all_leaf_mask"] = self.all_leaf_mask

        return result

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "EnvInput":
        """从字典创建"""
        return cls(
            date=data["date"],
            temperature=float(data["temperature"]),
            humidity=float(data["humidity"]),
            light=float(data["light"]),
            source=data.get("source", "csv"),
            leaf_instance_count=data.get("leaf_instance_count"),
            leaf_average_mask=data.get("leaf_average_mask"),
            flower_instance_count=data.get("flower_instance_count"),
            flower_mask_pixel_count=data.get("flower_mask_pixel_count"),
            terminal_average_mask=data.get("terminal_average_mask"),
            fruit_mask_average=data.get("fruit_mask_average"),
            all_leaf_mask=data.get("all_leaf_mask")
        )

    @classmethod
    def from_frontend(
        cls,
        date: str,
        temperature: float,
        humidity: float,
        light: float,
        **yolo_metrics
    ) -> "EnvInput":
        """从前端输入创建"""
        return cls(
            date=date,
            temperature=temperature,
            humidity=humidity,
            light=light,
            source="frontend",
            **yolo_metrics
        )

    def has_yolo_metrics(self) -> bool:
        """是否包含 YOLO 指标"""
        return any([
            self.leaf_instance_count is not None,
            self.leaf_average_mask is not None,
            self.flower_instance_count is not None,
            self.flower_mask_pixel_count is not None,
            self.terminal_average_mask is not None,
            self.fruit_mask_average is not None,
            self.all_leaf_mask is not None
        ])
