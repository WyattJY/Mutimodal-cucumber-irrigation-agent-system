"""图像处理服务"""

import base64
from pathlib import Path


class ImageService:
    """图像处理服务"""

    @staticmethod
    def encode_image(image_path: str) -> str:
        """
        将图像编码为 Base64 字符串

        Args:
            image_path: 图像文件路径

        Returns:
            Base64 编码的字符串
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def get_image_url(b64_data: str, mime_type: str = "image/jpeg") -> str:
        """
        生成 data URL

        Args:
            b64_data: Base64 编码的图像数据
            mime_type: MIME 类型

        Returns:
            data URL 字符串
        """
        return f"data:{mime_type};base64,{b64_data}"

    @staticmethod
    def get_mime_type(image_path: str) -> str:
        """根据文件扩展名获取 MIME 类型"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return mime_types.get(ext, "image/jpeg")
