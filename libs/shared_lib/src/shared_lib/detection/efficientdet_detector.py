"""Lightweight EfficientDet-Lite0 wrapper using tflite_runtime.

Downloads the int8 model on first use and keeps the interpreter alive
across frames (unlike Vilib which re-creates it every call).
"""

from __future__ import annotations

import logging
import os
import urllib.request
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_URL = (
    "https://raw.githubusercontent.com/google-coral/test_data/"
    "master/efficientdet_lite0_320_ptq.tflite"
)
_MODEL_DIR = Path(__file__).parent / "models"
_MODEL_PATH = _MODEL_DIR / "efficientdet_lite0_320_ptq.tflite"

# Full COCO 2017 label set (91 entries, index 0 is background).
# Embedded here to avoid Vilib's load_labels() bug with multi-word labels.
COCO_LABELS: tuple[str, ...] = (
    "",             # 0  background
    "person",       # 1
    "bicycle",      # 2
    "car",          # 3
    "motorcycle",   # 4
    "airplane",     # 5
    "bus",          # 6
    "train",        # 7
    "truck",        # 8
    "boat",         # 9
    "traffic light", # 10
    "fire hydrant", # 11
    "",             # 12
    "stop sign",    # 13
    "parking meter", # 14
    "bench",        # 15
    "bird",         # 16
    "cat",          # 17
    "dog",          # 18
    "horse",        # 19
    "sheep",        # 20
    "cow",          # 21
    "elephant",     # 22
    "bear",         # 23
    "zebra",        # 24
    "giraffe",      # 25
    "",             # 26
    "backpack",     # 27
    "umbrella",     # 28
    "",             # 29
    "",             # 30
    "handbag",      # 31
    "tie",          # 32
    "suitcase",     # 33
    "frisbee",      # 34
    "skis",         # 35
    "snowboard",    # 36
    "sports ball",  # 37
    "kite",         # 38
    "baseball bat", # 39
    "baseball glove", # 40
    "skateboard",   # 41
    "surfboard",    # 42
    "tennis racket", # 43
    "bottle",       # 44
    "",             # 45
    "wine glass",   # 46
    "cup",          # 47
    "fork",         # 48
    "knife",        # 49
    "spoon",        # 50
    "bowl",         # 51
    "banana",       # 52
    "apple",        # 53
    "sandwich",     # 54
    "orange",       # 55
    "broccoli",     # 56
    "carrot",       # 57
    "hot dog",      # 58
    "pizza",        # 59
    "donut",        # 60
    "cake",         # 61
    "chair",        # 62
    "couch",        # 63
    "potted plant", # 64
    "bed",          # 65
    "",             # 66
    "dining table", # 67
    "",             # 68
    "",             # 69
    "toilet",       # 70
    "",             # 71
    "tv",           # 72
    "laptop",       # 73
    "mouse",        # 74
    "remote",       # 75
    "keyboard",     # 76
    "cell phone",   # 77
    "microwave",    # 78
    "oven",         # 79
    "toaster",      # 80
    "sink",         # 81
    "refrigerator", # 82
    "",             # 83
    "book",         # 84
    "clock",        # 85
    "vase",         # 86
    "scissors",     # 87
    "teddy bear",   # 88
    "hair drier",   # 89
    "toothbrush",   # 90
)

_NMS_IOU_THRESHOLD = 0.5

# SSD box-decoding scale factors (standard values for EfficientDet / MobileNet SSD)
_BOX_SCALE_Y = 10.0
_BOX_SCALE_X = 10.0
_BOX_SCALE_H = 5.0
_BOX_SCALE_W = 5.0

# EfficientDet-Lite0 feature pyramid strides and anchors per spatial location
_FEATURE_STRIDES = (8, 16, 32, 64, 128)
_ANCHORS_PER_LOC = 9  # 3 scales x 3 aspect ratios

