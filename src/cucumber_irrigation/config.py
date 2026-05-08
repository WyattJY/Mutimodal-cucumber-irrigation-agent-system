from __future__ import annotations
"""配置加载模块"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def load_settings(config_path: str = "configs/settings.yaml") -> dict[str, Any]:
    """
    加载 YAML 配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_api_key(env_path: str = ".env") -> str:
    """
    从环境变量加载 API Key

    Args:
        env_path: .env 文件路径

    Returns:
        API Key
    """
    load_dotenv(env_path)
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("环境变量 LLM_API_KEY 未设置")
    return api_key


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从当前文件向上查找包含 pyproject.toml 的目录
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # 如果找不到，返回当前工作目录
    return Path.cwd()
