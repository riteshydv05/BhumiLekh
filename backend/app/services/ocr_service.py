"""OCR Service — multilingual document text extraction.

Full pipeline position
----------------------

    Upload Document
          ↓
    Document Preprocessing
          ↓
    Script / Language Detection  ← script_detector.py  (lightweight, pre-OCR)
          ↓                         3-stage cascade:
          │                           1. Embedded text probe  (PDF text-layer)
          │                           2. Tesseract OSD        (image-based)
          │                           3. Fast OCR probe       (Unicode counting)
          ↓
    OCR Router
     ┌──────┬──────┬──────┬──────┐
    Hindi  Tamil Telugu Kannada English  …
     └──────┴──────┴──────┴──────┘
          ↓
    Text Extraction
          ↓
    Land-Field Extraction
          ↓
    Validation / Verification
          ↓
    Structured Record → PostgreSQL / PostGIS

Engine priority (per document type)
------------------------------------
PDF documents:
  1. PaddleOCR (primary) — converts each page to an image, runs PP-OCRv4/v6
  2. pypdf text extraction (fallback) — pure-Python, works on text-based PDFs

Image documents (JPEG/PNG/TIFF):
  1. PaddleOCR (primary)
  2. Tesseract via pytesseract (fallback, requires system binary)

All results are returned as both:
  - ``OCRResult``   — legacy flat struct (backward compatible with existing pipeline)
  - ``OcrDocument`` — normalized block-level struct with bounding boxes and confidence
                      (for LayoutLMv3 and downstream spatial processing)

Key public functions
--------------------
``run_ocr_with_script_detection()``
    **Preferred entry point.**  Auto-detects script/language FIRST (no manual
    language selection needed), then routes to the matching OCR engine.
    Returns a combined dict with both the detection result and OCR output.

``run_ocr()``
    Lower-level function that accepts an explicit ``language`` parameter.
    Used internally and for cases where language is already known.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports — each engine degrades gracefully
# ---------------------------------------------------------------------------
try:
    import pypdf  # noqa: F401
    _PYPDF_AVAILABLE = True
except ImportError:
    _PYPDF_AVAILABLE = False
    logger.warning("pypdf not installed; PDF text fallback unavailable")

try:
    import pytesseract
    from PIL import Image as _PILImage  # noqa: F401
    _TESSERACT_AVAILABLE = True
    pytesseract.get_tesseract_version()
except Exception:
    _TESSERACT_AVAILABLE = False
    logger.warning(
        "Tesseract binary not found or pytesseract not installed. "
        "Image OCR fallback is disabled. Install: brew install tesseract tesseract-lang"
    )

try:
    from PIL import Image as _PILImageCheck  # noqa: F401
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False


# ---------------------------------------------------------------------------
# Backward-compatible flat result (consumed by existing pipeline stages)
# ---------------------------------------------------------------------------

@dataclass
class OCRResult:
    """Flat OCR result — backward-compatible with the existing pipeline."""

    text: str = ""
    page_count: int = 0
    confidence: float = 0.0
    method: str = "none"
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    # Extended: holds the normalized per-page block structure
    pages: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal: pypdf text-layer extraction (PDF only, no image rasterisation)
# ---------------------------------------------------------------------------

def _extract_text_pdf_pypdf(file_bytes: bytes) -> tuple[str, int, list[dict]]:
    """Extract embedded text from PDF using pypdf.

    Returns (full_text, page_count, pages_list).
    pages_list uses the normalized page dict schema (no bounding boxes).
    Raises RuntimeError if pypdf is unavailable.
    """
    if not _PYPDF_AVAILABLE:
        raise RuntimeError("pypdf is not installed")

    import pypdf  # local import

    reader = pypdf.PdfReader(BytesIO(file_bytes))
    page_count = len(reader.pages)
    full_pages: list[dict] = []
    all_text: list[str] = []

    ts = datetime.utcnow().isoformat()
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            logger.warning("pypdf: page %d extraction failed: %s", i + 1, exc)
            text = ""

        all_text.append(text)
        # Build normalized page dict — no bbox info available from text layer
        blocks = []
        if text.strip():
            blocks.append({
                "text": text,
                "bbox": [0.0, 0.0, 0.0, 0.0],   # No spatial info from pypdf
                "confidence": 1.0,
                "language": None,
                "ocr_engine": "pypdf_text",
                "timestamp": ts,
            })

        full_pages.append({
            "page": i + 1,
            "width": 0,
            "height": 0,
            "blocks": blocks,
        })

    full_text = "\n".join(all_text)
    logger.info(
        "pypdf: extracted %d pages, %d chars", page_count, len(full_text)
    )
    return full_text, page_count, full_pages


# ---------------------------------------------------------------------------
# Internal: Tesseract image OCR (fallback for images when PaddleOCR fails)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Internal: Tesseract image OCR (fallback for images when PaddleOCR fails)
# ---------------------------------------------------------------------------

_TESSERACT_LANG_MAP: dict[str, list[str]] = {
    "ta": ["tam+eng", "tam"],
    "tamil": ["tam+eng", "tam"],
    "hi": ["hin+eng", "hin"],
    "hindi": ["hin+eng", "hin"],
    "mr": ["mar+hin+eng", "mar+eng", "mar"],
    "marathi": ["mar+hin+eng", "mar+eng", "mar"],
    "gu": ["guj+eng", "guj"],
    "gujarati": ["guj+eng", "guj"],
    "te": ["tel+eng", "tel"],
    "telugu": ["tel+eng", "tel"],
    "kn": ["kan+eng", "kan"],
    "kannada": ["kan+eng", "kan"],
    "ml": ["mal+eng", "mal"],
    "malayalam": ["mal+eng", "mal"],
    "bn": ["ben+eng", "ben"],
    "bengali": ["ben+eng", "ben"],
    "pa": ["pan+eng", "pan"],
    "punjabi": ["pan+eng", "pan"],
    "en": ["eng"],
    "english": ["eng"],
}


def _extract_text_image_tesseract(
    image_bytes: bytes, language: str = "auto"
) -> tuple[str, float]:
    """Tesseract OCR on a single image. Returns (text, avg_confidence)."""
    if not _TESSERACT_AVAILABLE:
        raise RuntimeError(
            "Tesseract not available. Install: brew install tesseract tesseract-lang"
        )

    import pytesseract  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    img = Image.open(BytesIO(image_bytes)).convert("L")  # grayscale

    lang_key = (language or "auto").lower().strip()
    if lang_key in _TESSERACT_LANG_MAP:
        langs_to_try = _TESSERACT_LANG_MAP[lang_key] + ["tam+hin+mar+tel+kan+guj+ben+eng", "eng"]
    else:
        langs_to_try = [
            "tam+hin+mar+tel+kan+guj+ben+eng",
            "tam+eng",
            "hin+eng",
            "mar+hin+eng",
            "tel+eng",
            "kan+eng",
            "eng",
        ]

    data = None
    for lang_code in langs_to_try:
        try:
            data = pytesseract.image_to_data(
                img,
                lang=lang_code,
                output_type=pytesseract.Output.DICT,
            )
            if data and any(str(t).strip() for t in data.get("text", [])):
                logger.info("Tesseract succeeded with lang='%s'", lang_code)
                break
        except Exception:
            continue

    if not data:
        data = pytesseract.image_to_data(
            img,
            output_type=pytesseract.Output.DICT,
        )

    words = [
        (data["text"][i], int(data["conf"][i]))
        for i in range(len(data["text"]))
        if data["conf"][i] != -1 and str(data["text"][i]).strip()
    ]
    text = " ".join(w for w, _ in words)
    avg_conf = (
        sum(c for _, c in words) / len(words) / 100.0 if words else 0.0
    )
    return text, avg_conf


# ---------------------------------------------------------------------------
# Primary: PaddleOCR pipeline (PDF via image rendering + direct image)
# ---------------------------------------------------------------------------

def _run_paddle_on_pdf(file_bytes: bytes, language: str = "auto") -> tuple[list[dict], int, float]:
    """Render each PDF page and run PaddleOCR.

    Returns (pages_list, page_count, avg_confidence).
    """
    from app.services.pdf_renderer import render_pdf_pages
    from app.services.paddle_ocr_engine import run_paddle_ocr_on_image

    page_renders = render_pdf_pages(file_bytes)
    if not page_renders:
        raise RuntimeError("pdf_renderer returned no pages — cannot run PaddleOCR on PDF")

    page_count = len(page_renders)
    pages: list[dict] = []
    all_conf: list[float] = []

    for page_num, pil_img, w, h in page_renders:
        page_dict = run_paddle_ocr_on_image(pil_img, page_num=page_num, lang=language)
        pages.append(page_dict)
        for block in page_dict["blocks"]:
            if block["confidence"] > 0:
                all_conf.append(block["confidence"])

    avg_conf = sum(all_conf) / len(all_conf) if all_conf else 0.0
    return pages, page_count, avg_conf


def _run_paddle_on_image_bytes(
    file_bytes: bytes,
    language: str = "auto",
) -> tuple[list[dict], float]:
    """Decode image bytes and run PaddleOCR.

    Returns (pages_list, avg_confidence).
    """
    from PIL import Image
    from app.services.paddle_ocr_engine import run_paddle_ocr_on_image

    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    page_dict = run_paddle_ocr_on_image(img, page_num=1, lang=language)

    all_conf = [b["confidence"] for b in page_dict["blocks"] if b["confidence"] > 0]
    avg_conf = sum(all_conf) / len(all_conf) if all_conf else 0.0
    return [page_dict], avg_conf


# ---------------------------------------------------------------------------
# Public API — primary entry point
# ---------------------------------------------------------------------------

def run_ocr(file_bytes: bytes, content_type: str, language: str = "auto") -> OCRResult:
    """Run OCR on a document, returning a backward-compatible OCRResult.

    Engine selection:
      - PaddleOCR is tried first for all supported types with script routing.
      - pypdf text extraction is the PDF fallback.
      - Tesseract is the image fallback (uses requested language).

    The result includes a ``pages`` field with the normalized block-level
    structure for downstream spatial processing (LayoutLMv3 etc.).

    Never raises — all errors are captured in OCRResult.error.
    """
    result = OCRResult()
    paddle_succeeded = False

    # -----------------------------------------------------------------------
    # 1. Try PaddleOCR (primary for all types)
    # -----------------------------------------------------------------------
    if content_type == "application/pdf":
        result.page_count = 0  # Will be set by the chosen method
        try:
            pages, page_count, avg_conf = _run_paddle_on_pdf(file_bytes, language=language)
            result.pages = pages
            result.page_count = page_count
            result.confidence = round(avg_conf, 4)
            result.text = "\n\n".join(
                "\n".join(b["text"] for b in p["blocks"]) for p in pages
            )
            result.method = f"paddle({language})+pypdfium2"
            paddle_succeeded = True
            logger.info(
                "PaddleOCR PDF (%s): %d pages, %d chars, conf=%.2f",
                language, page_count, len(result.text), avg_conf,
            )
        except Exception as exc:
            logger.warning(
                "PaddleOCR PDF failed (will try pypdf fallback): %s", exc
            )
            result.warnings.append(f"PaddleOCR PDF failed: {exc}")

        # -------------------------------------------------------------------
        # 1b. pypdf text fallback (for text-layer PDFs when PaddleOCR fails
        #     or extracted nothing)
        # -------------------------------------------------------------------
        if not paddle_succeeded or not result.text.strip():
            try:
                text, page_count, pages = _extract_text_pdf_pypdf(file_bytes)
                if text.strip():
                    if not result.text.strip():
                        result.text = text
                        result.page_count = page_count
                        result.pages = pages
                        result.confidence = 1.0
                        result.method = "pypdf_text"
                        logger.info(
                            "pypdf fallback: %d pages, %d chars", page_count, len(text)
                        )
                    else:
                        result.text = text
                        result.method += "+pypdf_text_merge"
                        logger.info("Merged pypdf text with empty PaddleOCR result")
            except Exception as exc:
                msg = f"pypdf fallback failed: {exc}"
                result.warnings.append(msg)
                logger.warning(msg)

        if not result.text.strip() and not result.error:
            result.error = "No text extracted from PDF (all engines failed or doc is blank)"

    elif content_type in {"image/jpeg", "image/png", "image/tiff"}:
        result.page_count = 1

        # Try PaddleOCR on image for all supported languages
        try:
            pages, avg_conf = _run_paddle_on_image_bytes(file_bytes, language=language)
            if pages and pages[0].get("blocks"):
                result.pages = pages
                result.confidence = round(avg_conf, 4)
                result.text = "\n".join(b["text"] for b in pages[0]["blocks"])
                result.method = f"paddle({language})"
                paddle_succeeded = True
                logger.info(
                    "PaddleOCR image (%s): %d chars, conf=%.2f", language, len(result.text), avg_conf
                )
        except Exception as exc:
            logger.warning(
                "PaddleOCR image failed (will try Tesseract fallback): %s", exc
            )
            result.warnings.append(f"PaddleOCR image failed: {exc}")

        # Tesseract fallback if PaddleOCR didn't yield text
        if not paddle_succeeded or not result.text.strip():
            try:
                text, conf = _extract_text_image_tesseract(file_bytes, language=language)
                if text.strip():
                    result.text = text
                    result.confidence = round(conf, 4)
                    result.method = f"tesseract({language})"
                    ts = datetime.utcnow().isoformat()
                    result.pages = [{
                        "page": 1,
                        "width": 0,
                        "height": 0,
                        "blocks": [{
                            "text": text,
                            "bbox": [0.0, 0.0, 0.0, 0.0],
                            "confidence": conf,
                            "language": language,
                            "ocr_engine": "tesseract",
                            "timestamp": ts,
                        }],
                    }]
                    logger.info(
                        "Tesseract OCR (%s): %d chars, conf=%.2f", language, len(text), conf
                    )
            except RuntimeError as exc:
                result.warnings.append(str(exc))
                logger.warning("Tesseract OCR skipped: %s", exc)
            except Exception as exc:
                result.error = f"Image OCR failed: {exc}"
                logger.error("Image OCR error: %s", exc, exc_info=True)

    else:
        result.error = f"Unsupported content type for OCR: {content_type}"
        result.warnings.append(result.error)
        logger.warning("Unsupported content type: %s", content_type)

    return result


def run_ocr_structured(
    file_bytes: bytes, content_type: str, language: str = "auto"
) -> dict:
    """Run OCR and return the normalized OcrDocument dict."""
    result = run_ocr(file_bytes, content_type, language=language)
    return {
        "page_count": result.page_count,
        "full_text": result.text,
        "avg_confidence": result.confidence,
        "method": result.method,
        "error": result.error,
        "warnings": result.warnings,
        "pages": result.pages,
    }


# ---------------------------------------------------------------------------
# Recommended entry point — Script Detection → OCR Router → OCR Engine
# ---------------------------------------------------------------------------

def run_ocr_with_script_detection(
    file_bytes: bytes,
    content_type: str,
    max_sample_pages: int = 2,
) -> dict:
    """Auto-detect script/language FIRST, then run the matching OCR engine.

    This is the **recommended** public entry point for new pipeline code.
    It implements the full recommended pipeline::

        Upload Document
              ↓
        Document Preprocessing
              ↓
        Script / Language Detection  (lightweight — no full OCR model loaded)
              ↓
        OCR Router
         ┌──────┬──────┬──────┬──────┐
        Hindi  Tamil Telugu Kannada English …
         └──────┴──────┴──────┴──────┘
              ↓
        Text Extraction
              ↓
        Land-Field Extraction → Validation → Structured Record

    Args:
        file_bytes:        Raw bytes of the uploaded document.
        content_type:      MIME type (``"application/pdf"``, ``"image/jpeg"`` etc.)
        max_sample_pages:  Pages to sample for script detection (default 2).

    Returns:
        dict with keys:

        ``script_detection``  — Full :class:`~script_detector.ScriptDetectionResult`
                                as a dict.  Example::

                                    {
                                      "detected_language": "Tamil",
                                      "language_code": "ta",
                                      "script": "Tamil",
                                      "confidence": 0.97,
                                      "ocr_engine": "paddle_ta",
                                      "next_step": "tamil_ocr",
                                      "detection_method": "tesseract_osd",
                                      "sample_pages": [1, 2],
                                      "elapsed_ms": 187.4,
                                      "warnings": []
                                    }

        ``page_count``        — Total pages processed.
        ``full_text``         — Concatenated OCR text.
        ``avg_confidence``    — Average OCR confidence (0.0–1.0).
        ``method``            — OCR engine + language label.
        ``error``             — Error string or None.
        ``warnings``          — List of warning strings.
        ``pages``             — Per-page block list (for LayoutLMv3 etc.).

    Never raises — all errors are captured and returned in the result dict.
    """
    from app.services.script_detector import detect_script_from_document

    # ── Step 1: Lightweight script detection (no OCR model loaded yet) ────
    detection = detect_script_from_document(
        file_bytes,
        content_type,
        max_sample_pages=max_sample_pages,
    )

    logger.info(
        "OCR Router: detected script=%s lang=%s conf=%.2f method=%s → routing to %s",
        detection.script_name,
        detection.language_code,
        detection.confidence,
        detection.detection_method,
        detection.next_step,
    )

    # ── Step 2: Route to the correct OCR engine ───────────────────────────
    ocr_result = run_ocr(
        file_bytes,
        content_type,
        language=detection.language_code,
    )

    return {
        "script_detection": detection.to_dict(),
        "page_count": ocr_result.page_count,
        "full_text": ocr_result.text,
        "avg_confidence": ocr_result.confidence,
        "method": ocr_result.method,
        "error": ocr_result.error,
        "warnings": ocr_result.warnings + detection.warnings,
        "pages": ocr_result.pages,
    }
