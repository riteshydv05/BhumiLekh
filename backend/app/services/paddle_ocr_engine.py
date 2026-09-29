"""PaddleOCR Engine — dynamic multi-language engine registry and per-image OCR.

Design:
  - PaddleOCR instances are lazily instantiated per script/language and cached in a thread-safe registry.
  - Supports Indic scripts (Devanagari, Tamil, Telugu, Kannada, Malayalam, Gujarati, Bengali, Punjabi) as well as English.
  - Script detection automatically resolves script codes from text or explicit requested language.
  - Graceful degradation: if PaddleOCR cannot initialize for a language, all calls return
    empty results and log a warning.
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

_DEFAULT_LANG = os.environ.get("PADDLE_OCR_LANG", "hi")
_USE_ANGLE = os.environ.get("PADDLE_OCR_USE_ANGLE", "false").lower() == "true"
_DET_THRESH = float(os.environ.get("PADDLE_OCR_DET_THRESH", "0.3"))
_REC_THRESH = float(os.environ.get("PADDLE_OCR_REC_THRESH", "0.0"))
_DET_MODEL = os.environ.get("PADDLE_OCR_DET_MODEL", "PP-OCRv4_mobile_det")
_REC_MODEL = os.environ.get("PADDLE_OCR_REC_MODEL")
_REC_BATCH_SIZE = int(os.environ.get("PADDLE_OCR_REC_BATCH_SIZE", "8"))

# Language alias mapping to PaddleOCR language codes / models
LANG_MAP: dict[str, str] = {
    "hi": "hi", "hindi": "hi", "mr": "hi", "marathi": "hi", "ne": "hi", "sa": "hi", "devanagari": "hi",
    "en": "en", "english": "en",
    "ta": "ta", "tamil": "ta",
    "te": "te", "telugu": "te",
    "kn": "kn", "kannada": "kn",
    "ml": "ml", "malayalam": "ml",
    "gu": "gu", "gujarati": "gu",
    "bn": "bn", "bengali": "bn",
    "pa": "pa", "punjabi": "pa",
    "or": "or", "odia": "or",
}

# ---------------------------------------------------------------------------
# Engine Registry state (Thread-safe)
# ---------------------------------------------------------------------------
_ocr_registry: dict = {}
_init_lock = threading.Lock()
_failed_languages: set = set()

# ---------------------------------------------------------------------------
# Optional import check
# ---------------------------------------------------------------------------
try:
    from paddleocr import PaddleOCR as _PaddleOCR

    _PADDLE_IMPORTABLE = True
except ImportError as _import_err:
    _PADDLE_IMPORTABLE = False
    logger.warning("paddleocr not importable — PaddleOCR engine disabled: %s", _import_err)


def detect_script(text: str) -> str:
    """Detect script language code from text using Unicode ranges."""
    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    tamil_count = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    telugu_count = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    kannada_count = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
    malayalam_count = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
    gujarati_count = sum(1 for c in text if '\u0A80' <= c <= '\u0AFF')
    bengali_count = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    punjabi_count = sum(1 for c in text if '\u0A00' <= c <= '\u0A7F')
    odia_count = sum(1 for c in text if '\u0B00' <= c <= '\u0B7F')

    counts = {
        "hi": devanagari_count,
        "ta": tamil_count,
        "te": telugu_count,
        "kn": kannada_count,
        "ml": malayalam_count,
        "gu": gujarati_count,
        "bn": bengali_count,
        "pa": punjabi_count,
        "or": odia_count,
    }

    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang
    return "en"


def _normalize_lang(lang: str | None) -> str:
    if not lang or lang == "auto":
        return LANG_MAP.get(_DEFAULT_LANG, "hi")
    clean = lang.lower().strip()
    return LANG_MAP.get(clean, "hi")


def _get_engine(lang: str = "hi"):
    """Return the shared PaddleOCR instance for the requested language.

    Thread-safe. Lazy loading per language. Returns None on failure.
    """
    if not _PADDLE_IMPORTABLE:
        return None

    norm_lang = _normalize_lang(lang)

    if norm_lang in _ocr_registry:
        return _ocr_registry[norm_lang]
    if norm_lang in _failed_languages:
        return None

    with _init_lock:
        if norm_lang in _ocr_registry:
            return _ocr_registry[norm_lang]
        if norm_lang in _failed_languages:
            return None

        rec_model = _REC_MODEL
        if not rec_model:
            if norm_lang == "hi":
                rec_model = "devanagari_PP-OCRv5_mobile_rec"
            elif norm_lang == "en":
                rec_model = "en_PP-OCRv5_mobile_rec"
            else:
                rec_model = None

        logger.info(
            "PaddleOCR: initializing engine for lang=%s (det=%s, rec=%s)",
            norm_lang, _DET_MODEL, rec_model or "default",
        )
        try:
            if rec_model:
                engine = _PaddleOCR(
                    text_detection_model_name=_DET_MODEL,
                    text_recognition_model_name=rec_model,
                    text_recognition_batch_size=_REC_BATCH_SIZE,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=_USE_ANGLE,
                    text_det_thresh=_DET_THRESH,
                    text_rec_score_thresh=_REC_THRESH,
                )
            else:
                engine = _PaddleOCR(
                    lang=norm_lang,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=_USE_ANGLE,
                    text_det_thresh=_DET_THRESH,
                    text_rec_score_thresh=_REC_THRESH,
                )
            _ocr_registry[norm_lang] = engine
            logger.info("PaddleOCR: engine initialized successfully for lang=%s", norm_lang)
            return engine
        except Exception as exc:
            logger.warning(
                "PaddleOCR: specific init for lang=%s failed (%s), falling back to lang parameter init",
                norm_lang, exc
            )
            try:
                engine = _PaddleOCR(
                    lang=norm_lang,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=_USE_ANGLE,
                )
                _ocr_registry[norm_lang] = engine
                return engine
            except Exception as exc2:
                _failed_languages.add(norm_lang)
                logger.error(
                    "PaddleOCR: initialization failed for lang=%s — %s", norm_lang, exc2
                )
                return None


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
    """Parse a single PaddleOCR result object into block dicts."""
    blocks: list[dict] = []
    if paddle_result is None:
        return blocks

    try:
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
    lang: str = "auto",
) -> dict:
    """Run PaddleOCR on a single PIL Image with script/language routing.

    Never raises — returns empty blocks on failure.
    """
    w, h = image.size
    page_dict = {
        "page": page_num,
        "width": w,
        "height": h,
        "blocks": [],
    }

    engine = _get_engine(lang=lang)
    if engine is None:
        # Retry fallback with default language
        engine = _get_engine(lang="hi")

    if engine is None:
        logger.warning(
            "PaddleOCR: engine not available for page %d (lang=%s) — returning empty",
            page_num, lang,
        )
        return page_dict

    try:
        img_array = np.array(image.convert("RGB"))

        results = engine.predict(img_array) if hasattr(engine, "predict") else engine.ocr(img_array)
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
                "language": lang if lang != "auto" else detect_script(b["text"]),
                "ocr_engine": ocr_engine,
                "timestamp": ts,
            }
            for b in raw_blocks
        ]

        logger.info(
            "PaddleOCR: page %d (lang=%s) — %d blocks extracted",
            page_num, lang, len(page_dict["blocks"]),
        )

    except Exception as exc:
        logger.error(
            "PaddleOCR: error processing page %d (lang=%s): %s",
            page_num, lang, exc, exc_info=True,
        )

    return page_dict


def get_engine_status() -> dict:
    """Return engine initialization status for health-checks/diagnostics."""
    return {
        "importable": _PADDLE_IMPORTABLE,
        "initialized": len(_ocr_registry) > 0,
        "lang": _DEFAULT_LANG,
        "loaded_languages": list(_ocr_registry.keys()),
        "failed_languages": list(_failed_languages),
        "use_angle_cls": _USE_ANGLE,
    }
