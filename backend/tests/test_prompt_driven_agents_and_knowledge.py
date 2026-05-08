from __future__ import annotations

import asyncio
import io
import json
import sys
import types
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


try:
    import loguru  # noqa: F401
except Exception:
    class _Logger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass

    sys.modules["loguru"] = types.SimpleNamespace(logger=_Logger())


class _Doc:
    page_content = "FAO56 cucumber irrigation water stress threshold and ETc adjustment."
    metadata = {"doc_id": "fao56-test", "source": "Fao56.pdf", "score": 0.9, "page": 42}


async def _fake_llm_json(system_prompt, user_payload, schema_name, fallback, **kwargs):
    enriched = dict(fallback)
    enriched["llm_status"] = "mocked"
    enriched["schema_name"] = schema_name
    enriched["prompt_version"] = "test"
    return enriched


def test_yolo_agent_returns_prompt_driven_json_report(monkeypatch):
    from app.graph import subagent

    monkeypatch.setattr(subagent.llm_agent_service, "analyze_json", _fake_llm_json)

    result = asyncio.run(
        subagent.yolo_agent_node(
            {
                "image_today_path": None,
                "image_yesterday_path": None,
                "date": "2025-03-16",
                "phase": "perception",
            }
        )
    )

    report = result["yolo_agent_report"]
    assert report["agent_name"] == "YOLOAgent"
    assert report["status"] in {"ok", "degraded"}
    assert report["schema_name"] == "yolo_agent_report"
    assert "segmentation_metrics" in report
    assert result["subagent_runs"][0]["prompt_driven"] is True


def test_tsmixer_agent_uses_96_by_11_contract_and_returns_report(monkeypatch):
    from app.graph import subagent

    monkeypatch.setattr(subagent.llm_agent_service, "analyze_json", _fake_llm_json)

    result = asyncio.run(
        subagent.tsmixer_agent_node(
            {
                "env_data": {"temperature": 25, "humidity": 70, "light": 50000},
                "yolo_metrics": {"leaf Instance Count": 8},
                "history_irrigation": [3.5, 4.0, 5.0],
                "yolo_agent_report": {"status": "ok", "crop_state": {"vigor": "normal"}},
            }
        )
    )

    report = result["tsmixer_agent_report"]
    assert report["agent_name"] == "TSMixerAgent"
    assert report["schema_name"] == "tsmixer_agent_report"
    assert report["input_contract"]["window_size"] == 96
    assert report["input_contract"]["feature_count"] == 11
    assert len(result["feature_window"]) == 96
    assert len(result["feature_window"][0]) == 11


def test_rag_agent_returns_phase_report_with_references(monkeypatch):
    from app.graph import subagent
    from app.services import rag_service as rag_module

    async def fake_retrieve(query, top_k=5, filters=None):
        return [_Doc()]

    monkeypatch.setattr(subagent.llm_agent_service, "analyze_json", _fake_llm_json)
    monkeypatch.setattr(rag_module.rag_service, "retrieve", fake_retrieve)

    result = asyncio.run(
        subagent.rag_agent_node(
            {
                "query": "FAO56 cucumber irrigation water stress",
                "top_k": 5,
                "phase": "prediction",
                "yolo_agent_report": {"status": "ok"},
                "tsmixer_agent_report": {"status": "ok", "prediction_l_per_m2": 5.2},
            }
        )
    )

    report = result["rag_agent_report"]
    assert report["agent_name"] == "RAGAgent"
    assert report["phase"] == "prediction"
    assert report["schema_name"] == "rag_agent_report"
    assert report["references"][0]["doc_id"] == "fao56-test"


def test_prediction_join_returns_main_agent_decision(monkeypatch):
    from app.graph import builder_v2

    monkeypatch.setattr(builder_v2.llm_agent_service, "analyze_json", _fake_llm_json)

    result = asyncio.run(
        builder_v2.prediction_join_node(
            {
                "date": "2025-03-16",
                "env_data": {"temperature": 25, "humidity": 70, "light": 50000},
                "yolo_agent_report": {"agent_name": "YOLOAgent", "status": "ok"},
                "tsmixer_agent_report": {"agent_name": "TSMixerAgent", "status": "ok", "prediction_l_per_m2": 5.2},
                "rag_agent_reports": [{"agent_name": "RAGAgent", "phase": "prediction", "status": "ok"}],
                "tsmixer_prediction": 5.2,
                "rag_references": [{"doc_id": "fao56-test", "title": "FAO56"}],
            }
        )
    )

    decision = result["main_agent_decision"]
    assert decision["agent_name"] == "MainAgent"
    assert decision["schema_name"] == "main_agent_decision"
    assert decision["final_irrigation_l_per_m2"] == 5.2
    assert "subagent_summary" in decision


