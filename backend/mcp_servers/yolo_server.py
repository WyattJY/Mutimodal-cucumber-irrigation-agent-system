"""
YOLO MCP Server — 将 YOLO 实例分割封装为标准 MCP 工具

启动方式:
  python mcp_servers/yolo_server.py          # stdio 模式（本地）
  python mcp_servers/yolo_server.py --http   # Streamable HTTP 模式（远程）
"""
from __future__ import annotations

import sys
import json
import base64
import argparse
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# 添加 backend 路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

mcp = FastMCP("YOLO Segmentation Server")


@mcp.tool()
async def yolo_segment(
    image_base64: str,
    image_id: Optional[str] = None,
    save_visualization: bool = False,
) -> dict:
    """
    对输入图像进行 YOLO11n-FCHL 实例分割，提取植株表型指标。

    Args:
        image_base64: Base64 编码的 JPEG/PNG 图像
        image_id: 可选的图像标识符（用于日志追踪）
        save_visualization: 是否保存可视化结果图像

    Returns:
        {
            "leaf": {"instance_count": 12, "average_mask": 3456.5, ...},
            "flower": {"instance_count": 3, "mask_pixel_count": 450, ...},
            "fruit": {"instance_count": 5, "mask_average": 234.1, ...},
            "terminal": {"instance_count": 8, "average_mask": 189.3, ...},
            "all_leaf_mask": 28000,
            "visualization_base64": "..." (如果 save_visualization=True)
        }
    """
    from app.services.yolo_service import yolo_service

    try:
        # 调用已有的 YOLO Service
        image_bytes = base64.b64decode(image_base64)
        filename = image_id or f"mcp_{__import__('time').time_ns()}"

        metrics, vis_bytes = yolo_service.process_bytes(
            image_bytes, filename=filename
        )

        result = {"metrics": metrics}

        # 可选返回可视化图像
        if save_visualization and vis_bytes:
            result["visualization_base64"] = base64.b64encode(vis_bytes).decode()

        return result

    except Exception as e:
        return {"error": str(e), "metrics": {}}


@mcp.tool()
async def yolo_health_check() -> dict:
    """检查 YOLO 模型是否已加载且可用。"""
    from app.services.yolo_service import yolo_service

    return {
        "available": yolo_service.is_available,
        "model_loaded": yolo_service._model is not None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="使用 Streamable HTTP 模式")
    parser.add_argument("--port", type=int, default=8010, help="HTTP 端口")
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport="stdio")