_BOX_COLORS = (
    (0, 255, 255),
    (255, 0, 0),
    (0, 255, 64),
    (255, 255, 0),
    (255, 128, 64),
    (128, 128, 255),
    (255, 128, 255),
    (255, 128, 128),
)


def _ensure_model() -> Path:
    """Download EfficientDet-Lite0 int8 if not present. Returns model path."""
    if _MODEL_PATH.exists():
        return _MODEL_PATH
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading EfficientDet-Lite0 model to %s ...", _MODEL_PATH)
    try:
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    except Exception:
        if _MODEL_PATH.exists():
            _MODEL_PATH.unlink()
        raise
    logger.info("Model download complete (%d bytes)", _MODEL_PATH.stat().st_size)
    return _MODEL_PATH


class EfficientDetDetector:
    """Run EfficientDet-Lite0 inference via tflite_runtime.

    The interpreter is created once and reused across frames.
    """

    def __init__(self, model_path: str | os.PathLike[str] | None = None) -> None:
        from tflite_runtime.interpreter import Interpreter

        path = str(model_path) if model_path else str(_ensure_model())
        self._interpreter = Interpreter(model_path=path)
        self._interpreter.allocate_tensors()

        input_detail = self._interpreter.get_input_details()[0]
        _, self._input_h, self._input_w, _ = input_detail["shape"]
        self._input_index = input_detail["index"]

        self._output_map = self._map_outputs(
            self._interpreter.get_output_details()
        )
        self._pre_nms = "raw_scores" in self._output_map
        self._anchors: np.ndarray | None = None
        if self._pre_nms:
            self._anchors = self._generate_anchors()
        logger.info(
            "EfficientDetDetector ready (input %dx%d, pre_nms=%s, anchors=%s, outputs=%s)",
            self._input_w,
            self._input_h,
            self._pre_nms,
            self._anchors.shape if self._anchors is not None else None,
            self._output_map,
        )

    def _generate_anchors(self) -> np.ndarray:
        """Generate SSD anchor centers for EfficientDet-Lite0.

        With fixed_anchor_size=True all anchors at a location share the same
        center and have unit width/height.  Returns (num_anchors, 2) array
        of (cy, cx) normalised to [0, 1].
        """
        anchors: list[tuple[float, float]] = []
        for stride in _FEATURE_STRIDES:
            feat_h = -(-self._input_h // stride)  # ceil division
            feat_w = -(-self._input_w // stride)
            for y in range(feat_h):
                for x in range(feat_w):
                    cy = (y + 0.5) / feat_h
                    cx = (x + 0.5) / feat_w
                    for _ in range(_ANCHORS_PER_LOC):
                        anchors.append((cy, cx))
        return np.array(anchors, dtype=np.float32)

    def _decode_boxes(self, raw_boxes: np.ndarray) -> np.ndarray:
        """Decode raw SSD box offsets to [ymin, xmin, ymax, xmax] normalised.

        MediaPipe EfficientDet uses reverse_output_order, so the raw columns
        are [dx, dy, dw, dh] (x-first) instead of the standard [dy, dx, dh, dw].
        With fixed_anchor_size the anchor w/h is 1.0, so decoding simplifies.
        """
        assert self._anchors is not None
        cx = raw_boxes[:, 0] / _BOX_SCALE_X + self._anchors[:, 1]
        cy = raw_boxes[:, 1] / _BOX_SCALE_Y + self._anchors[:, 0]
        w = np.exp(np.clip(raw_boxes[:, 2] / _BOX_SCALE_W, -10, 10))
        h = np.exp(np.clip(raw_boxes[:, 3] / _BOX_SCALE_H, -10, 10))

        boxes = np.stack([cy - h / 2, cx - w / 2, cy + h / 2, cx + w / 2], axis=1)
        np.clip(boxes, 0.0, 1.0, out=boxes)
        return boxes

    @staticmethod
    def _map_outputs(details: list[dict]) -> dict[str, int]:
        """Identify output tensors by name, then shape, then position."""
        for d in details:
            logger.info(
                "  TFLite output: name=%-40s shape=%-15s dtype=%s idx=%d",
                d["name"],
                str(tuple(d["shape"])),
                d["dtype"],
                d["index"],
            )

        # --- try name-based matching first ---
        mapping: dict[str, int] = {}
        for d in details:
            name = d["name"].lower()
            idx = d["index"]
            if any(k in name for k in ("location", "box")):
                mapping.setdefault("boxes", idx)
            elif any(k in name for k in ("category", "class")):
                mapping.setdefault("classes", idx)
            elif "score" in name:
                mapping.setdefault("scores", idx)
            elif any(k in name for k in ("count", "number", "num_det")):
                mapping.setdefault("count", idx)
        if len(mapping) == 4:
            return mapping

        # --- fallback: identify by shape/dtype ---
        mapping = {}
        for d in details:
            idx = d["index"]
            shape = tuple(d["shape"])
            if len(shape) == 3 and shape[-1] == 4 and "boxes" not in mapping:
                mapping["boxes"] = idx
            elif shape == (1,) and "count" not in mapping:
                mapping["count"] = idx
            elif (
                len(shape) == 2
                and np.issubdtype(d["dtype"], np.integer)
                and "classes" not in mapping
            ):
                mapping["classes"] = idx
            elif (
                len(shape) == 2
                and np.issubdtype(d["dtype"], np.floating)
                and "scores" not in mapping
            ):
                mapping["scores"] = idx
        if len(mapping) == 4:
            return mapping

        # --- pre-NMS format: 2 outputs (raw_boxes, raw_scores) ---
        raw_boxes_idx = None
        raw_scores_idx = None
        for d in details:
            shape = tuple(d["shape"])
            if len(shape) == 3 and shape[-1] == 4:
                raw_boxes_idx = d["index"]
            elif len(shape) == 3 and shape[-1] > 4:
                raw_scores_idx = d["index"]
        if raw_boxes_idx is not None and raw_scores_idx is not None:
            return {"raw_boxes": raw_boxes_idx, "raw_scores": raw_scores_idx}

        # --- last resort: positional (standard SSD order) ---
        if len(details) >= 4:
            indices = [d["index"] for d in details]
            return {
                "boxes": indices[0],
                "classes": indices[1],
                "scores": indices[2],
                "count": indices[3],
            }

        raise RuntimeError(
            f"Cannot identify EfficientDet output tensors. "
            f"Found {len(details)} output(s): "
            f"{[(d['name'], tuple(d['shape']), str(d['dtype'])) for d in details]}"
        )

    def detect(self, img: np.ndarray, threshold: float = 0.3) -> list[dict]:
        """Run inference on a BGR image.

        Returns list of dicts with keys:
          class_id, class_name, score, bounding_box (ymin, xmin, ymax, xmax normalised)
        """
        h, w = img.shape[:2]
        resized = cv2.resize(img, (self._input_w, self._input_h))
        # Model expects RGB uint8
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        self._interpreter.tensor(self._input_index)()[0][:, :] = rgb
        self._interpreter.invoke()

        if self._pre_nms:
            return self._decode_pre_nms(h, w, threshold)
        return self._decode_post_nms(h, w, threshold)

    def _decode_post_nms(self, h: int, w: int, threshold: float) -> list[dict]:
        """Decode outputs from a model with built-in NMS (4 output tensors)."""
        boxes = np.squeeze(
            self._interpreter.get_tensor(self._output_map["boxes"])
        )
        classes = np.squeeze(
            self._interpreter.get_tensor(self._output_map["classes"])
        )
        scores = np.squeeze(
            self._interpreter.get_tensor(self._output_map["scores"])
        )
        count = int(
            np.squeeze(
                self._interpreter.get_tensor(self._output_map["count"])
            )
        )

        results: list[dict] = []
        for i in range(count):
            score = float(scores[i])
            if score < threshold:
                continue
            # Model uses 0-indexed classes (0=person); COCO_LABELS[0] is background
            class_id = int(classes[i]) + 1
            results.append(self._make_detection(class_id, score, boxes[i], h, w))
        return results

    def _decode_pre_nms(self, h: int, w: int, threshold: float) -> list[dict]:
        """Decode raw outputs and apply NMS (2 output tensors, no built-in NMS)."""
        raw_scores = np.squeeze(
            self._interpreter.get_tensor(self._output_map["raw_scores"])
        )  # (num_anchors, num_classes)
        raw_boxes = np.squeeze(
            self._interpreter.get_tensor(self._output_map["raw_boxes"])
        )  # (num_anchors, 4) — encoded [dy, dx, dh, dw]

        # Raw score outputs are logits; apply sigmoid to get probabilities
        raw_scores = 1.0 / (1.0 + np.exp(-np.clip(raw_scores, -50, 50)))

        # Decode anchor-relative offsets to absolute [ymin, xmin, ymax, xmax]
        decoded_boxes = self._decode_boxes(raw_boxes)

        # Best class per anchor
        best_class_indices = np.argmax(raw_scores, axis=1)
        best_scores = np.max(raw_scores, axis=1)

        # Filter by threshold
        mask = best_scores >= threshold
        above = np.where(mask)[0]
        if len(above) == 0:
            return []

        filtered_scores = best_scores[above]
        filtered_classes = best_class_indices[above]
        filtered_boxes = decoded_boxes[above]

        # Convert [ymin, xmin, ymax, xmax] normalised -> [x, y, w, h] for NMS
        nms_boxes = []
        for box in filtered_boxes:
            ymin, xmin, ymax, xmax = box
            nms_boxes.append(
                [float(xmin), float(ymin), float(xmax - xmin), float(ymax - ymin)]
            )

        nms_indices = cv2.dnn.NMSBoxes(
            nms_boxes, filtered_scores.tolist(), threshold, _NMS_IOU_THRESHOLD
        )
        if len(nms_indices) == 0:
            return []

        results: list[dict] = []
        for idx in np.asarray(nms_indices).flatten():
            # Model has no background class; output index 0 = COCO label 1 (person)
            class_id = int(filtered_classes[idx]) + 1
            score = float(filtered_scores[idx])
            results.append(
                self._make_detection(class_id, score, filtered_boxes[idx], h, w)
            )
        return results

    @staticmethod
    def _make_detection(
        class_id: int, score: float, box: np.ndarray, h: int, w: int
    ) -> dict:
        class_name = (
            COCO_LABELS[class_id]
            if 0 <= class_id < len(COCO_LABELS)
            else f"id:{class_id}"
        )
        ymin, xmin, ymax, xmax = (float(v) for v in box)
        return {
            "class_id": class_id,
            "class_name": class_name,
            "score": score,
            "bounding_box": (ymin, xmin, ymax, xmax),
            "x": int(xmin * w),
            "y": int(ymin * h),
            "w": int((xmax - xmin) * w),
            "h": int((ymax - ymin) * h),
            "img_width": w,
            "img_height": h,
        }

    @staticmethod
    def draw(
        img: np.ndarray,
        detections: list[dict],
        allowed_classes: frozenset[str] | None = None,
        min_score: float = 0.0,
    ) -> np.ndarray:
        """Draw filtered bounding boxes onto *img* (in-place). Returns img."""
        drawn = 0
        for det in detections:
            if det["score"] < min_score:
                continue
            if allowed_classes is not None and det["class_name"] not in allowed_classes:
                continue
            x, y, w, h = det["x"], det["y"], det["w"], det["h"]
            color = _BOX_COLORS[drawn % len(_BOX_COLORS)]
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                img,
                f"{det['class_name']} {det['score']:.2f}",
                (x + 6, y + 18),
                cv2.FONT_HERSHEY_PLAIN,
                1.2,
                color,
                1,
                cv2.LINE_AA,
            )
            drawn += 1
        return img