def test_user_literature_upload_is_saved_and_searchable(monkeypatch, tmp_path):
    from fastapi import UploadFile
    from app.api.v1 import knowledge
    from cucumber_irrigation.rag.json_store import JsonKnowledgeStore

    user_dir = tmp_path / "user_literature"
    monkeypatch.setattr(knowledge, "USER_LITERATURE_DIR", user_dir, raising=False)

    upload = UploadFile(
        filename="substrate_notes.md",
        file=io.BytesIO("substrate salinity requires irrigation correction".encode("utf-8")),
    )
    response = asyncio.run(
        knowledge.upload_knowledge_file(file=upload, title="Substrate Notes", category="user_pdf")
    )

    assert response["success"] is True
    assert response["data"]["chunk_count"] >= 1
    assert (user_dir / response["data"]["stored_filename"]).exists()

    system_chunks = tmp_path / "fao56_chunks.json"
    system_chunks.write_text(
        json.dumps(
            [
                {
                    "unique_id": "system-1",
                    "page_content": "standard FAO56 evapotranspiration reference",
                    "page_num": 1,
                    "file_name": "Fao56.pdf",
                    "metadata": {},
                }
            ]
        ),
        encoding="utf-8",
    )
    store = JsonKnowledgeStore(json_path=str(system_chunks), user_literature_dir=str(user_dir))
    results = store.search("substrate salinity correction", top_k=3)

    assert results
    assert results[0].source == "substrate_notes.md"


