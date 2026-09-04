"""PaddleOCR Engine — singleton initialization and per-image OCR.

Design:
  - PaddleOCR is initialized ONCE (lazily, on first use) and reused.
  - Initialization is thread-safe via a module-level lock.
  - The engine is loaded in the Celery worker process, not in the FastAPI process.
  - Graceful degradation: if PaddleOCR cannot initialize, all calls return
    empty results and log a warning. The pipeline continues.

Supported languages (PP-OCRv6):
  en (English), ch (Simplified Chinese), chinese_cht (Traditional Chinese),
  japan (Japanese), plus LATIN_LANGS (includes: hi for Devanagari via Indic pack)

For multilingual Indian documents, use lang='en' as default.
The model handles mixed-script documents reasonably well.

Configuration (via environment variables):
  PADDLE_OCR_LANG        Language code (default: "en")
  PADDLE_OCR_USE_ANGLE   Enable textline orientation correction (default: "false")
  PADDLE_OCR_DET_THRESH  Detection threshold 0.0–1.0 (default: "0.3")
  PADDLE_OCR_REC_THRESH  Recognition threshold 0.0–1.0 (default: "0.0")
  PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK  Set "True" to skip connectivity check
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

_LANG = os.environ.get("PADDLE_OCR_LANG", "hi")
_USE_ANGLE = os.environ.get("PADDLE_OCR_USE_ANGLE", "false").lower() == "true"
_DET_THRESH = float(os.environ.get("PADDLE_OCR_DET_THRESH", "0.3"))
_REC_THRESH = float(os.environ.get("PADDLE_OCR_REC_THRESH", "0.0"))
_DET_MODEL = os.environ.get("PADDLE_OCR_DET_MODEL", "PP-OCRv4_mobile_det")
_REC_MODEL = os.environ.get("PADDLE_OCR_REC_MODEL")
_REC_BATCH_SIZE = int(os.environ.get("PADDLE_OCR_REC_BATCH_SIZE", "8"))

# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------
_ocr_instance = None
_init_lock = threading.Lock()
_init_attempted = False
_init_failed = False
_init_error: str | None = None

# ---------------------------------------------------------------------------
# Optional import check
# ---------------------------------------------------------------------------
try:
    from paddleocr import PaddleOCR as _PaddleOCR

    _PADDLE_IMPORTABLE = True
except ImportError as _import_err:
    _PADDLE_IMPORTABLE = False
    _import_error_msg = str(_import_err)
    logger.warning(
        "paddleocr not importable — PaddleOCR engine disabled: %s", _import_err
    )


def _get_engine() -> "_PaddleOCR | None":
    """Return the shared PaddleOCR instance, initializing if needed.

    Thread-safe. Returns None if initialization fails.
    Never raises.
    """
    global _ocr_instance, _init_attempted, _init_failed, _init_error

    if not _PADDLE_IMPORTABLE:
        return None

    # Fast path: already initialized
    if _ocr_instance is not None:
        return _ocr_instance
    if _init_failed:
        return None

    with _init_lock:
        # Double-check after acquiring lock
        if _ocr_instance is not None:
            return _ocr_instance
        if _init_failed:
            return None

        _init_attempted = True

        rec_model = _REC_MODEL
        if not rec_model:
            if _LANG in ("hi", "mr", "ne", "sa", "devanagari"):
                rec_model = "devanagari_PP-OCRv5_mobile_rec"
            else:
                rec_model = "en_PP-OCRv5_mobile_rec"

        logger.info(
            "PaddleOCR: initializing engine (lang=%s, det=%s, rec=%s, angle_cls=%s, batch_size=%d)",
            _LANG, _DET_MODEL, rec_model, _USE_ANGLE, _REC_BATCH_SIZE,
        )
        try:
            # Fast path: mobile detection + mobile recognition with batch processing
            try:
                _ocr_instance = _PaddleOCR(
                    text_detection_model_name=_DET_MODEL,
                    text_recognition_model_name=rec_model,
                    text_recognition_batch_size=_REC_BATCH_SIZE,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=_USE_ANGLE,
                    text_det_thresh=_DET_THRESH,
                    text_rec_score_thresh=_REC_THRESH,
                )
            except Exception as opt_err:
                logger.warning(
                    "PaddleOCR: mobile model init failed, falling back to standard init: %s", opt_err
                )
                _ocr_instance = _PaddleOCR(
                    lang=_LANG,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=_USE_ANGLE,
                    text_det_thresh=_DET_THRESH,
                    text_rec_score_thresh=_REC_THRESH,
                )
            logger.info("PaddleOCR: engine initialized successfully (lang=%s)", _LANG)
        except Exception as exc:
            _init_failed = True
            _init_error = str(exc)
            logger.error(
                "PaddleOCR: initialization failed — OCR disabled: %s", exc, exc_info=True
            )
            return None

    return _ocr_instance


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def _poly_to_bbox(poly: list) -> list[float]:
    """Convert a 4-point polygon [[x,y],...] to [x1, y1, x2, y2] bbox."""
    try:
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        return [min(xs), min(ys), max(xs), max(ys)]
    except Exception:
        return [0.0, 0.0, 0.0, 0.0]


def _parse_result(paddle_result) -> list[dict]:
    """Parse a single PaddleOCR result object (dict/json/list) into block dicts.

    Each dict has keys: text, bbox, confidence, poly.
    Returns empty list on any parsing error.
    """
    blocks: list[dict] = []
    if paddle_result is None:
        return blocks

    try:
        # Case A: Object with .json property (Paddlex / PaddleOCR 3.x predict)
        res = {}
        if hasattr(paddle_result, "json"):
            json_data = paddle_result.json
            if isinstance(json_data, dict):
                res = json_data.get("res", json_data)
        elif isinstance(paddle_result, dict):
            res = paddle_result.get("res", paddle_result)

        if isinstance(res, dict) and "rec_texts" in res:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            polys = res.get("rec_polys", res.get("dt_polys", []))
            boxes = res.get("rec_boxes", [])

            for i, text in enumerate(texts):
                if not text or not str(text).strip():
                    continue

                confidence = float(scores[i]) if i < len(scores) else 0.0
                if i < len(boxes) and boxes[i]:
                    b = boxes[i]
                    bbox = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]
                elif i < len(polys) and polys[i]:
                    bbox = _poly_to_bbox(polys[i])
                else:
                    bbox = [0.0, 0.0, 0.0, 0.0]

                poly = polys[i] if i < len(polys) else []

                blocks.append({
                    "text": str(text).strip(),
                    "bbox": bbox,
                    "confidence": round(confidence, 6),
                    "poly": poly,
                })
            return blocks

        # Case B: Standard PaddleOCR ocr() list structure: [[[box], (text, score)], ...]
        if isinstance(paddle_result, list):
            for item in paddle_result:
                if isinstance(item, list) and len(item) >= 2:
                    poly = item[0]
                    text_score = item[1]
                    if isinstance(text_score, (tuple, list)) and len(text_score) >= 2:
                        txt = str(text_score[0]).strip()
                        conf = float(text_score[1])
                        if txt:
                            blocks.append({
                                "text": txt,
                                "bbox": _poly_to_bbox(poly),
                                "confidence": round(conf, 6),
                                "poly": poly,
                            })

    except Exception as exc:
        logger.warning("PaddleOCR: result parsing error: %s", exc, exc_info=True)

    return blocks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_paddle_ocr_on_image(
    image: "PILImage",
    page_num: int = 1,
    ocr_engine: str = "paddle",
) -> dict:
    """Run PaddleOCR on a single PIL Image.

    Returns a page-level OCR dict matching the normalized schema::

        {
            "page": 1,
            "width": 1240,
            "height": 1754,
            "blocks": [
                {
                    "text": "Survey No: 245/A",
                    "bbox": [18.0, 39.0, 101.0, 52.0],
                    "confidence": 0.9987,
                    "language": null,
                    "ocr_engine": "paddle",
                    "timestamp": "2026-09-04T13:00:00"
                }
            ]
        }

    Never raises — returns empty blocks on failure.
    """
    w, h = image.size
    page_dict = {
        "page": page_num,
        "width": w,
        "height": h,
        "blocks": [],
    }

    engine = _get_engine()
    if engine is None:
        logger.warning(
            "PaddleOCR: engine not available for page %d — returning empty", page_num
        )
        return page_dict

    try:
        # PaddleOCR 3.x accepts PIL Images, numpy arrays, or file paths
        img_array = np.array(image.convert("RGB"))

        results = engine.predict(img_array)
        if not results:
            logger.info("PaddleOCR: no results for page %d", page_num)
            return page_dict

        ts = datetime.utcnow().isoformat()
        raw_blocks = _parse_result(results[0])

        page_dict["blocks"] = [
            {
                "text": b["text"],
                "bbox": b["bbox"],
                "confidence": b["confidence"],
                "language": None,   # PaddleOCR 3.x doesn't return per-block lang
                "ocr_engine": ocr_engine,
                "timestamp": ts,
            }
            for b in raw_blocks
        ]

        logger.info(
            "PaddleOCR: page %d — %d blocks extracted",
            page_num, len(page_dict["blocks"]),
        )

    except Exception as exc:
        logger.error(
            "PaddleOCR: error processing page %d: %s", page_num, exc, exc_info=True
        )

    return page_dict


def get_engine_status() -> dict:
    """Return engine initialization status for health-checks/diagnostics."""
    return {
        "importable": _PADDLE_IMPORTABLE,
        "initialized": _ocr_instance is not None,
        "init_attempted": _init_attempted,
        "init_failed": _init_failed,
        "init_error": _init_error,
        "lang": _LANG,
        "use_angle_cls": _USE_ANGLE,
    }
