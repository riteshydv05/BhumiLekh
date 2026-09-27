"""Script / Language Detection Stage.

This module implements the **lightweight pre-OCR script detector** that
runs *before* any heavy OCR model is loaded.

Pipeline position
-----------------

    Upload Document
          ↓
    Document Preprocessing  (pdf_renderer / image decode)
          ↓
    ► Script Detection  ◄ (THIS MODULE)
          ↓
    OCR Router  →  Hindi OCR | Tamil OCR | Telugu OCR | English OCR | …
          ↓
    Text Extraction
          ↓
    Land-Field Extraction
          ↓
    Validation / Verification
          ↓
    Structured Record → PostgreSQL / PostGIS

Detection Strategy
------------------
For **scanned PDFs and images** (no embedded text layer) we CANNOT rely on
a text-based language detector such as ``langdetect`` because there is no
text to analyse yet.

Instead, we use a three-step cascade (fastest → most accurate):

1. **Embedded text probe** (PDF only) — if ``pypdf`` can extract ≥ 20 chars
   from the first page, we run Unicode block counting on that sample.
   Cost: ~0 ms.

2. **Tesseract OSD** (orientation & script detection) — runs
   ``tesseract --psm 0`` on a small, centre-cropped, grayscale thumbnail
   (~600 px wide) sampled from the first few pages.  Does NOT recognise text;
   only detects the dominant writing system.
   Cost: 50–300 ms per page, 1 page is usually enough.

3. **Fast OCR probe** (ultimate fallback) — runs Tesseract in full OCR mode
   on a tiny thumbnail (400 px) with ``--psm 6 -l script/Devanagari+…`` and
   uses Unicode block counting on the resulting characters.
   Cost: 200–600 ms, run only when OSD fails.

The result is a ``ScriptDetectionResult`` dataclass containing:

    - ``language_code``  : ISO 639-1 code  (e.g. ``"ta"``, ``"hi"``)
    - ``language_name``  : Human-readable  (e.g. ``"Tamil"``)
    - ``script_name``    : Unicode block   (e.g. ``"Tamil"``, ``"Devanagari"``)
    - ``confidence``     : float 0.0–1.0
    - ``ocr_engine_hint``: engine key for the OCR router
    - ``next_step``      : string label for pipeline routing
    - ``detection_method``: which of the 3 steps succeeded
    - ``sample_pages``   : which page indices were sampled

All errors are caught; the service always returns a usable result (falls back
to ``"hi"``/Devanagari for Indian land-record PDFs when uncertain).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Script → Language mapping  (Unicode block name → ISO 639-1 primary code)
# ---------------------------------------------------------------------------

# Unicode block ranges for Indic & common scripts
_SCRIPT_RANGES: list[tuple[int, int, str, str, str]] = [
    # (start, end, script_name, lang_code, ocr_engine_hint)
    (0x0900, 0x097F, "Devanagari", "hi",  "paddle_hi"),
    (0x0980, 0x09FF, "Bengali",    "bn",  "paddle_bn"),
    (0x0A00, 0x0A7F, "Gurmukhi",   "pa",  "paddle_pa"),
    (0x0A80, 0x0AFF, "Gujarati",   "gu",  "paddle_gu"),
    (0x0B00, 0x0B7F, "Odia",       "or",  "tesseract_or"),
    (0x0B80, 0x0BFF, "Tamil",      "ta",  "paddle_ta"),
    (0x0C00, 0x0C7F, "Telugu",     "te",  "paddle_te"),
    (0x0C80, 0x0CFF, "Kannada",    "kn",  "paddle_kn"),
    (0x0D00, 0x0D7F, "Malayalam",  "ml",  "paddle_ml"),
    (0x0600, 0x06FF, "Arabic",     "ur",  "tesseract_urd"),
]

_LATIN_RANGE = (0x0041, 0x007A)   # A-z (basic Latin letters)

_LANG_NAMES: dict[str, str] = {
    "hi": "Hindi",
    "mr": "Marathi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "or": "Odia",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "ur": "Urdu",
    "en": "English",
    "sa": "Sanskrit",
    "as": "Assamese",
}

# Devanagari is shared by Hindi + Marathi.  Domain keywords help disambiguate.
_MARATHI_KEYWORDS = {
    "गाव", "तालुका", "जिल्हा", "नमुना", "भोगवटदार", "खातेदार",
    "महाराष्ट्र", "सर्व्हे", "फेरफार",
}

# Tesseract OSD script label → (lang_code, script_name, engine_hint)
_OSD_SCRIPT_MAP: dict[str, tuple[str, str, str]] = {
    "Devanagari":  ("hi",  "Devanagari",  "paddle_hi"),
    "Tamil":       ("ta",  "Tamil",        "paddle_ta"),
    "Telugu":      ("te",  "Telugu",       "paddle_te"),
    "Kannada":     ("kn",  "Kannada",      "paddle_kn"),
    "Malayalam":   ("ml",  "Malayalam",    "paddle_ml"),
    "Bengali":     ("bn",  "Bengali",      "paddle_bn"),
    "Gujarati":    ("gu",  "Gujarati",     "paddle_gu"),
    "Gurmukhi":    ("pa",  "Gurmukhi",     "paddle_pa"),
    "Latin":       ("en",  "Latin",        "paddle_en"),
    "Arabic":      ("ur",  "Arabic",       "tesseract_urd"),
    "Oriya":       ("or",  "Odia",         "tesseract_or"),
}

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScriptDetectionResult:
    """Structured result returned by :func:`detect_script_from_document`."""

    language_code: str = "hi"
    language_name: str = "Hindi"
    script_name: str = "Devanagari"
    confidence: float = 0.0

    # Routing hints for downstream consumers
    ocr_engine_hint: str = "paddle_hi"
    next_step: str = "hindi_ocr"

    # Diagnostics
    detection_method: str = "fallback"
    sample_pages: list[int] = field(default_factory=list)
    elapsed_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "detected_language": self.language_name,
            "language_code": self.language_code,
            "script": self.script_name,
            "confidence": round(self.confidence, 4),
            "ocr_engine": self.ocr_engine_hint,
            "next_step": self.next_step,
            "detection_method": self.detection_method,
            "sample_pages": self.sample_pages,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Helpers — Unicode block counting
# ---------------------------------------------------------------------------

def _count_scripts(text: str) -> dict[str, int]:
    """Count characters per Unicode script block."""
    counts: dict[str, int] = {name: 0 for _, _, name, _, _ in _SCRIPT_RANGES}
    counts["Latin"] = 0
    counts["Digit"] = 0

    for ch in text:
        cp = ord(ch)
        matched = False
        for start, end, name, _, _ in _SCRIPT_RANGES:
            if start <= cp <= end:
                counts[name] += 1
                matched = True
                break
        if not matched:
            if _LATIN_RANGE[0] <= cp <= _LATIN_RANGE[1]:
                counts["Latin"] += 1
            elif ch.isdigit():
                counts["Digit"] += 1

    return counts


def _dominant_lang_from_text(
    text: str,
) -> tuple[str, str, str, float]:
    """Analyse a Unicode text sample and return (lang_code, lang_name, script, confidence).

    Uses Devanagari domain keywords to distinguish Hindi from Marathi.
    """
    counts = _count_scripts(text)

    # Remove non-script counts
    script_counts = {
        k: v for k, v in counts.items()
        if k not in ("Digit",)
    }

    total = sum(script_counts.values())
    if total == 0:
        return "en", "English", "Latin", 0.1

    dominant_script = max(script_counts, key=script_counts.get)
    dominant_count = script_counts[dominant_script]
    confidence = dominant_count / total

    if dominant_script == "Latin":
        return "en", "English", "Latin", confidence

    # Find matching lang code + engine hint
    for start, end, sname, lang_code, engine in _SCRIPT_RANGES:
        if sname == dominant_script:
            lang_name = _LANG_NAMES.get(lang_code, lang_code)

            # Devanagari disambiguation: Marathi vs Hindi
            if dominant_script == "Devanagari":
                if any(kw in text for kw in _MARATHI_KEYWORDS):
                    return "mr", "Marathi", "Devanagari", confidence

            return lang_code, lang_name, dominant_script, confidence

    return "hi", "Hindi", "Devanagari", confidence


def _build_result(
    lang_code: str,
    lang_name: str,
    script: str,
    confidence: float,
    method: str,
    sample_pages: list[int],
    t0: float,
    warnings: list[str] | None = None,
) -> ScriptDetectionResult:
    """Construct a :class:`ScriptDetectionResult` from detection outputs."""
    # Determine next_step label
    step_map = {
        "ta": "tamil_ocr",
        "te": "telugu_ocr",
        "kn": "kannada_ocr",
        "ml": "malayalam_ocr",
        "bn": "bengali_ocr",
        "gu": "gujarati_ocr",
        "pa": "punjabi_ocr",
        "or": "odia_ocr",
        "ur": "urdu_ocr",
        "hi": "hindi_ocr",
        "mr": "marathi_ocr",
        "en": "english_ocr",
        "sa": "hindi_ocr",   # Sanskrit via Devanagari pipeline
    }

    # Determine engine hint
    engine_map = {
        "ta": "paddle_ta",
        "te": "paddle_te",
        "kn": "paddle_kn",
        "ml": "paddle_ml",
        "bn": "paddle_bn",
        "gu": "paddle_gu",
        "pa": "paddle_pa",
        "or": "tesseract_or",
        "ur": "tesseract_urd",
        "hi": "paddle_hi",
        "mr": "paddle_hi",   # Marathi uses Devanagari PaddleOCR model
        "en": "paddle_en",
        "sa": "paddle_hi",
    }

    return ScriptDetectionResult(
        language_code=lang_code,
        language_name=lang_name,
        script_name=script,
        confidence=confidence,
        ocr_engine_hint=engine_map.get(lang_code, "paddle_hi"),
        next_step=step_map.get(lang_code, "hindi_ocr"),
        detection_method=method,
        sample_pages=sample_pages,
        elapsed_ms=(time.monotonic() - t0) * 1000,
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# Stage 1 — Embedded text probe (text-layer PDFs only)
# ---------------------------------------------------------------------------

def _detect_from_embedded_text(
    pdf_bytes: bytes,
    t0: float,
) -> Optional[ScriptDetectionResult]:
    """Try to extract embedded text from the PDF and detect script."""
    try:
        import pypdf  # local import; soft dependency
        reader = pypdf.PdfReader(BytesIO(pdf_bytes))
        sample = ""
        pages_checked = []
        for i, page in enumerate(reader.pages[:3]):
            try:
                t = (page.extract_text() or "").strip()
            except Exception:
                t = ""
            if t:
                sample += t + "\n"
                pages_checked.append(i + 1)
            if len(sample) >= 80:
                break

        if len(sample.strip()) >= 20:
            lang_code, lang_name, script, conf = _dominant_lang_from_text(sample)
            if conf >= 0.35:
                logger.info(
                    "ScriptDetector [Stage-1/embedded-text]: %s (%s) conf=%.2f",
                    lang_name, lang_code, conf,
                )
                return _build_result(
                    lang_code, lang_name, script, conf,
                    "embedded_text_probe", pages_checked, t0,
                )
    except Exception as exc:
        logger.debug("ScriptDetector [Stage-1]: embedded text probe skipped — %s", exc)
    return None


# ---------------------------------------------------------------------------
# Stage 2 — Tesseract OSD (orientation & script detection, no text output)
# ---------------------------------------------------------------------------

def _render_thumbnail(
    image_source,  # PIL Image or pdf_bytes
    is_pdf: bool,
    page_index: int = 0,
    thumb_width: int = 600,
) -> Optional["PILImage.Image"]:  # noqa: F821
    """Render a greyscale thumbnail for OSD/OCR probe."""
    try:
        from PIL import Image as PILImage

        if is_pdf:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(image_source)
            if page_index >= len(doc):
                return None
            page = doc[page_index]
            scale = 150 / 72.0
            bitmap = page.render(scale=scale, rotation=0)
            img = bitmap.to_pil().convert("L")
            page.close()
            doc.close()
        else:
            img = PILImage.open(BytesIO(image_source)).convert("L")

        # Resize maintaining aspect ratio
        w, h = img.size
        if w > thumb_width:
            ratio = thumb_width / w
            img = img.resize((thumb_width, int(h * ratio)), PILImage.LANCZOS)

        # Crop centre strip (avoid blank margins)
        cw, ch = img.size
        top = int(ch * 0.15)
        bot = int(ch * 0.85)
        img = img.crop((0, top, cw, bot))

        return img
    except Exception as exc:
        logger.debug("ScriptDetector: thumbnail render failed — %s", exc)
        return None


def _detect_via_tesseract_osd(
    image_source: bytes,
    is_pdf: bool,
    t0: float,
    max_pages: int = 2,
) -> Optional[ScriptDetectionResult]:
    """Run Tesseract OSD (--psm 0) on sample pages to detect script."""
    try:
        import pytesseract
    except ImportError:
        logger.debug("ScriptDetector [Stage-2]: pytesseract not installed, skipping OSD")
        return None

    votes: dict[str, int] = {}
    pages_checked = []

    for page_idx in range(max_pages):
        thumb = _render_thumbnail(image_source, is_pdf, page_index=page_idx)
        if thumb is None:
            continue

        try:
            osd_output = pytesseract.image_to_osd(
                thumb,
                output_type=pytesseract.Output.DICT,
                config="--psm 0",
            )
            script_label = osd_output.get("script", "")
            script_conf = float(osd_output.get("script_confidence", 0.0))

            if script_label and script_conf > 0.5:
                votes[script_label] = votes.get(script_label, 0) + 1
                pages_checked.append(page_idx + 1)
                logger.info(
                    "ScriptDetector [Stage-2/OSD]: page=%d script=%s conf=%.2f",
                    page_idx + 1, script_label, script_conf,
                )
        except Exception as exc:
            logger.debug("ScriptDetector [Stage-2]: OSD page %d failed — %s", page_idx + 1, exc)

    if not votes:
        return None

    dominant = max(votes, key=votes.get)
    confidence = votes[dominant] / max(sum(votes.values()), 1)

    # Map Tesseract OSD script label → language
    mapping = _OSD_SCRIPT_MAP.get(dominant)
    if not mapping:
        logger.debug("ScriptDetector [Stage-2]: unknown OSD script '%s'", dominant)
        return None

    lang_code, script_name, _ = mapping
    lang_name = _LANG_NAMES.get(lang_code, lang_code)
    # Boost confidence since OSD is quite reliable
    confidence = min(confidence * 0.85 + 0.15, 0.97)

    logger.info(
        "ScriptDetector [Stage-2/OSD]: result=%s (%s) agg_conf=%.2f",
        lang_name, lang_code, confidence,
    )
    return _build_result(
        lang_code, lang_name, script_name, confidence,
        "tesseract_osd", pages_checked, t0,
    )


# ---------------------------------------------------------------------------
# Stage 3 — Fast OCR probe with Unicode counting (ultimate fallback)
# ---------------------------------------------------------------------------

def _detect_via_fast_ocr_probe(
    image_source: bytes,
    is_pdf: bool,
    t0: float,
) -> ScriptDetectionResult:
    """Run a tiny Tesseract OCR pass and count Unicode blocks (ultimate fallback)."""
    thumb = _render_thumbnail(image_source, is_pdf, page_index=0, thumb_width=400)
    warnings: list[str] = []

    if thumb is not None:
        try:
            import pytesseract

            # Try a broad multilingual OCR pass to capture any Indic chars
            lang_str = "hin+tam+tel+kan+mal+guj+ben+pan+eng"
            try:
                raw = pytesseract.image_to_string(thumb, lang=lang_str, config="--psm 6")
            except Exception:
                # Fallback to English only if specific langs not installed
                raw = pytesseract.image_to_string(thumb, config="--psm 6")
                warnings.append("Tesseract multilingual lang pack unavailable; English-only probe used")

            if raw.strip():
                lang_code, lang_name, script, conf = _dominant_lang_from_text(raw)
                logger.info(
                    "ScriptDetector [Stage-3/fast-probe]: %s (%s) conf=%.2f",
                    lang_name, lang_code, conf,
                )
                return _build_result(
                    lang_code, lang_name, script, max(conf, 0.40),
                    "fast_ocr_probe", [1], t0, warnings,
                )
        except Exception as exc:
            warnings.append(f"Fast OCR probe failed: {exc}")
            logger.debug("ScriptDetector [Stage-3]: fast probe failed — %s", exc)

    warnings.append("All detection stages failed; defaulting to Hindi (Devanagari)")
    logger.warning("ScriptDetector: all 3 stages failed — returning default Hindi result")
    return _build_result(
        "hi", "Hindi", "Devanagari", 0.30,
        "fallback_default", [], t0, warnings,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_script_from_document(
    file_bytes: bytes,
    content_type: str,
    max_sample_pages: int = 2,
) -> ScriptDetectionResult:
    """Detect the dominant script/language from a document *before* running OCR.

    This is the main public entry point.  It runs the three-stage cascade and
    returns a :class:`ScriptDetectionResult` that the OCR router uses to
    select the correct engine.

    Args:
        file_bytes:       Raw bytes of the uploaded document (PDF or image).
        content_type:     MIME type — ``"application/pdf"``, ``"image/jpeg"`` etc.
        max_sample_pages: Maximum PDF pages to sample (default 2; first 2 pages
                          are usually enough for Indian land records).

    Returns:
        :class:`ScriptDetectionResult` — always returns a usable result, never raises.

    Example response dict (via ``.to_dict()``)::

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
    """
    t0 = time.monotonic()
    is_pdf = content_type == "application/pdf"

    logger.info(
        "ScriptDetector: starting detection — content_type=%s, size=%d bytes",
        content_type, len(file_bytes),
    )

    # ── Stage 1: Embedded text (PDF with text layer only) ──────────────────
    if is_pdf:
        result = _detect_from_embedded_text(file_bytes, t0)
        if result and result.confidence >= 0.50:
            return result

    # ── Stage 2: Tesseract OSD (image-based script detection) ──────────────
    result = _detect_via_tesseract_osd(
        file_bytes, is_pdf, t0, max_pages=max_sample_pages
    )
    if result and result.confidence >= 0.55:
        return result

    # ── Stage 3: Fast OCR probe + Unicode counting ──────────────────────────
    return _detect_via_fast_ocr_probe(file_bytes, is_pdf, t0)


def detect_script_from_image(pil_image) -> ScriptDetectionResult:
    """Detect script from an already-rendered PIL Image (in-pipeline use).

    Useful when the PDF pages have already been rendered by ``pdf_renderer``
    and we want to run per-page script detection without re-loading the PDF.

    Uses Stage-2 (OSD) only, falling back to Stage-3 Unicode probe.
    """
    from io import BytesIO as _BIO

    t0 = time.monotonic()
    buf = _BIO()
    pil_image.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    result = _detect_via_tesseract_osd(img_bytes, is_pdf=False, t0=t0, max_pages=1)
    if result and result.confidence >= 0.55:
        return result
    return _detect_via_fast_ocr_probe(img_bytes, is_pdf=False, t0=t0)
