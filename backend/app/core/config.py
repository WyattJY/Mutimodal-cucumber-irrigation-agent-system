# Configuration Management Module
"""
配置管理模块 - 管理 API Key、Base URL 等配置

支持:
1. 默认配置 (开发者 API Key)
2. 用户自定义配置 (Settings 页面)
3. 环境变量覆盖
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 配置文件路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
USER_CONFIG_FILE = CONFIG_DIR / "user_settings.json"


class Settings(BaseSettings):
    """应用配置"""

    # API 服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # 默认 LLM 配置 (开发者配置)
    default_openai_api_key: str = Field(
        default="",
        description="默认 OpenAI API Key",
        validation_alias=AliasChoices("DEFAULT_OPENAI_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY")
    )
    default_openai_base_url: str = Field(
        default="https://yunwu.ai/v1",
        description="默认 OpenAI Base URL",
        validation_alias=AliasChoices("DEFAULT_OPENAI_BASE_URL", "LLM_BASE_URL", "OPENAI_BASE_URL")
    )
    default_openai_model: str = Field(
        default="gpt-5.2-chat-latest",
        description="默认模型",
        validation_alias=AliasChoices("DEFAULT_OPENAI_MODEL", "LLM_MODEL", "OPENAI_MODEL")
    )

    # 模型路径
    yolo_model_path: str = "./models/yolo/yolo11_seg_best.pt"
    tsmixer_model_path: str = "./models/tsmixer/model.pt"

    # 数据路径
    images_dir: str = "./data/images"
    output_dir: str = "./output"
    cold_start_csv: str = "./data/csv/irrigation_pre.csv"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


class UserConfig:
    """用户自定义配置 (保存到文件)"""

    def __init__(self):
        self._config: dict = {}
        self._load()

    def _load(self):
        """从文件加载配置"""
        if USER_CONFIG_FILE.exists():
            try:
                with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}
        else:
            self._config = {}

    def _save(self):
        """保存配置到文件"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def openai_api_key(self) -> Optional[str]:
        return self._config.get("openai_api_key")

    @openai_api_key.setter
    def openai_api_key(self, value: str):
        self._config["openai_api_key"] = value
        self._save()

    @property
    def openai_base_url(self) -> Optional[str]:
        return self._config.get("openai_base_url")

    @openai_base_url.setter
    def openai_base_url(self, value: str):
        self._config["openai_base_url"] = value
        self._save()

    @property
    def openai_model(self) -> Optional[str]:
        return self._config.get("openai_model")

    @openai_model.setter
    def openai_model(self, value: str):
        self._config["openai_model"] = value
        self._save()

    @property
    def use_custom_config(self) -> bool:
        return self._config.get("use_custom_config", False)

    @use_custom_config.setter
    def use_custom_config(self, value: bool):
        self._config["use_custom_config"] = value
        self._save()

    def update(self, **kwargs):
        """批量更新配置"""
        for key, value in kwargs.items():
            if value is not None:
                self._config[key] = value
        self._save()

    def to_dict(self) -> dict:
        """返回配置字典"""
        return {
            "use_custom_config": self.use_custom_config,
            "openai_api_key": self.openai_api_key,
            "openai_base_url": self.openai_base_url,
            "openai_model": self.openai_model,
        }

    def clear(self):
        """清除用户配置"""
        self._config = {}
        self._save()


# 全局实例
settings = Settings()
user_config = UserConfig()


def get_active_openai_config() -> dict:
    """获取当前激活的 OpenAI 配置"""
    if user_config.use_custom_config and user_config.openai_api_key:
        return {
            "api_key": user_config.openai_api_key,
            "base_url": user_config.openai_base_url or settings.default_openai_base_url,
            "model": user_config.openai_model or settings.default_openai_model,
        }
    else:
        return {
            "api_key": settings.default_openai_api_key,
            "base_url": settings.default_openai_base_url,
            "model": settings.default_openai_model,
        }
