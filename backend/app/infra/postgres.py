"""PostgreSQL connectivity with graceful local fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from app.core.config import settings


@dataclass
class PostgresRuntime:
    backend: str
    pool: Any | None = None
    error: str | None = None


class PostgresManager:
    def __init__(self) -> None:
        self.runtime = PostgresRuntime(backend="disabled")

    async def connect(self) -> PostgresRuntime:
        if settings.graph_backend == "memory":
            self.runtime = PostgresRuntime(backend="memory")
            return self.runtime

        try:
            import asyncpg  # type: ignore

            pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=1, max_size=5)
            self.runtime = PostgresRuntime(backend="postgres", pool=pool)
            logger.info("[postgres] connected")
        except Exception as exc:
            self.runtime = PostgresRuntime(backend="memory", error=str(exc))
            logger.warning(f"[postgres] unavailable, using memory fallback: {exc}")
        return self.runtime

    async def close(self) -> None:
        if self.runtime.pool is not None:
            await self.runtime.pool.close()
            logger.info("[postgres] closed")
        self.runtime = PostgresRuntime(backend="disabled")

    async def ensure_knowledge_schema(self) -> dict:
        if self.runtime.pool is None:
            return {
                "backend": self.runtime.backend,
                "ready": False,
                "error": self.runtime.error or "postgres pool is not connected",
            }

        statements = [
            """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                original_filename TEXT,
                stored_filename TEXT,
                stored_path TEXT,
                chunks_path TEXT,
                chunk_count INTEGER DEFAULT 0,
                image_count INTEGER DEFAULT 0,
                index_status TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
                page_num INTEGER,
                chunk_index INTEGER,
                content TEXT NOT NULL,
                chroma_id TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS knowledge_assets (
                asset_id TEXT PRIMARY KEY,
                doc_id TEXT REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
                page_num INTEGER,
                asset_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                public_url TEXT,
                width INTEGER,
                height INTEGER,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc_id ON knowledge_chunks(doc_id)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_assets_doc_id ON knowledge_assets(doc_id)",
        ]

        try:
            async with self.runtime.pool.acquire() as conn:
                for statement in statements:
                    await conn.execute(statement)
            return {"backend": "postgres", "ready": True, "error": None}
        except Exception as exc:
            logger.warning(f"[postgres] knowledge schema init failed: {exc}")
            return {"backend": "postgres", "ready": False, "error": str(exc)}

    async def upsert_knowledge_document(
        self,
        document: dict,
        chunks: list[dict],
        assets: list[dict],
    ) -> dict:
        schema = await self.ensure_knowledge_schema()
        if not schema.get("ready"):
            return {
                "backend": self.runtime.backend,
                "indexed": False,
                "document_count": 0,
                "chunk_count": 0,
                "asset_count": 0,
                "error": schema.get("error"),
            }

        try:
            async with self.runtime.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        INSERT INTO knowledge_documents (
                            doc_id, title, category, original_filename, stored_filename,
                            stored_path, chunks_path, chunk_count, image_count, index_status, metadata, updated_at
                        )
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,NOW())
                        ON CONFLICT (doc_id) DO UPDATE SET
                            title=EXCLUDED.title,
                            category=EXCLUDED.category,
                            original_filename=EXCLUDED.original_filename,
                            stored_filename=EXCLUDED.stored_filename,
                            stored_path=EXCLUDED.stored_path,
                            chunks_path=EXCLUDED.chunks_path,
                            chunk_count=EXCLUDED.chunk_count,
                            image_count=EXCLUDED.image_count,
                            index_status=EXCLUDED.index_status,
                            metadata=EXCLUDED.metadata,
                            updated_at=NOW()
                        """,
                        document.get("doc_id"),
                        document.get("title"),
                        document.get("category"),
                        document.get("original_filename"),
                        document.get("stored_filename"),
                        document.get("stored_path"),
                        document.get("chunks_path"),
                        int(document.get("chunk_count") or len(chunks)),
                        int(document.get("image_count") or len(assets)),
                        document.get("index_status") or "indexed",
                        self._jsonb(document),
                    )
                    await conn.executemany(
                        """
                        INSERT INTO knowledge_chunks (
                            chunk_id, doc_id, page_num, chunk_index, content, chroma_id, metadata
                        )
                        VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            page_num=EXCLUDED.page_num,
                            chunk_index=EXCLUDED.chunk_index,
                            content=EXCLUDED.content,
                            chroma_id=EXCLUDED.chroma_id,
                            metadata=EXCLUDED.metadata
                        """,
                        [
                            (
                                chunk.get("unique_id") or chunk.get("id"),
                                document.get("doc_id"),
                                chunk.get("page_num") or chunk.get("page"),
                                (chunk.get("metadata") or {}).get("chunk_index"),
                                chunk.get("page_content") or chunk.get("content") or "",
                                chunk.get("unique_id") or chunk.get("id"),
                                self._jsonb(chunk.get("metadata") or {}),
                            )
                            for chunk in chunks
                        ],
                    )
                    if assets:
                        await conn.executemany(
                            """
                            INSERT INTO knowledge_assets (
                                asset_id, doc_id, page_num, asset_type, file_path, public_url,
                                width, height, metadata
                            )
                            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb)
                            ON CONFLICT (asset_id) DO UPDATE SET
                                page_num=EXCLUDED.page_num,
                                asset_type=EXCLUDED.asset_type,
                                file_path=EXCLUDED.file_path,
                                public_url=EXCLUDED.public_url,
                                width=EXCLUDED.width,
                                height=EXCLUDED.height,
                                metadata=EXCLUDED.metadata
                            """,
                            [
                                (
                                    asset.get("asset_id"),
                                    document.get("doc_id"),
                                    asset.get("page_num"),
                                    asset.get("asset_type") or "image",
                                    asset.get("file_path"),
                                    asset.get("public_url"),
                                    asset.get("width"),
                                    asset.get("height"),
                                    self._jsonb(asset.get("metadata") or {}),
                                )
                                for asset in assets
                            ],
                        )
            return {
                "backend": "postgres",
                "indexed": True,
                "document_count": 1,
                "chunk_count": len(chunks),
                "asset_count": len(assets),
                "error": None,
            }
        except Exception as exc:
            logger.warning(f"[postgres] knowledge upsert failed: {exc}")
            return {
                "backend": "postgres",
                "indexed": False,
                "document_count": 0,
                "chunk_count": 0,
                "asset_count": 0,
                "error": str(exc),
            }

    @staticmethod
    def _jsonb(value: Any) -> str:
        import json

        return json.dumps(value or {}, ensure_ascii=False, default=str)

    def status(self) -> dict:
        return {
            "backend": self.runtime.backend,
            "connected": self.runtime.pool is not None,
            "error": self.runtime.error,
        }


postgres_manager = PostgresManager()
