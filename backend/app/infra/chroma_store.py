"""ChromaDB adapter used by the Agentic RAG layer.

The application can run without Chroma installed. In that case RAG falls back
to local keyword retrieval but still exposes the same metadata contract.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import PROJECT_ROOT, settings


class ChromaManager:
    def __init__(self) -> None:
        self.client: Any | None = None
        self.collection: Any | None = None
        self.backend = "keyword"
        self.error: str | None = None

    async def connect(self) -> None:
        if not settings.use_chroma:
            self.backend = "keyword"
            return

        try:
            cache_home = PROJECT_ROOT / "data" / "cache" / "chroma_home"
            cache_home.mkdir(parents=True, exist_ok=True)
            os.environ["HOME"] = str(cache_home)
            os.environ["USERPROFILE"] = str(cache_home)
            os.environ.setdefault("XDG_CACHE_HOME", str(PROJECT_ROOT / "data" / "cache"))

            import chromadb  # type: ignore
            from chromadb.utils.embedding_functions import onnx_mini_lm_l6_v2  # type: ignore

            onnx_mini_lm_l6_v2.ONNXMiniLM_L6_V2.DOWNLOAD_PATH = (
                cache_home
                / ".cache"
                / "chroma"
                / "onnx_models"
                / onnx_mini_lm_l6_v2.ONNXMiniLM_L6_V2.MODEL_NAME
            )

            self.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            self.collection = self.client.get_or_create_collection(settings.chroma_collection)
            self.backend = "chroma"
            self.error = None
            logger.info("[chroma] connected")
        except Exception as exc:
            self.client = None
            self.collection = None
            self.backend = "keyword"
            self.error = str(exc)
            logger.warning(f"[chroma] unavailable, using keyword fallback: {exc}")

    async def close(self) -> None:
        self.client = None
        self.collection = None

    def upsert_documents(self, chunks: list[dict]) -> dict:
        """Upsert knowledge chunks into Chroma while keeping a local fallback contract."""
        if self.collection is None:
            return {
                "backend": self.backend,
                "indexed": False,
                "indexed_count": 0,
                "error": self.error or "chroma collection is not connected",
            }

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        for chunk in chunks:
            chunk_id = str(chunk.get("id") or chunk.get("unique_id") or chunk.get("doc_id") or "")
            content = str(chunk.get("content") or chunk.get("page_content") or chunk.get("snippet") or "")
            if not chunk_id or not content:
                continue
            metadata = chunk.get("metadata") or {}
            ids.append(chunk_id)
            documents.append(content)
            metadatas.append(self._normalize_metadata(metadata))

        if not ids:
            return {"backend": self.backend, "indexed": False, "indexed_count": 0, "error": "no valid chunks"}

        try:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            return {"backend": self.backend, "indexed": True, "indexed_count": len(ids), "error": None}
        except Exception as exc:
            self.error = str(exc)
            logger.warning(f"[chroma] knowledge upsert failed: {exc}")
            return {"backend": self.backend, "indexed": False, "indexed_count": 0, "error": str(exc)}

    @staticmethod
    def _normalize_metadata(metadata: dict) -> dict:
        normalized: dict[str, str | int | float | bool | None] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized[str(key)] = value
            else:
                normalized[str(key)] = str(value)
        return normalized

    def query(self, query_text: str, top_k: int = 5, where: dict | None = None) -> list[dict]:
        if self.collection is None:
            return []

        result = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        rows: list[dict] = []
        for idx, doc in enumerate(documents):
            distance = distances[idx] if idx < len(distances) else 1.0
            rows.append(
                {
                    "doc_id": ids[idx] if idx < len(ids) else f"chroma_{idx}",
                    "title": (metadatas[idx] or {}).get("title") if idx < len(metadatas) else None,
                    "snippet": doc,
                    "relevance": max(0.0, 1.0 - float(distance)),
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                }
            )
        return rows

    def status(self) -> dict:
        return {"backend": self.backend, "connected": self.collection is not None, "error": self.error}


chroma_manager = ChromaManager()