def test_user_literature_upload_sanitizes_surrogate_unicode(monkeypatch, tmp_path):
    from fastapi import UploadFile
    from app.api.v1 import knowledge

    user_dir = tmp_path / "user_literature"
    monkeypatch.setattr(knowledge, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(
        knowledge,
        "_extract_upload_pages",
        lambda path: [{"page_num": 1, "text": "normal text \ud835 with invalid surrogate"}],
    )

    upload = UploadFile(
        filename="bad_unicode.pdf",
        file=io.BytesIO(b"%PDF-1.4 fake pdf body"),
    )
    response = asyncio.run(
        knowledge.upload_knowledge_file(file=upload, title="Bad Unicode", category="user_pdf")
    )

    assert response["success"] is True
    chunks_path = Path(response["data"]["chunks_path"])
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    assert chunks
    assert "\ud835" not in chunks[0]["page_content"]


def test_chat_rag_uses_uploaded_literature_when_local_rag_unavailable(monkeypatch, tmp_path):
    from app.api.v1 import chat

    user_dir = tmp_path / "user_literature"
    user_dir.mkdir()
    chunks_path = user_dir / "paper_chunks.json"
    chunks_path.write_text(
        json.dumps(
            [
                {
                    "unique_id": "paper_chunk_0000",
                    "page_content": (
                        "2026届硕士学位论文 CO2浓度、温度与施氮量耦合对樱桃番茄生长的调控效应。"
                        "摘要：本研究探究CO2浓度、温度和施氮量三因素交互对樱桃番茄生长、"
                        "产量、品质和氮素吸收利用的影响。"
                    ),
                    "page_num": 1,
                    "file_name": "1.pdf",
                    "metadata": {"source_type": "user", "content_type": "user_literature"},
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (user_dir / "paper.metadata.json").write_text(
        json.dumps(
            {
                "doc_id": "paper",
                "title": "送审论文",
                "original_filename": "1.pdf",
                "chunks_path": str(chunks_path),
                "chunk_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(chat, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(chat, "RAG_AVAILABLE", False, raising=False)
    monkeypatch.setattr(chat, "_rag_service", None, raising=False)

    context, references = asyncio.run(chat._search_rag("我上传的那个送审论文是讲什么的"))

    assert "CO2浓度、温度与施氮量耦合" in context
    assert references
    assert references[0]["source"] == "1.pdf"


def test_chat_returns_uploaded_pdf_assets_for_result_figure_query(monkeypatch, tmp_path):
    from app.api.v1 import chat

    user_dir = tmp_path / "user_literature"
    user_dir.mkdir()
    chunks_path = user_dir / "paper_chunks.json"
    chunks_path.write_text(
        json.dumps(
            [
                {
                    "unique_id": "paper_chunk_0034",
                    "page_content": "图3-2 CO2 浓度、温度和施氮量三因素交互对樱桃番茄茎粗的影响。",
                    "page_num": 34,
                    "file_name": "1.送审论文.pdf",
                    "metadata": {"source_type": "user", "content_type": "user_literature"},
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (user_dir / "paper.metadata.json").write_text(
        json.dumps(
            {
                "doc_id": "paper",
                "title": "1.送审论文",
                "original_filename": "1.送审论文.pdf",
                "chunks_path": str(chunks_path),
                "chunk_count": 1,
                "image_count": 1,
                "assets": [
                    {
                        "asset_id": "paper_page_034_img_001",
                        "doc_id": "paper",
                        "page_num": 34,
                        "asset_type": "image",
                        "file_path": str(user_dir / "assets" / "paper" / "page_034_img_001.jpg"),
                        "public_url": "/static/user_literature/assets/paper/page_034_img_001.jpg",
                        "width": 1200,
                        "height": 800,
                        "metadata": {},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(chat, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(chat, "_has_real_llm_key", lambda config: False)

    response = asyncio.run(
        chat.chat(
            chat.ChatRequest(
                message="请展示1.送审论文的结果图",
                use_history=False,
                use_rag=True,
            )
        )
    )

    assert response.success is True
    assets = response.data["assets"]
    assert assets[0]["asset_id"] == "paper_page_034_img_001"
    assert assets[0]["public_url"].endswith("page_034_img_001.jpg")
    assert "[[asset:paper_page_034_img_001]]" in response.data["content"]


def test_chat_attaches_assets_for_uploaded_model_question_without_image_keyword(monkeypatch, tmp_path):
    from app.api.v1 import chat

    user_dir = tmp_path / "user_literature"
    user_dir.mkdir()
    chunks_path = user_dir / "paper_chunks.json"
    chunks_path.write_text(
        json.dumps(
            [
                {
                    "unique_id": "paper_chunk_0004",
                    "page_content": "Fig.2 YOLO11n-FCHL framework. The YOLO backbone is improved with FBC, C3K2_FBC, HyperNeck and LSCDHead for cucumber segmentation.",
                    "page_num": 4,
                    "file_name": "paper.pdf",
                    "metadata": {"source_type": "user", "content_type": "user_literature"},
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (user_dir / "paper.metadata.json").write_text(
        json.dumps(
            {
                "doc_id": "paper",
                "title": "Paper",
                "original_filename": "paper.pdf",
                "chunks_path": str(chunks_path),
                "chunk_count": 1,
                "image_count": 1,
                "assets": [
                    {
                        "asset_id": "paper_page_004_figure_001",
                        "doc_id": "paper",
                        "page_num": 4,
                        "asset_type": "image",
                        "file_path": str(user_dir / "assets" / "paper" / "page_004_figure_001.jpg"),
                        "public_url": "/static/user_literature/assets/paper/page_004_figure_001.jpg",
                        "width": 1200,
                        "height": 800,
                        "metadata": {"layout_label": "figure"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(chat, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(chat, "_has_real_llm_key", lambda config: False)

    response = asyncio.run(
        chat.chat(
            chat.ChatRequest(
                message="paper.pdf yolo improved how?",
                use_history=False,
                use_rag=True,
            )
        )
    )

    assert response.success is True
    assert response.data["references"][0]["source_type"] == "user_upload"
    assert response.data["assets"][0]["asset_id"] == "paper_page_004_figure_001"
    assert "[[asset:paper_page_004_figure_001]]" in response.data["content"]


def test_chat_followup_image_request_uses_recent_uploaded_literature_context(monkeypatch, tmp_path):
    from app.api.v1 import chat

    user_dir = tmp_path / "user_literature"
    user_dir.mkdir()
    chunks_path = user_dir / "paper_chunks.json"
    chunks_path.write_text(
        json.dumps(
            [
                {
                    "unique_id": "paper_chunk_0004",
                    "page_content": "Fig.2 YOLO11n-FCHL framework. The model improves Backbone, Neck and Head with FBC, HyperNeck and LSCDHead.",
                    "page_num": 4,
                    "file_name": "paper.pdf",
                    "metadata": {"source_type": "user", "content_type": "user_literature"},
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (user_dir / "paper.metadata.json").write_text(
        json.dumps(
            {
                "doc_id": "paper",
                "title": "Paper",
                "original_filename": "paper.pdf",
                "chunks_path": str(chunks_path),
                "chunk_count": 1,
                "image_count": 1,
                "assets": [
                    {
                        "asset_id": "paper_page_004_figure_001",
                        "doc_id": "paper",
                        "page_num": 4,
                        "asset_type": "image",
                        "file_path": str(user_dir / "assets" / "paper" / "page_004_figure_001.jpg"),
                        "public_url": "/static/user_literature/assets/paper/page_004_figure_001.jpg",
                        "width": 1200,
                        "height": 800,
                        "metadata": {"layout_label": "figure"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(chat, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(chat, "_has_real_llm_key", lambda config: False)
    chat._conversation_history[:] = [
        {"role": "user", "content": "paper.pdf yolo improved how?"},
        {"role": "assistant", "content": "paper.pdf says YOLO uses FBC. [[asset:paper_page_004_figure_001]]"},
    ]
    try:
        response = asyncio.run(
            chat.chat(
                chat.ChatRequest(
                    message="please include figure",
                    use_history=True,
                    use_rag=True,
                )
            )
        )
    finally:
        chat._conversation_history.clear()

    assert response.success is True
    assert response.data["references"][0]["source_type"] == "user_upload"
    assert response.data["assets"][0]["asset_id"] == "paper_page_004_figure_001"
    assert "[[asset:paper_page_004_figure_001]]" in response.data["content"]


def test_chat_image_attachment_upload_stays_project_local(monkeypatch, tmp_path):
    from fastapi import UploadFile
    from app.api.v1 import chat

    attachment_dir = tmp_path / "chat_attachments"
    monkeypatch.setattr(chat, "CHAT_ATTACHMENTS_DIR", attachment_dir, raising=False)

    upload = UploadFile(
        filename="leaf.png",
        file=io.BytesIO(b"\x89PNG\r\n\x1a\nfake-image"),
        headers={"content-type": "image/png"},
    )
    response = asyncio.run(chat.upload_chat_image(file=upload))

    data = response["data"]
    assert response["success"] is True
    assert data["attachment_id"]
    assert data["public_url"].startswith("/static/chat_attachments/")
    assert Path(data["stored_path"]).exists()
    assert Path(data["metadata_path"]).exists()
    assert attachment_dir.resolve() in Path(data["stored_path"]).resolve().parents


def test_chat_image_attachment_builds_vision_message(monkeypatch, tmp_path):
    from app.api.v1 import chat

    attachment_dir = tmp_path / "chat_attachments"
    attachment_dir.mkdir()
    image_path = attachment_dir / "img_123.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nfake-image")
    metadata_path = attachment_dir / "img_123.metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "attachment_id": "img_123",
                "original_filename": "leaf.png",
                "stored_filename": "img_123.png",
                "stored_path": str(image_path),
                "public_url": "/static/chat_attachments/img_123.png",
                "mime_type": "image/png",
                "size_bytes": image_path.stat().st_size,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(chat, "CHAT_ATTACHMENTS_DIR", attachment_dir, raising=False)

    attachment = chat._load_chat_attachment("img_123")
    message = chat._build_user_message("分析这张图", attachment)

    assert message["role"] == "user"
    assert message["content"][0] == {"type": "text", "text": "分析这张图"}
    assert message["content"][1]["type"] == "image_url"
    assert message["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_chroma_manager_upserts_knowledge_chunks():
    from app.infra.chroma_store import ChromaManager

    calls = {}

    class FakeCollection:
        def upsert(self, ids, documents, metadatas):
            calls["ids"] = ids
            calls["documents"] = documents
            calls["metadatas"] = metadatas

    manager = ChromaManager()
    manager.collection = FakeCollection()
    manager.backend = "chroma"

    result = manager.upsert_documents(
        [
            {
                "id": "chunk-1",
                "content": "CO2 concentration and nitrogen application affect cherry tomato growth.",
                "metadata": {"doc_id": "doc-1", "page_num": 1, "source": "paper.pdf"},
            }
        ]
    )

    assert result["backend"] == "chroma"
    assert result["indexed_count"] == 1
    assert calls["ids"] == ["chunk-1"]
    assert calls["documents"][0].startswith("CO2 concentration")
    assert calls["metadatas"][0]["doc_id"] == "doc-1"


def test_upload_indexes_postgres_chroma_and_returns_asset_metadata(monkeypatch, tmp_path):
    from fastapi import UploadFile
    from app.api.v1 import knowledge

    user_dir = tmp_path / "user_literature"
    monkeypatch.setattr(knowledge, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(knowledge, "_extract_pdf_images", lambda *args, **kwargs: [
        {
            "asset_id": "asset-1",
            "doc_id": "doc",
            "page_num": 1,
            "asset_type": "image",
            "file_path": str(user_dir / "assets" / "doc" / "page_001_img_001.png"),
            "public_url": "/static/user_literature/assets/doc/page_001_img_001.png",
            "width": 100,
            "height": 80,
            "metadata": {},
        }
    ])

    indexed_payload = {}

    async def fake_index_document(document, chunks, assets):
        indexed_payload["document"] = document
        indexed_payload["chunks"] = chunks
        indexed_payload["assets"] = assets
        return {
            "postgres": {"backend": "postgres", "indexed": True},
            "chroma": {"backend": "chroma", "indexed_count": len(chunks)},
        }

    monkeypatch.setattr(knowledge.knowledge_indexer, "index_document", fake_index_document)

    upload = UploadFile(
        filename="paper.md",
        file=io.BytesIO("uploaded paper text about irrigation and nitrogen".encode("utf-8")),
    )
    response = asyncio.run(
        knowledge.upload_knowledge_file(file=upload, title="Paper", category="user_literature")
    )

    data = response["data"]
    assert data["index_status"] == "indexed"
    assert data["image_count"] == 1
    assert data["index_backends"]["chroma"]["indexed_count"] == data["chunk_count"]
    assert indexed_payload["document"]["doc_id"] == data["doc_id"]
    assert indexed_payload["chunks"][0]["metadata"]["doc_id"] == data["doc_id"]
    assert indexed_payload["assets"][0]["asset_id"] == "asset-1"


def test_pdf_parser_model_paths_stay_inside_project():
    from app.core.config import PROJECT_ROOT
    from app.services.pdf_enhanced_parser import (
        DEFAULT_DOCLAYOUT_MODEL_PATH,
        DEFAULT_TABLE_DETECTION_MODEL_DIR,
        DEFAULT_TABLE_STRUCTURE_MODEL_DIR,
        PDF_PARSERS_ROOT,
    )

    project_root = PROJECT_ROOT.resolve()
    for path in [
        PDF_PARSERS_ROOT,
        DEFAULT_DOCLAYOUT_MODEL_PATH,
        DEFAULT_TABLE_DETECTION_MODEL_DIR,
        DEFAULT_TABLE_STRUCTURE_MODEL_DIR,
    ]:
        assert project_root in path.resolve().parents or path.resolve() == project_root


def test_upload_merges_enhanced_pdf_layout_tables_into_index(monkeypatch, tmp_path):
    from fastapi import UploadFile
    from app.api.v1 import knowledge

    user_dir = tmp_path / "user_literature"
    monkeypatch.setattr(knowledge, "USER_LITERATURE_DIR", user_dir, raising=False)
    monkeypatch.setattr(
        knowledge,
        "_extract_upload_pages",
        lambda path: [{"page_num": 1, "text": "PDF page text with a treatment table"}],
    )
    monkeypatch.setattr(knowledge, "_extract_pdf_images", lambda *args, **kwargs: [])

    class FakeEnhancedParser:
        def parse(self, **kwargs):
            doc_id = kwargs["doc_id"]
            return {
                "chunks": [
                    {
                        "unique_id": f"{doc_id}_table_0000",
                        "page_content": "| T | Yield |\n| --- | --- |\n| T1 | 12.5 |",
                        "page_num": 1,
                        "file_name": kwargs["original_filename"],
                        "metadata": {
                            "doc_id": doc_id,
                            "title": kwargs["title"],
                            "source": kwargs["original_filename"],
                            "source_type": "user",
                            "category": kwargs["category"],
                            "content_type": "user_literature_table",
                            "parser": "table-transformer",
                            "table_asset_id": f"{doc_id}_table_asset_0000",
                        },
                    }
                ],
                "assets": [
                    {
                        "asset_id": f"{doc_id}_table_asset_0000",
                        "doc_id": doc_id,
                        "page_num": 1,
                        "asset_type": "table",
                        "file_path": str(user_dir / "assets" / doc_id / "tables" / "page_001_table_001.md"),
                        "public_url": f"/static/user_literature/assets/{doc_id}/tables/page_001_table_001.md",
                        "width": None,
                        "height": None,
                        "metadata": {"parser": "table-transformer"},
                    }
                ],
                "layout_blocks": [
                    {
                        "page_num": 1,
                        "label": "table",
                        "confidence": 0.91,
                        "bbox": [10, 10, 200, 80],
                        "parser": "doclayout-yolo",
                    }
                ],
                "parser_status": {
                    "doclayout_yolo": "mocked",
                    "table_transformer": "mocked",
                },
                "table_count": 1,
            }

    monkeypatch.setattr(knowledge, "enhanced_pdf_parser", FakeEnhancedParser(), raising=False)

    indexed_payload = {}

    async def fake_index_document(document, chunks, assets):
        indexed_payload["document"] = document
        indexed_payload["chunks"] = chunks
        indexed_payload["assets"] = assets
        return {
            "postgres": {"backend": "postgres", "indexed": True, "asset_count": len(assets)},
            "chroma": {"backend": "chroma", "indexed": True, "indexed_count": len(chunks)},
        }

    monkeypatch.setattr(knowledge.knowledge_indexer, "index_document", fake_index_document)

    upload = UploadFile(filename="paper.pdf", file=io.BytesIO(b"%PDF-1.4 fake pdf body"))
    response = asyncio.run(
        knowledge.upload_knowledge_file(file=upload, title="Paper", category="user_literature")
    )

    data = response["data"]
    assert data["table_count"] == 1
    assert data["layout_block_count"] == 1
    assert data["parser_status"]["table_transformer"] == "mocked"
    assert any(chunk["metadata"]["content_type"] == "user_literature_table" for chunk in indexed_payload["chunks"])
    assert indexed_payload["assets"][0]["asset_type"] == "table"


def test_pdf_image_extraction_writes_assets(tmp_path):
    try:
        import fitz  # type: ignore
        from PIL import Image
    except Exception:
        import pytest
        pytest.skip("PyMuPDF/Pillow not available")

    from app.api.v1.knowledge import _extract_pdf_images

    image_path = tmp_path / "source.png"
    Image.new("RGB", (32, 24), color=(10, 120, 90)).save(image_path)

    pdf_path = tmp_path / "paper.pdf"
    doc = fitz.open()
    page = doc.new_page(width=120, height=120)
    page.insert_image(fitz.Rect(10, 10, 80, 70), filename=str(image_path))
    doc.save(pdf_path)
    doc.close()

    assets = _extract_pdf_images(pdf_path, "doc-1", tmp_path / "assets")

    assert assets
    assert Path(assets[0]["file_path"]).exists()
    assert assets[0]["doc_id"] == "doc-1"
    assert assets[0]["page_num"] == 1
    assert assets[0]["width"] == 32
    assert assets[0]["height"] == 24


def test_gpt_chat_latest_uses_max_completion_tokens():
    from app.core.openai_compat import completion_token_kwargs, temperature_kwargs

    assert completion_token_kwargs("gpt-chat-latest", 2048) == {"max_completion_tokens": 2048}
    assert completion_token_kwargs("qwen-plus", 2048) == {"max_tokens": 2048}
    assert temperature_kwargs("gpt-chat-latest", 0.7) == {}
    assert temperature_kwargs("qwen-plus", 0.7) == {"temperature": 0.7}
