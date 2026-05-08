"""Runtime configuration for the cucumber irrigation Agent backend.

The target stack follows the AI_TRAVEL engineering pattern while keeping the
domain as greenhouse cucumber irrigation:

- OpenAI-compatible Qwen/LLM endpoint
- LangGraph checkpointer/store with PostgreSQL preferred and memory fallback
- Redis cache with local fallback
- ChromaDB vector store with keyword fallback
- FastMCP tool servers for YOLO, TSMixer and RAG
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
USER_CONFIG_FILE = CONFIG_DIR / "user_settings.json"


class Settings(BaseSettings):
    """Application settings loaded from environment and optional .env."""

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "local"

    default_openai_api_key: str = Field(
        default="",
        description="OpenAI-compatible API key. Qwen-compatible providers are supported.",
        validation_alias=AliasChoices(
            "DEFAULT_OPENAI_API_KEY",
            "LLM_API_KEY",
            "OPENAI_API_KEY",
            "QWEN_API_KEY",
        ),
    )
    default_openai_base_url: str = Field(
        default="https://aihubmix.com/v1",
        description="OpenAI-compatible base URL.",
        validation_alias=AliasChoices(
            "DEFAULT_OPENAI_BASE_URL",
            "LLM_BASE_URL",
            "OPENAI_BASE_URL",
            "QWEN_BASE_URL",
        ),
    )
    default_openai_model: str = Field(
        default="gpt-chat-latest",
        description="Default chat model.",
        validation_alias=AliasChoices(
            "DEFAULT_OPENAI_MODEL",
            "LLM_MODEL",
            "OPENAI_MODEL",
            "QWEN_MODEL",
        ),
    )
    default_vision_model: str = Field(
        default="gpt-chat-latest",
        description="Default vision-capable model.",
        validation_alias=AliasChoices("LLM_VISION_MODEL", "OPENAI_VISION_MODEL", "QWEN_VISION_MODEL"),
    )

    graph_backend: str = Field(default="auto", validation_alias=AliasChoices("GRAPH_BACKEND"))
    postgres_dsn: str = Field(
        default="postgresql://agriagent:agriagent@localhost:5432/agriagent",
        validation_alias=AliasChoices("POSTGRES_DSN", "DATABASE_URL"),
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias=AliasChoices("REDIS_URL"))
    chroma_host: str = Field(default="localhost", validation_alias=AliasChoices("CHROMA_HOST"))
    chroma_port: int = Field(default=8001, validation_alias=AliasChoices("CHROMA_PORT"))
    chroma_collection: str = Field(default="cucumber_irrigation_knowledge")
    use_chroma: bool = Field(default=True, validation_alias=AliasChoices("USE_CHROMA"))
    use_redis_cache: bool = Field(default=True, validation_alias=AliasChoices("USE_REDIS_CACHE"))
    enable_mcp: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_MCP"))
    enable_langsmith: bool = Field(default=False, validation_alias=AliasChoices("ENABLE_LANGSMITH"))

    yolo_model_path: str = "./models/yolo/yolo11_seg_best.pt"
    tsmixer_model_path: str = "./models/tsmixer/model.pt"
    images_dir: str = "./data/images"
    output_dir: str = "./output"
    cold_start_csv: str = "./data/csv/irrigation_pre.csv"

    pdf_parsers_root: str = Field(default="./.tools/pdf_parsers", validation_alias=AliasChoices("PDF_PARSERS_ROOT"))
    doclayout_yolo_model_path: str = Field(
        default="./.tools/pdf_parsers/models/doclayout-yolo/doclayout_yolo_docstructbench_imgsz1024.pt",
        validation_alias=AliasChoices("DOCLAYOUT_YOLO_MODEL_PATH"),
    )
    table_transformer_detection_model_dir: str = Field(
        default="./.tools/pdf_parsers/models/table-transformer-detection",
        validation_alias=AliasChoices("TABLE_TRANSFORMER_DETECTION_MODEL_DIR"),
    )
    table_transformer_structure_model_dir: str = Field(
        default="./.tools/pdf_parsers/models/table-transformer-structure-recognition-v1.1-all",
        validation_alias=AliasChoices("TABLE_TRANSFORMER_STRUCTURE_MODEL_DIR"),
    )
    enable_pdf_vision_parsers: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_PDF_VISION_PARSERS"))
    pdf_vision_max_pages: int = Field(default=8, validation_alias=AliasChoices("PDF_VISION_MAX_PAGES"))
    pdf_parser_device: str = Field(default="cpu", validation_alias=AliasChoices("PDF_PARSER_DEVICE"))

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


class UserConfig:
    """User-editable LLM configuration persisted by the Settings page."""

    def __init__(self) -> None:
        self._config: dict = {}
        self._load()

    def _load(self) -> None:
        if USER_CONFIG_FILE.exists():
            try:
                self._config = json.loads(USER_CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                self._config = {}
        else:
            self._config = {}

    def _save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        USER_CONFIG_FILE.write_text(
            json.dumps(self._config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def openai_api_key(self) -> Optional[str]:
        return self._config.get("openai_api_key")

    @openai_api_key.setter
    def openai_api_key(self, value: str) -> None:
        self._config["openai_api_key"] = value
        self._save()

    @property
    def openai_base_url(self) -> Optional[str]:
        return self._config.get("openai_base_url")

    @openai_base_url.setter
    def openai_base_url(self, value: str) -> None:
        self._config["openai_base_url"] = value
        self._save()

    @property
    def openai_model(self) -> Optional[str]:
        return self._config.get("openai_model")

    @openai_model.setter
    def openai_model(self, value: str) -> None:
        self._config["openai_model"] = value
        self._save()

    @property
    def use_custom_config(self) -> bool:
        return self._config.get("use_custom_config", False)

    @use_custom_config.setter
    def use_custom_config(self, value: bool) -> None:
        self._config["use_custom_config"] = value
        self._save()

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if value is not None:
                self._config[key] = value
        self._save()

    def to_dict(self) -> dict:
        return {
            "use_custom_config": self.use_custom_config,
            "openai_api_key": self.openai_api_key,
            "openai_base_url": self.openai_base_url,
            "openai_model": self.openai_model,
        }

    def clear(self) -> None:
        self._config = {}
        self._save()


settings = Settings()
user_config = UserConfig()


def get_active_openai_config() -> dict:
    """Return the active OpenAI-compatible LLM configuration."""
    if user_config.use_custom_config and user_config.openai_api_key:
        active_model = user_config.openai_model or settings.default_openai_model
        return {
            "api_key": user_config.openai_api_key,
            "base_url": user_config.openai_base_url or settings.default_openai_base_url,
            "model": active_model,
            "vision_model": active_model,
        }

    return {
        "api_key": settings.default_openai_api_key,
        "base_url": settings.default_openai_base_url,
        "model": settings.default_openai_model,
        "vision_model": settings.default_vision_model,
    }
