from __future__ import annotations

from app.infra.chroma_store import chroma_manager
from app.infra.postgres import postgres_manager


class KnowledgeIndexer:
    """Persist uploaded knowledge into PostgreSQL and ChromaDB with graceful fallback."""

    async def index_document(self, document: dict, chunks: list[dict], assets: list[dict]) -> dict:
        postgres_result = await postgres_manager.upsert_knowledge_document(document, chunks, assets)
        chroma_result = chroma_manager.upsert_documents(self._to_chroma_chunks(chunks, assets))
        return {
            "postgres": postgres_result,
            "chroma": chroma_result,
        }

    @staticmethod
    def _to_chroma_chunks(chunks: list[dict], assets: list[dict]) -> list[dict]:
        assets_by_page: dict[int, list[str]] = {}
        for asset in assets:
            page_num = asset.get("page_num")
            if page_num is None:
                continue
            assets_by_page.setdefault(int(page_num), []).append(asset.get("asset_id", ""))

        rows: list[dict] = []
        for chunk in chunks:
            metadata = dict(chunk.get("metadata") or {})
            page_num = chunk.get("page_num") or chunk.get("page") or metadata.get("page")
            if page_num is not None:
                metadata["page_num"] = int(page_num)
                metadata["image_asset_ids"] = ",".join(
                    asset_id for asset_id in assets_by_page.get(int(page_num), []) if asset_id
                )
            rows.append({
                "id": chunk.get("unique_id") or chunk.get("id"),
                "content": chunk.get("page_content") or chunk.get("content") or "",
                "metadata": metadata,
            })
        return rows


knowledge_indexer = KnowledgeIndexer()
