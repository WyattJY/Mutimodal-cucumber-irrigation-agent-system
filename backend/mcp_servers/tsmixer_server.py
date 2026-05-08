"""
TSMixer MCP Server — 将 TSMixer 时序预测封装为标准 MCP 工具

启动方式:
  python mcp_servers/tsmixer_server.py          # stdio 模式
  python mcp_servers/tsmixer_server.py --http   # Streamable HTTP 模式
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

mcp = FastMCP("TSMixer Prediction Server")


@mcp.tool()
async def tsmixer_predict(
    temperature: float,
    humidity: float,
    light: float,
    yolo_metrics: dict,
    target_date: Optional[str] = None,
    history_irrigation: Optional[float] = None,
) -> dict:
    """
    基于 TSMixer 模型预测次日灌水量。

    TSMixer 融合 11 维特征：
    - 环境数据 3 维：温度(°C)、湿度(%)、光照(lux)
    - 视觉表型 7 维：YOLO 输出的叶/花/果/顶芽指标
    - 历史灌水 1 维：前日实际灌水量

    Args:
        temperature: 日均温度 (°C)
        humidity: 日均湿度 (%)
        light: 日均光照 (lux)
        yolo_metrics: YOLO 分割结果（leaf/flower/fruit/terminal 指标）
        target_date: 预测目标日期 (YYYY-MM-DD)
        history_irrigation: 前日实际灌水量 (L/m²)

    Returns:
        {
            "prediction": 8.5,         # 预测灌水量 (L/m²)
            "confidence": [7.2, 9.8],  # 95% 置信区间
            "features_used": 11,
            "model": "TSMixer"
        }
    """
    from app.services.tsmixer_service import tsmixer_service

    try:
        # 构建环境数据
        env_data = {
            "temperature": temperature,
            "humidity": humidity,
            "light": light,
        }

        # 调用已有的 TSMixer Service
        features = tsmixer_service.build_features(
            env_data=env_data,
            yolo_metrics=yolo_metrics,
            target_date=target_date,
        )

        result = tsmixer_service.predict(features, return_confidence=True)

        return {
            "prediction": result.get("value", 0),
            "confidence": result.get("confidence", []),
            "features_used": 11,
            "model": "TSMixer",
            "input_summary": {
                "temperature": temperature,
                "humidity": humidity,
                "light": light,
                "leaf_count": yolo_metrics.get("leaf_instance_count"),
                "flower_count": yolo_metrics.get("flower_instance_count"),
            },
        }

    except Exception as e:
        return {"error": str(e), "prediction": None}


@mcp.tool()
async def tsmixer_health_check() -> dict:
    """检查 TSMixer 模型是否已加载且可用。"""
    from app.services.tsmixer_service import tsmixer_service

    return {
        "available": tsmixer_service.is_available,
        "model_loaded": tsmixer_service._model is not None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="使用 Streamable HTTP 模式")
    parser.add_argument("--port", type=int, default=8012, help="HTTP 端口")
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport="stdio")
