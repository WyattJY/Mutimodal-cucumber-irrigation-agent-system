"""Redis cache adapter with an in-process fallback."""
from __future__ import annotations

import json
import time
from typing import Any

from loguru import logger

from app.core.config import settings


class RedisCache:
    def __init__(self) -> None:
        self._client: Any | None = None
        self._memory: dict[str, tuple[float | None, str]] = {}
        self.backend = "memory"
        self.error: str | None = None

    async def connect(self) -> None:
        if not settings.use_redis_cache:
            self.backend = "memory"
            return

        try:
            import redis.asyncio as redis  # type: ignore

            self._client = redis.from_url(settings.redis_url, decode_responses=True)
            await self._client.ping()
            self.backend = "redis"
            self.error = None
            logger.info("[redis] connected")
        except Exception as exc:
            self._client = None
            self.backend = "memory"
            self.error = str(exc)
            logger.warning(f"[redis] unavailable, using memory fallback: {exc}")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
        self._client = None

    async def get_json(self, key: str) -> Any | None:
        if self._client is not None:
            raw = await self._client.get(key)
        else:
            item = self._memory.get(key)
            if item is None:
                return None
            expires_at, raw = item
            if expires_at is not None and expires_at < time.time():
                self._memory.pop(key, None)
                return None

        if not raw:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        raw = json.dumps(value, ensure_ascii=False)
        if self._client is not None:
            await self._client.set(key, raw, ex=ttl_seconds)
        else:
            expires_at = time.time() + ttl_seconds if ttl_seconds else None
            self._memory[key] = (expires_at, raw)

    def status(self) -> dict:
        return {"backend": self.backend, "connected": self._client is not None, "error": self.error}


redis_cache = RedisCache()

