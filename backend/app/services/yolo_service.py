from __future__ import annotations
# YOLO Instance Segmentation Service
import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import io
import base64

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
CUSTOM_ULTRALYTICS_PATH = BACKEND_DIR / "ultralytics"

if CUSTOM_ULTRALYTICS_PATH.exists():
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("ultralytics"):
            del sys.modules[mod_name]
    print(f"[YOLO] Custom ultralytics path: {CUSTOM_ULTRALYTICS_PATH}")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "yolo"
IMAGES_DIR = PROJECT_ROOT / "data" / "images"
OUTPUT_DIR = PROJECT_ROOT / "output" / "segmented_images"
METRICS_DIR = PROJECT_ROOT / "output" / "yolo_metrics"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

NEW_WIDTH, NEW_HEIGHT = 3200, 1920
TILE_SIZE = 640
NUM_COLS = NEW_WIDTH // TILE_SIZE
NUM_ROWS = NEW_HEIGHT // TILE_SIZE

CLASS_NAMES = {0: "leaf", 1: "terminal", 2: "flower", 3: "fruit"}
CLASS_COLORS = {"leaf": (0, 0, 255), "terminal": (0, 150, 150), "flower": (0, 255, 0), "fruit": (255, 0, 0)}


class YOLOService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if YOLOService._model is None:
            self._load_model()

    def _load_model(self):
        model_path = MODELS_DIR / "yolo11_seg_best.pt"
        if not model_path.exists():
            print(f"[YOLO] Model not found at {model_path}")
            return
        try:
            from ultralytics import YOLO
            import torch

            # 强制使用 CPU (避免 CUDA 兼容性问题)
            device = 'cpu'
            print(f"[YOLO] Using CPU for inference")

            YOLOService._model = YOLO(str(model_path))
            YOLOService._model.to(device)
            YOLOService._device = device
            print(f"[YOLO] Model loaded from {model_path} (device: {device})")
        except Exception as e:
            print(f"[YOLO] Failed to load model: {e}")

    @property
    def model(self):
        return YOLOService._model

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def _mock_metrics(self, image_path=None):
        import random
        return {"leaf_instance_count": random.randint(8, 15), "is_mock": True}

    def process_image(self, image_path, save_visualization=True, conf_threshold=0.25, use_tile_inference=True):
        if not self.is_available:
            return self._mock_metrics(image_path)
        import cv2
        import numpy as np

        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")

        if use_tile_inference:
            return self._process_with_tiles(image, image_path, conf_threshold)
        else:
            return self._process_single(image, image_path, conf_threshold)

    def _process_with_tiles(self, image, image_path, conf_threshold=0.25):
        """分块推理: 缩放到3200x1920，切成15块，分别推理，拼接结果"""
        import cv2
        import numpy as np

        # 1. 缩放到 3200x1920
        resized = cv2.resize(image, (NEW_WIDTH, NEW_HEIGHT))

        # 2. 存储所有检测结果
        all_boxes = []
        all_masks = []
        all_classes = []
        all_confs = []

        # 3. 分块推理 (5列 x 3行 = 15块)
        for row in range(NUM_ROWS):
            for col in range(NUM_COLS):
                x_start = col * TILE_SIZE
                y_start = row * TILE_SIZE
                tile = resized[y_start:y_start+TILE_SIZE, x_start:x_start+TILE_SIZE]

                # 推理单个 tile
                results = self.model(tile, conf=conf_threshold, verbose=False)[0]

                if results.boxes is not None:
                    for i, box in enumerate(results.boxes):
                        # 偏移坐标到原图位置
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1 += x_start
                        x2 += x_start
                        y1 += y_start
                        y2 += y_start
                        all_boxes.append([x1, y1, x2, y2])
                        all_classes.append(int(box.cls[0]))
                        all_confs.append(float(box.conf[0]))

                        # 处理 mask
                        if results.masks is not None and i < len(results.masks.data):
                            mask = results.masks.data[i].cpu().numpy()
                            # 创建全图大小的 mask
                            full_mask = np.zeros((NEW_HEIGHT, NEW_WIDTH), dtype=np.float32)
                            mask_resized = cv2.resize(mask, (TILE_SIZE, TILE_SIZE))
                            full_mask[y_start:y_start+TILE_SIZE, x_start:x_start+TILE_SIZE] = mask_resized
                            all_masks.append(full_mask)

        # 4. 统计各类别数量
        counts = {"leaf": 0, "terminal": 0, "flower": 0, "fruit": 0}
        for cls_id in all_classes:
            cls_name = CLASS_NAMES.get(cls_id, "unknown")
            if cls_name in counts:
                counts[cls_name] += 1

        # 5. 可视化
        vis_image = resized.copy()
        for i, mask in enumerate(all_masks):
            cls_name = CLASS_NAMES.get(all_classes[i], "unknown")
            color = CLASS_COLORS.get(cls_name, (255, 255, 255))
            mask_bool = mask > 0.5
            overlay = vis_image.copy()
            overlay[mask_bool] = color
            vis_image = cv2.addWeighted(vis_image, 0.7, overlay, 0.3, 0)

        for i, box in enumerate(all_boxes):
            x1, y1, x2, y2 = map(int, box)
            cls_name = CLASS_NAMES.get(all_classes[i], "unknown")
            color = CLASS_COLORS.get(cls_name, (255, 255, 255))
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            label = f"{cls_name}: {all_confs[i]:.2f}"
            cv2.putText(vis_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # 6. 保存结果
        image_name = Path(image_path).stem
        vis_path = OUTPUT_DIR / f"{image_name}_segmented.jpg"
        cv2.imwrite(str(vis_path), vis_image)

        metrics = {
            "leaf_instance_count": counts["leaf"],
            "terminal_count": counts["terminal"],
            "flower_count": counts["flower"],
            "fruit_count": counts["fruit"],
            "total_instances": sum(counts.values()),
            "visualization_path": str(vis_path),
            "processed_at": datetime.now().isoformat(),
            "is_mock": False,
            "tile_inference": True
        }

        metrics_path = METRICS_DIR / f"{image_name}_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        return metrics

    def _process_single(self, image, image_path, conf_threshold=0.25):
        """单次推理 (不分块)"""
        import cv2

        results = self.model(image, conf=conf_threshold, verbose=False)[0]

        counts = {"leaf": 0, "terminal": 0, "flower": 0, "fruit": 0}
        if results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                cls_name = CLASS_NAMES.get(cls_id, "unknown")
                if cls_name in counts:
                    counts[cls_name] += 1

        vis_image = image.copy()
        if results.masks is not None:
            for i, mask in enumerate(results.masks.data):
                cls_id = int(results.boxes.cls[i])
                cls_name = CLASS_NAMES.get(cls_id, "unknown")
                color = CLASS_COLORS.get(cls_name, (255, 255, 255))
                mask_np = mask.cpu().numpy()
                mask_resized = cv2.resize(mask_np, (image.shape[1], image.shape[0]))
                mask_bool = mask_resized > 0.5
                overlay = vis_image.copy()
                overlay[mask_bool] = color
                vis_image = cv2.addWeighted(vis_image, 0.7, overlay, 0.3, 0)

        if results.boxes is not None:
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                cls_name = CLASS_NAMES.get(cls_id, "unknown")
                color = CLASS_COLORS.get(cls_name, (255, 255, 255))
                conf = float(box.conf[0])
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
                label = f"{cls_name}: {conf:.2f}"
                cv2.putText(vis_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        image_name = Path(image_path).stem
        vis_path = OUTPUT_DIR / f"{image_name}_segmented.jpg"
        cv2.imwrite(str(vis_path), vis_image)

        metrics = {
            "leaf_instance_count": counts["leaf"],
            "terminal_count": counts["terminal"],
            "flower_count": counts["flower"],
            "fruit_count": counts["fruit"],
            "total_instances": sum(counts.values()),
            "visualization_path": str(vis_path),
            "processed_at": datetime.now().isoformat(),
            "is_mock": False,
            "tile_inference": False
        }

        metrics_path = METRICS_DIR / f"{image_name}_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        return metrics

    def get_cached_metrics(self, date_str):
        if "-" in date_str:
            parts = date_str.split("-")
            short_date = f"{parts[1]}{parts[2]}"
        else:
            short_date = date_str
        metrics_path = METRICS_DIR / f"{short_date}_metrics.json"
        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def process_date(self, date_str):
        if "-" in date_str:
            parts = date_str.split("-")
            short_date = f"{parts[1]}{parts[2]}"
        else:
            short_date = date_str
        for ext in [".jpg", ".JPG", ".jpeg", ".png"]:
            path = IMAGES_DIR / f"{short_date}{ext}"
            if path.exists():
                return self.process_image(str(path))
        raise FileNotFoundError(f"Image not found: {date_str}")

    def get_segmented_image_path(self, date_str):
        if "-" in date_str:
            parts = date_str.split("-")
            short_date = f"{parts[1]}{parts[2]}"
        else:
            short_date = date_str
        seg_path = OUTPUT_DIR / f"{short_date}_segmented.jpg"
        return seg_path if seg_path.exists() else None

    def process_bytes(self, image_bytes, filename, conf_threshold=0.25):
        """处理图像字节流 - 使用分块推理"""
        import cv2
        import numpy as np
        if not self.is_available:
            return self._mock_metrics(), None
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Cannot decode image")

        # 使用分块推理 (与 tuili.py 一致)
        # 1. 缩放到 3200x1920
        resized = cv2.resize(image, (NEW_WIDTH, NEW_HEIGHT))

        # 2. 存储所有检测结果
        all_masks_with_class = []  # [(mask, class_idx), ...]
        counts = {"leaf": 0, "terminal": 0, "flower": 0, "fruit": 0}

        # 3. 分块推理 (5列 x 3行 = 15块)
        for row in range(NUM_ROWS):
            for col in range(NUM_COLS):
                x_start = col * TILE_SIZE
                y_start = row * TILE_SIZE
                tile = resized[y_start:y_start+TILE_SIZE, x_start:x_start+TILE_SIZE]

                # 推理单个 tile
                results = self.model(tile, conf=conf_threshold, verbose=False)[0]

                if results.masks is not None and results.boxes is not None:
                    for i, (mask, cls_idx) in enumerate(zip(results.masks.data, results.boxes.cls)):
                        cls_id = int(cls_idx)
                        cls_name = CLASS_NAMES.get(cls_id, "unknown")
                        if cls_name in counts:
                            counts[cls_name] += 1

                        # 创建全图大小的 mask
                        mask_np = mask.cpu().numpy()
                        full_mask = np.zeros((NEW_HEIGHT, NEW_WIDTH), dtype=np.uint8)
                        mask_resized = cv2.resize(mask_np, (TILE_SIZE, TILE_SIZE))
                        full_mask[y_start:y_start+TILE_SIZE, x_start:x_start+TILE_SIZE] = (mask_resized > 0.5).astype(np.uint8) * 255
                        all_masks_with_class.append((full_mask, cls_id))

        # 4. 可视化 (与 tuili.py 一致的方式)
        mask_layer = np.zeros_like(resized, dtype=np.uint8)
        for mask, cls_id in all_masks_with_class:
            cls_name = CLASS_NAMES.get(cls_id, "unknown")
            color = CLASS_COLORS.get(cls_name, (255, 255, 255))
            colored_mask = np.zeros_like(resized, dtype=np.uint8)
            colored_mask[mask > 127] = color
            mask_layer = cv2.add(mask_layer, colored_mask)

        vis_image = cv2.addWeighted(resized, 1.0, mask_layer, 0.5, 0.0)

        # 5. 保存和返回
        vis_path = OUTPUT_DIR / f"{filename}_segmented.jpg"
        cv2.imwrite(str(vis_path), vis_image)
        _, vis_bytes = cv2.imencode(".jpg", vis_image)

        metrics = {
            "leaf_instance_count": counts["leaf"],
            "terminal_count": counts["terminal"],
            "flower_count": counts["flower"],
            "fruit_count": counts["fruit"],
            "total_instances": sum(counts.values()),
            "visualization_path": str(vis_path),
            "processed_at": datetime.now().isoformat(),
            "is_mock": False,
            "tile_inference": True
        }
        return metrics, vis_bytes.tobytes()

    def batch_process(self):
        results = []
        for ext in ["*.jpg", "*.JPG", "*.jpeg", "*.png"]:
            for img_path in IMAGES_DIR.glob(ext):
                try:
                    metrics = self.process_image(str(img_path))
                    results.append({"image": img_path.name, "success": True, "metrics": metrics})
                except Exception as e:
                    results.append({"image": img_path.name, "success": False, "error": str(e)})
        return results


yolo_service = YOLOService()

