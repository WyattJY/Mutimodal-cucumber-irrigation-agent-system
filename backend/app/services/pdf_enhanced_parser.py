"""Enhanced PDF parsing for user literature ingestion.

This module keeps all third-party parser repositories, model weights and caches
inside the project tree. The heavy vision models are optional: failures are
reported in parser_status while the deterministic PyMuPDF/pdfplumber path still
produces chunks and assets for indexing.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import PROJECT_ROOT, settings


PDF_PARSERS_ROOT = (PROJECT_ROOT / settings.pdf_parsers_root).resolve()
DEFAULT_DOCLAYOUT_MODEL_PATH = (PROJECT_ROOT / settings.doclayout_yolo_model_path).resolve()
DEFAULT_TABLE_DETECTION_MODEL_DIR = (PROJECT_ROOT / settings.table_transformer_detection_model_dir).resolve()
DEFAULT_TABLE_STRUCTURE_MODEL_DIR = (PROJECT_ROOT / settings.table_transformer_structure_model_dir).resolve()


class EnhancedPdfParser:
    """Extract layout/table assets and table chunks from uploaded PDFs."""

    def __init__(self) -> None:
        self.root = PDF_PARSERS_ROOT
        self.models_dir = self.root / "models"
        self.cache_dir = self.root / "cache"
        self.doclayout_model_path = DEFAULT_DOCLAYOUT_MODEL_PATH
        self.table_detection_model_dir = DEFAULT_TABLE_DETECTION_MODEL_DIR
        self.table_structure_model_dir = DEFAULT_TABLE_STRUCTURE_MODEL_DIR
        self._doclayout_model: Any | None = None
        self._table_processor: Any | None = None
        self._table_detection_model: Any | None = None
        self._configure_local_caches()

    def parse(
        self,
        *,
        path: Path,
        doc_id: str,
        assets_root: Path,
        original_filename: str,
        title: str,
        category: str,
    ) -> dict:
        if path.suffix.lower() != ".pdf":
            return self._empty_result("not_pdf")

        self._configure_local_caches()
        assets_root.mkdir(parents=True, exist_ok=True)

        parser_status: dict[str, Any] = {
            "root": str(self.root),
            "doclayout_yolo": "not_run",
            "table_transformer": "not_run",
            "pdfplumber_tables": "not_run",
        }
        chunks: list[dict] = []
        assets: list[dict] = []
        layout_blocks: list[dict] = []

        if settings.enable_pdf_vision_parsers:
            page_images = self._render_page_images(path, doc_id, assets_root, max_pages=settings.pdf_vision_max_pages)
            layout_blocks = self._run_doclayout_yolo(page_images, parser_status)
            transformer_blocks = self._run_table_transformer_detection(page_images, parser_status)
            layout_blocks.extend(transformer_blocks)
            layout_assets = self.crop_layout_assets(
                page_images=page_images,
                layout_blocks=layout_blocks,
                doc_id=doc_id,
                assets_root=assets_root,
                original_filename=original_filename,
            )
            assets.extend(layout_assets)
            parser_status["layout_crop_assets"] = f"ok:{len(layout_assets)}"
        else:
            parser_status["doclayout_yolo"] = "disabled"
            parser_status["table_transformer"] = "disabled"
            parser_status["layout_crop_assets"] = "disabled"

        table_chunks, table_assets = self._extract_pdfplumber_tables(
            path=path,
            doc_id=doc_id,
            assets_root=assets_root,
            original_filename=original_filename,
            title=title,
            category=category,
            parser_status=parser_status,
        )
        chunks.extend(table_chunks)
        assets.extend(table_assets)

        return {
            "chunks": chunks,
            "assets": assets,
            "layout_blocks": layout_blocks,
            "parser_status": parser_status,
            "table_count": len(table_chunks),
        }

    def _configure_local_caches(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(self.cache_dir / "huggingface"))
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(self.cache_dir / "huggingface" / "hub"))
        os.environ.setdefault("TORCH_HOME", str(self.cache_dir / "torch"))
        os.environ.setdefault("XDG_CACHE_HOME", str(self.cache_dir / "xdg"))
        os.environ.setdefault("ULTRALYTICS_SETTINGS", str(self.cache_dir / "ultralytics" / "settings.yaml"))

    @staticmethod
    def _empty_result(reason: str) -> dict:
        return {
            "chunks": [],
            "assets": [],
            "layout_blocks": [],
            "parser_status": {"status": reason},
            "table_count": 0,
        }

    def _render_page_images(self, path: Path, doc_id: str, assets_root: Path, max_pages: int) -> list[dict]:
        page_dir = assets_root / doc_id / "page_images"
        page_dir.mkdir(parents=True, exist_ok=True)
        page_images: list[dict] = []
        try:
            import fitz  # type: ignore

            with fitz.open(str(path)) as pdf:
                for page_index, page in enumerate(pdf, start=1):
                    if max_pages > 0 and page_index > max_pages:
                        break
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    image_path = page_dir / f"page_{page_index:03d}.jpg"
                    pix.save(str(image_path))
                    page_images.append({
                        "page_num": page_index,
                        "image_path": image_path,
                        "width": pix.width,
                        "height": pix.height,
                    })
        except Exception as exc:
            logger.warning(f"[pdf-parser] page rendering failed: {exc}")
        return page_images

    def _run_doclayout_yolo(self, page_images: list[dict], parser_status: dict) -> list[dict]:
        if not page_images:
            parser_status["doclayout_yolo"] = "no_page_images"
            return []
        if not self.doclayout_model_path.exists():
            parser_status["doclayout_yolo"] = f"missing_model:{self.doclayout_model_path}"
            return []

        try:
            from doclayout_yolo import YOLOv10  # type: ignore

            if self._doclayout_model is None:
                self._doclayout_model = YOLOv10(str(self.doclayout_model_path))
            model = self._doclayout_model
            detections: list[dict] = []
            image_paths = [str(item["image_path"]) for item in page_images]
            results = model.predict(
                image_paths,
                imgsz=1024,
                conf=0.2,
                device=settings.pdf_parser_device,
                verbose=False,
            )
            page_by_path = {str(item["image_path"]): item["page_num"] for item in page_images}
            for result in results:
                names = getattr(result, "names", {}) or {}
                source_path = str(getattr(result, "path", ""))
                page_num = page_by_path.get(source_path)
                boxes = getattr(result, "boxes", None)
                if boxes is None:
                    continue
                xyxy = boxes.xyxy.cpu().tolist()
                confs = boxes.conf.cpu().tolist()
                classes = boxes.cls.cpu().tolist()
                for bbox, confidence, class_id in zip(xyxy, confs, classes):
                    detections.append({
                        "page_num": page_num,
                        "label": str(names.get(int(class_id), class_id)),
                        "confidence": float(confidence),
                        "bbox": [round(float(value), 2) for value in bbox],
                        "parser": "doclayout-yolo",
                    })
            parser_status["doclayout_yolo"] = f"ok:{len(detections)}"
            return detections
        except Exception as exc:
            parser_status["doclayout_yolo"] = f"failed:{exc}"
            logger.warning(f"[pdf-parser] DocLayout-YOLO failed: {exc}")
            return []

    def _run_table_transformer_detection(self, page_images: list[dict], parser_status: dict) -> list[dict]:
        if not page_images:
            parser_status["table_transformer"] = "no_page_images"
            return []
        if not self.table_detection_model_dir.exists():
            parser_status["table_transformer"] = f"missing_model:{self.table_detection_model_dir}"
            return []

        try:
            import torch
            from PIL import Image
            from transformers import AutoImageProcessor, TableTransformerForObjectDetection

            if self._table_processor is None:
                self._table_processor = AutoImageProcessor.from_pretrained(
                    str(self.table_detection_model_dir),
                    local_files_only=True,
                )
            if self._table_detection_model is None:
                self._table_detection_model = TableTransformerForObjectDetection.from_pretrained(
                    str(self.table_detection_model_dir),
                    local_files_only=True,
                )
                self._table_detection_model.to(settings.pdf_parser_device)
                self._table_detection_model.eval()
            processor = self._table_processor
            model = self._table_detection_model

            detections: list[dict] = []
            for page in page_images:
                image = Image.open(page["image_path"]).convert("RGB")
                inputs = processor(images=image, return_tensors="pt")
                inputs = {key: value.to(settings.pdf_parser_device) for key, value in inputs.items()}
                with torch.no_grad():
                    outputs = model(**inputs)
                target_sizes = torch.tensor([image.size[::-1]], device=settings.pdf_parser_device)
                results = processor.post_process_object_detection(outputs, threshold=0.75, target_sizes=target_sizes)[0]
                id2label = getattr(model.config, "id2label", {}) or {}
                for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                    detections.append({
                        "page_num": page["page_num"],
                        "label": str(id2label.get(int(label), int(label))),
                        "confidence": float(score.detach().cpu()),
                        "bbox": [round(float(value), 2) for value in box.detach().cpu().tolist()],
                        "parser": "table-transformer-detection",
                    })
            parser_status["table_transformer"] = f"ok:{len(detections)}"
            return detections
        except Exception as exc:
            parser_status["table_transformer"] = f"failed:{exc}"
            logger.warning(f"[pdf-parser] Table Transformer failed: {exc}")
            return []

    def crop_layout_assets(
        self,
        *,
        page_images: list[dict],
        layout_blocks: list[dict],
        doc_id: str,
        assets_root: Path,
        original_filename: str,
    ) -> list[dict]:
        """Persist detected figure/table layout regions as image assets."""
        if not page_images or not layout_blocks:
            return []

        target_labels = {"figure", "table"}
        page_by_num = {int(item["page_num"]): item for item in page_images if item.get("page_num")}
        crop_dir = assets_root / doc_id / "layout_crops"
        crop_dir.mkdir(parents=True, exist_ok=True)

        candidates = [
            block
            for block in layout_blocks
            if str(block.get("label") or "").lower().strip() in target_labels
            and block.get("bbox")
            and int(block.get("page_num") or 0) in page_by_num
        ]
        candidates.sort(
            key=lambda item: (
                int(item.get("page_num") or 0),
                str(item.get("label") or ""),
                -float(item.get("confidence") or 0),
            )
        )

        accepted: list[dict] = []
        for block in candidates:
            page_num = int(block.get("page_num") or 0)
            label = str(block.get("label") or "layout").lower().strip()
            bbox = [float(value) for value in block.get("bbox", [])[:4]]
            if len(bbox) != 4:
                continue
            if any(
                page_num == int(existing.get("page_num") or 0)
                and self._bbox_iou(bbox, existing.get("bbox") or []) > 0.65
                for existing in accepted
            ):
                continue
            accepted.append({**block, "bbox": bbox})

        assets: list[dict] = []
        try:
            from PIL import Image
        except Exception as exc:
            logger.warning(f"[pdf-parser] layout crop skipped, PIL unavailable: {exc}")
            return []

        counters: dict[tuple[int, str], int] = {}
        for block in accepted:
            page_num = int(block.get("page_num") or 0)
            page = page_by_num.get(page_num)
            if not page:
                continue
            image_path = Path(page["image_path"])
            if not image_path.exists():
                continue

            label = str(block.get("label") or "layout").lower().strip()
            counters[(page_num, label)] = counters.get((page_num, label), 0) + 1
            crop_index = counters[(page_num, label)]
            asset_id = f"{doc_id}_page_{page_num:03d}_{label}_{crop_index:03d}"
            output_path = crop_dir / f"page_{page_num:03d}_{label}_{crop_index:03d}.jpg"

            try:
                with Image.open(image_path) as image:
                    width, height = image.size
                    x1, y1, x2, y2 = self._expand_bbox(block["bbox"], width, height, padding=8)
                    if x2 - x1 < 24 or y2 - y1 < 24:
                        continue
                    image.crop((x1, y1, x2, y2)).save(output_path, quality=92)
                assets.append({
                    "asset_id": asset_id,
                    "doc_id": doc_id,
                    "page_num": page_num,
                    "asset_type": "image",
                    "file_path": str(output_path),
                    "public_url": self._asset_public_url(output_path, assets_root),
                    "width": int(x2 - x1),
                    "height": int(y2 - y1),
                    "metadata": {
                        "parser": str(block.get("parser") or "layout-detector"),
                        "layout_label": label,
                        "confidence": float(block.get("confidence") or 0),
                        "bbox": [round(float(value), 2) for value in block["bbox"]],
                        "source_file": original_filename,
                        "source_page_image": str(image_path),
                    },
                })
            except Exception as exc:
                logger.warning(f"[pdf-parser] layout crop failed on page {page_num}: {exc}")
                continue
        return assets

    @staticmethod
    def _expand_bbox(bbox: list[float], width: int, height: int, padding: int = 8) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = bbox
        return (
            max(int(x1) - padding, 0),
            max(int(y1) - padding, 0),
            min(int(x2) + padding, width),
            min(int(y2) + padding, height),
        )

    @staticmethod
    def _bbox_iou(a: list[float], b: list[float]) -> float:
        if len(a) != 4 or len(b) != 4:
            return 0.0
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
        intersection = iw * ih
        if intersection <= 0:
            return 0.0
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - intersection
        return intersection / union if union > 0 else 0.0

    def _extract_pdfplumber_tables(
        self,
        *,
        path: Path,
        doc_id: str,
        assets_root: Path,
        original_filename: str,
        title: str,
        category: str,
        parser_status: dict,
    ) -> tuple[list[dict], list[dict]]:
        try:
            import pdfplumber
        except Exception as exc:
            parser_status["pdfplumber_tables"] = f"unavailable:{exc}"
            return [], []

        table_dir = assets_root / doc_id / "tables"
        table_dir.mkdir(parents=True, exist_ok=True)
        chunks: list[dict] = []
        assets: list[dict] = []
        table_index = 0

        try:
            with pdfplumber.open(str(path)) as pdf:
                for page_index, page in enumerate(pdf.pages, start=1):
                    table_objects = []
                    try:
                        table_objects = page.find_tables()
                    except Exception:
                        table_objects = []

                    if table_objects:
                        extracted_tables = [table.extract() for table in table_objects]
                    else:
                        extracted_tables = page.extract_tables() or []

                    for page_table_index, rows in enumerate(extracted_tables, start=1):
                        markdown = self._table_to_markdown(rows)
                        if not markdown:
                            continue
                        asset_id = f"{doc_id}_page_{page_index:03d}_table_{page_table_index:03d}"
                        markdown_path = table_dir / f"page_{page_index:03d}_table_{page_table_index:03d}.md"
                        csv_path = table_dir / f"page_{page_index:03d}_table_{page_table_index:03d}.csv"
                        markdown_path.write_text(markdown, encoding="utf-8")
                        self._write_table_csv(csv_path, rows)
                        content = f"表格 P{page_index}-{page_table_index}\n\n{markdown}"
                        chunks.append({
                            "unique_id": f"{doc_id}_table_{table_index:04d}",
                            "page_content": content,
                            "page_num": page_index,
                            "file_name": original_filename,
                            "metadata": {
                                "doc_id": doc_id,
                                "title": title,
                                "source": original_filename,
                                "source_type": "user",
                                "category": category,
                                "chunk_index": table_index,
                                "content_type": "user_literature_table",
                                "parser": "pdfplumber+table-transformer",
                                "table_asset_id": asset_id,
                                "table_csv_path": str(csv_path),
                            },
                        })
                        assets.append({
                            "asset_id": asset_id,
                            "doc_id": doc_id,
                            "page_num": page_index,
                            "asset_type": "table",
                            "file_path": str(markdown_path),
                            "public_url": self._asset_public_url(markdown_path, assets_root),
                            "width": None,
                            "height": None,
                            "metadata": {
                                "parser": "pdfplumber+table-transformer",
                                "csv_path": str(csv_path),
                                "csv_public_url": self._asset_public_url(csv_path, assets_root),
                                "source_file": original_filename,
                            },
                        })
                        table_index += 1
            parser_status["pdfplumber_tables"] = f"ok:{len(chunks)}"
        except Exception as exc:
            parser_status["pdfplumber_tables"] = f"failed:{exc}"
            logger.warning(f"[pdf-parser] pdfplumber table extraction failed: {exc}")
        return chunks, assets

    @staticmethod
    def _asset_public_url(asset_path: Path, assets_root: Path) -> str:
        try:
            rel = asset_path.relative_to(assets_root.parent).as_posix()
        except ValueError:
            rel = asset_path.name
        return f"/static/user_literature/{rel}"

    @staticmethod
    def _table_to_markdown(rows: list) -> str:
        cleaned_rows = [
            [str(cell).replace("\n", " ").strip() if cell is not None else "" for cell in row]
            for row in rows
            if row and any(cell not in (None, "") for cell in row)
        ]
        if not cleaned_rows:
            return ""
        width = max(len(row) for row in cleaned_rows)
        normalized = [row + [""] * (width - len(row)) for row in cleaned_rows]
        header = normalized[0]
        separator = ["---"] * width
        body = normalized[1:] or [[""] * width]
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        for row in body:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    @staticmethod
    def _write_table_csv(path: Path, rows: list) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            for row in rows:
                writer.writerow(["" if cell is None else cell for cell in row])


enhanced_pdf_parser = EnhancedPdfParser()
