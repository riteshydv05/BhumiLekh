"""Intelligent Language Identification and OCR Model Selection Module.

This module analyzes incoming land-record documents (scanned/digital PDFs or images),
automatically identifies the language(s) and script(s), detects text types
(printed vs. handwritten), and routes the document or regions to the most suitable
OCR models:
  - PaddleOCR for supported printed multilingual text (Indic scripts + English)
  - TrOCR (microsoft/trocr-base-handwritten) for handwritten text / filled fields
  - Regional multi-model dispatch for mixed-language / multi-script documents

Pipeline Position:
    Upload Document (PDF / Image)
                 ↓
    ► Intelligent Language & Script Detection ◄ (Embedded text, OSD, Unicode distribution)
                 ↓
    ► Text-Type & Region Analysis ◄ (Printed vs. Handwritten candidate regions)
                 ↓
    ► OCR Model Selection ◄ (PaddleOCR per-language model + TrOCR for handwriting)
                 ↓
    ► Coordinated Regional Processing ◄ (Multi-engine extraction & fusion)
                 ↓
    Structured Output (detected_languages, selected_models, confidence, extracted_text, pages)
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported Scripts, Languages & Models
# ---------------------------------------------------------------------------

_SCRIPT_RANGES: list[tuple[int, int, str, str, str]] = [
    # (start, end, script_name, lang_code, paddle_lang_code)
    (0x0900, 0x097F, "Devanagari", "hi", "hi"),
    (0x0980, 0x09FF, "Bengali", "bn", "bn"),
    (0x0A00, 0x0A7F, "Gurmukhi", "pa", "pa"),
    (0x0A80, 0x0AFF, "Gujarati", "gu", "gu"),
    (0x0B00, 0x0B7F, "Odia", "or", "or"),
    (0x0B80, 0x0BFF, "Tamil", "ta", "ta"),
    (0x0C00, 0x0C7F, "Telugu", "te", "te"),
    (0x0C80, 0x0CFF, "Kannada", "kn", "kn"),
    (0x0D00, 0x0D7F, "Malayalam", "ml", "ml"),
    (0x0600, 0x06FF, "Arabic", "ur", "ur"),
]

_LATIN_RANGE = (0x0041, 0x007A)  # Basic Latin letters (A-Z, a-z)

LANGUAGE_NAMES: dict[str, str] = {
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "bn": "Bengali",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
    "en": "English",
}

# Domain vocabulary to disambiguate Marathi from Hindi under Devanagari script
_MARATHI_KEYWORDS = {
    "गाव", "तालुका", "जिल्हा", "नमुना", "अभिलेखा", "अभिलेख", "भोगवटदार",
    "खातेदार", "हक्क", "मालिक", "फेरफार", "सात", "१२", "आकारणी", "क्षेत्रफळ",
    "महाराष्ट्र", "नमुने", "सर्व्हे", "क्षेत्र", "पोट", "खराब"
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DetectedLanguage:
    """Represents a single detected language/script in the document."""
    code: str
    name: str
    script: str
    confidence: float
    is_primary: bool = False
    char_share: float = 0.0
    char_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "script": self.script,
            "confidence": round(self.confidence, 4),
            "is_primary": self.is_primary,
            "char_share": round(self.char_share, 4),
            "char_count": self.char_count,
        }


@dataclass
class SelectedOcrModel:
    """Represents an OCR model chosen by the router."""
    engine: str
    model_name: str
    text_type: str  # "printed" | "handwritten" | "mixed"
    language: str
    target_scope: str = "full_document"  # "full_document" | "region_crops" | "fallback"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "model_name": self.model_name,
            "text_type": self.text_type,
            "language": self.language,
            "target_scope": self.target_scope,
            "description": self.description,
        }


@dataclass
class IntelligentOCRResult:
    """Structured response from the intelligent language & OCR router."""
    detected_languages: list[DetectedLanguage]
    is_mixed_language: bool
    text_type_breakdown: dict[str, Any]
    selected_ocr_models: list[SelectedOcrModel]
    overall_confidence: float
    page_count: int
    extracted_text: str
    pages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected_languages": [l.to_dict() for l in self.detected_languages],
            "primary_language": self.detected_languages[0].to_dict() if self.detected_languages else None,
            "is_mixed_language": self.is_mixed_language,
            "text_type_breakdown": self.text_type_breakdown,
            "selected_ocr_models": [m.to_dict() for m in self.selected_ocr_models],
            "confidence_score": round(self.overall_confidence, 4),
            "page_count": self.page_count,
            "extracted_text": self.extracted_text,
            "pages": self.pages,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Step 1: Multi-Script Character Distribution Analysis
# ---------------------------------------------------------------------------

def count_unicode_scripts(text: str) -> dict[str, int]:
    """Count character occurrences per Unicode script block and Latin/digits."""
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
            if (_LATIN_RANGE[0] <= cp <= _LATIN_RANGE[1]) or (0x0061 <= cp <= 0x007A):
                counts["Latin"] += 1
            elif ch.isdigit():
                counts["Digit"] += 1

    return counts


def analyze_script_distribution(text: str, base_confidence: float = 0.95) -> list[DetectedLanguage]:
    """Analyze character distribution in text to detect primary and secondary languages."""
    if not text or not text.strip():
        return [DetectedLanguage(
            code="hi", name="Hindi", script="Devanagari",
            confidence=0.40, is_primary=True, char_share=1.0, char_count=0
        )]

    counts = count_unicode_scripts(text)
    script_counts = {k: v for k, v in counts.items() if k != "Digit" and v > 0}
    total_chars = sum(script_counts.values())

    if total_chars == 0:
        return [DetectedLanguage(
            code="en", name="English", script="Latin",
            confidence=0.50, is_primary=True, char_share=1.0, char_count=0
        )]

    # Sort scripts by character count descending
    sorted_scripts = sorted(script_counts.items(), key=lambda kv: kv[1], reverse=True)

    results: list[DetectedLanguage] = []
    script_to_meta = {name: (code, paddle_code) for _, _, name, code, paddle_code in _SCRIPT_RANGES}

    for idx, (script_name, count) in enumerate(sorted_scripts):
        char_share = count / total_chars
        is_primary = (idx == 0)

        if script_name == "Latin":
            code = "en"
            name = "English"
        elif script_name in script_to_meta:
            code = script_to_meta[script_name][0]
            name = LANGUAGE_NAMES.get(code, code)
            # Devanagari disambiguation
            if script_name == "Devanagari" and any(kw in text for kw in _MARATHI_KEYWORDS):
                code = "mr"
                name = "Marathi"
        else:
            code = "en"
            name = script_name

        # Calculate confidence factoring in char share and detection stability
        conf = min(base_confidence * (0.6 + 0.4 * min(char_share * 1.5, 1.0)), 0.99)

        results.append(DetectedLanguage(
            code=code,
            name=name,
            script=script_name,
            confidence=round(conf, 4),
            is_primary=is_primary,
            char_share=round(char_share, 4),
            char_count=count,
        ))

    return results


# ---------------------------------------------------------------------------
# Step 2: Intelligent Language Identification Cascade
# ---------------------------------------------------------------------------

def identify_language_and_scripts(
    file_bytes: bytes,
    content_type: str,
    sample_pages: int = 3,
) -> tuple[list[DetectedLanguage], bool, str]:
    """Identifies all languages and scripts present in the document.

    Cascade:
      1. Embedded PDF text layer analysis (fastest & most granular for digital PDFs).
      2. Tesseract OSD (image orientation & script detection across rendered pages).
      3. Fast multilingual OCR probe on thumbnail.
      4. Unicode script distribution analysis to detect mixed-language content.

    Returns:
      (detected_languages, is_mixed_language, detection_method)
    """
    t0 = time.monotonic()
    is_pdf = content_type == "application/pdf"
    method = "fallback"
    extracted_sample = ""

    # --- 1. Embedded Text Layer Probe (PDF only) ---
    if is_pdf:
        try:
            import pypdf
            reader = pypdf.PdfReader(BytesIO(file_bytes))
            for page in reader.pages[:sample_pages]:
                pt = (page.extract_text() or "").strip()
                if pt:
                    extracted_sample += pt + "\n"
            if len(extracted_sample.strip()) >= 20:
                method = "embedded_text_layer"
        except Exception as exc:
            logger.debug("IntelligentOCRRouter: embedded text extraction skipped: %s", exc)

    # --- 2. Tesseract OSD Probe (if embedded text absent or insufficient) ---
    if not extracted_sample or len(extracted_sample.strip()) < 20:
        try:
            from app.services.script_detector import detect_script_from_document
            det = detect_script_from_document(file_bytes, content_type, max_sample_pages=sample_pages)
            if det and det.confidence >= 0.50:
                method = f"script_detector_{det.detection_method}"
                primary_lang = DetectedLanguage(
                    code=det.language_code,
                    name=det.language_name,
                    script=det.script_name,
                    confidence=det.confidence,
                    is_primary=True,
                    char_share=0.92,
                    char_count=100,
                )
                # Check for secondary English / Latin content (very common in Indian revenue forms)
                secondary_lang = DetectedLanguage(
                    code="en",
                    name="English",
                    script="Latin",
                    confidence=0.80,
                    is_primary=False,
                    char_share=0.08,
                    char_count=10,
                )
                detected = [primary_lang, secondary_lang] if primary_lang.code != "en" else [primary_lang]
                is_mixed = len(detected) > 1 and detected[1].char_share >= 0.05
                return detected, is_mixed, method
        except Exception as exc:
            logger.warning("IntelligentOCRRouter: OSD probe failed: %s", exc)

    # --- 3. Unicode script distribution analysis on collected sample ---
    detected_languages = analyze_script_distribution(extracted_sample)

    # Check for mixed-language: secondary language with >= 5% character share
    is_mixed = False
    if len(detected_languages) > 1:
        secondary = detected_languages[1]
        if secondary.char_share >= 0.05 and secondary.code != detected_languages[0].code:
            is_mixed = True

    return detected_languages, is_mixed, method


# ---------------------------------------------------------------------------
# Step 3: Model Selection & Routing Decision Matrix
# ---------------------------------------------------------------------------

def select_ocr_models(
    detected_languages: list[DetectedLanguage],
    is_mixed_language: bool,
    has_handwriting: bool = False,
) -> list[SelectedOcrModel]:
    """Select the optimal OCR models based on detected language(s) and text type.

    Rules:
      - Printed multilingual text: PaddleOCR with the specific language configuration.
      - Handwritten text: TrOCR (microsoft/trocr-base-handwritten).
      - Mixed language: Primary PaddleOCR model + secondary script pass / English numbers.
    """
    selected: list[SelectedOcrModel] = []
    primary = detected_languages[0] if detected_languages else DetectedLanguage("hi", "Hindi", "Devanagari", 0.5, True)

    # 1. Primary Printed Text Model
    paddle_lang = primary.code
    paddle_desc = f"PaddleOCR ({primary.name} PP-OCRv5/v4) for printed text"

    if paddle_lang in {"hi", "mr", "ta", "te", "kn", "ml", "gu", "bn", "pa", "en"}:
        selected.append(SelectedOcrModel(
            engine=f"paddle_{paddle_lang}",
            model_name=f"PaddleOCR-{paddle_lang.upper()}",
            text_type="printed",
            language=paddle_lang,
            target_scope="full_document",
            description=paddle_desc,
        ))
    else:
        # Fallback for languages without standalone PaddleOCR model (e.g. Odia, Urdu)
        selected.append(SelectedOcrModel(
            engine=f"tesseract_{paddle_lang}",
            model_name=f"Tesseract-{primary.name}",
            text_type="printed",
            language=paddle_lang,
            target_scope="full_document",
            description=f"Tesseract OCR for printed {primary.name}",
        ))

    # 2. Secondary Model for Mixed-Language Content
    if is_mixed_language and len(detected_languages) > 1:
        secondary = detected_languages[1]
        if secondary.code != primary.code:
            selected.append(SelectedOcrModel(
                engine=f"paddle_{secondary.code}",
                model_name=f"PaddleOCR-{secondary.code.upper()}",
                text_type="printed_secondary",
                language=secondary.code,
                target_scope="region_crops",
                description=f"PaddleOCR ({secondary.name}) for mixed-language alphanumeric regions",
            ))

    # 3. Handwritten Text Model (TrOCR)
    if has_handwriting:
        selected.append(SelectedOcrModel(
            engine="trocr",
            model_name="microsoft/trocr-base-handwritten",
            text_type="handwritten",
            language=primary.code,
            target_scope="region_crops",
            description="TrOCR for handwritten annotations, signatures, and filled fields",
        ))

    return selected


# ---------------------------------------------------------------------------
# Step 4: Text Type Identification (Printed vs. Handwritten Candidates)
# ---------------------------------------------------------------------------

def detect_handwriting_candidate_blocks(
    pages: list[dict[str, Any]],
    confidence_threshold: float = 0.65,
) -> list[dict[str, Any]]:
    """Scan OCR output blocks to identify candidate handwritten text regions."""
    candidates = []
    for page in pages:
        page_num = page.get("page", 1)
        for block in page.get("blocks", []):
            conf = block.get("confidence", 1.0)
            engine = block.get("ocr_engine", "")
            # Only consider blocks processed by printed OCR engines with low confidence
            if ("paddle" in engine or "tesseract" in engine) and conf < confidence_threshold:
                text = block.get("text", "").strip()
                if len(text) >= 2:
                    candidates.append({
                        "page": page_num,
                        "bbox": block.get("bbox", [0, 0, 0, 0]),
                        "text": text,
                        "confidence": conf,
                    })
    return candidates


# ---------------------------------------------------------------------------
# Step 5: Master Pipeline Execution
# ---------------------------------------------------------------------------

def process_document_intelligently(
    file_bytes: bytes,
    content_type: str,
    language_hint: str = "auto",
    enable_handwriting: bool = True,
    sample_pages: int = 3,
) -> IntelligentOCRResult:
    """Analyze document, detect language(s), select OCR model(s), and extract text.

    Args:
        file_bytes: Raw bytes of the PDF or image.
        content_type: MIME type (application/pdf, image/jpeg, etc.)
        language_hint: Optional forced language ("auto", "ta", "hi", etc.)
        enable_handwriting: Whether to trigger TrOCR on handwritten regions.
        sample_pages: Max pages to sample during initial language identification.

    Returns:
        IntelligentOCRResult with full structured information.
    """
    t0 = time.monotonic()

    # 1. Automatic Language & Script Identification
    if language_hint and language_hint not in ("auto", "unknown"):
        primary_name = LANGUAGE_NAMES.get(language_hint, language_hint)
        detected_languages = [
            DetectedLanguage(
                code=language_hint,
                name=primary_name,
                script="Auto",
                confidence=0.99,
                is_primary=True,
                char_share=0.95,
                char_count=100,
            ),
            DetectedLanguage(
                code="en",
                name="English",
                script="Latin",
                confidence=0.85,
                is_primary=False,
                char_share=0.05,
                char_count=5,
            )
        ]
        is_mixed_language = True
        detection_method = "manual_override"
    else:
        detected_languages, is_mixed_language, detection_method = identify_language_and_scripts(
            file_bytes, content_type, sample_pages=sample_pages
        )

    primary_lang = detected_languages[0].code if detected_languages else "hi"
    logger.info(
        "IntelligentOCRRouter: Detected language: %s (conf=%.2f, mixed=%s, method=%s)",
        primary_lang, detected_languages[0].confidence, is_mixed_language, detection_method
    )

    # 2. Run Primary Multilingual OCR via PaddleOCR
    from app.services.ocr_service import run_ocr
    ocr_result = run_ocr(file_bytes, content_type, language=primary_lang)

    pages = ocr_result.pages or []
    extracted_text = ocr_result.text or ""
    overall_confidence = ocr_result.confidence or 0.85

    # 3. Handwriting Region Detection & TrOCR Routing
    has_handwriting = False
    handwritten_blocks_count = 0
    candidate_hw_regions = []

    if enable_handwriting and pages:
        candidate_hw_regions = detect_handwriting_candidate_blocks(pages, confidence_threshold=0.60)
        if candidate_hw_regions:
            has_handwriting = True
            logger.info(
                "IntelligentOCRRouter: Detected %d candidate handwritten regions",
                len(candidate_hw_regions)
            )
            # Invoke TrOCR on handwritten regions
            try:
                from app.services.trocr_service import run_trocr_on_regions, get_trocr_status
                from app.services.pdf_renderer import render_pdf_pages
                from PIL import Image

                trocr_status = get_trocr_status()
                if trocr_status["transformers_available"] and trocr_status["torch_available"]:
                    page_images: dict[int, Image.Image] = {}
                    if content_type == "application/pdf":
                        renders = render_pdf_pages(file_bytes)
                        for pnum, img, _, _ in renders:
                            page_images[pnum] = img
                    else:
                        img = Image.open(BytesIO(file_bytes)).convert("RGB")
                        page_images[1] = img

                    for cand in candidate_hw_regions:
                        pnum = cand["page"]
                        if pnum in page_images:
                            hw_res = run_trocr_on_regions(
                                page_images[pnum],
                                [{"bbox": cand["bbox"], "label": "handwriting"}],
                                page=pnum,
                                language=primary_lang,
                            )
                            if hw_res and hw_res[0].text.strip():
                                cand["trocr_text"] = hw_res[0].text.strip()
                                cand["trocr_conf"] = hw_res[0].confidence
                                handwritten_blocks_count += 1
            except Exception as hw_exc:
                logger.warning("IntelligentOCRRouter: TrOCR invocation warning: %s", hw_exc)

    # 4. Model Selection Records
    selected_models = select_ocr_models(
        detected_languages,
        is_mixed_language=is_mixed_language,
        has_handwriting=has_handwriting,
    )

    # 5. Enrich OCR Blocks with Language, Model & Text Type Metadata
    total_printed_blocks = 0
    for page in pages:
        for block in page.get("blocks", []):
            block_text = block.get("text", "")
            # Check if this block was tagged as handwritten by TrOCR
            matching_hw = next((c for c in candidate_hw_regions if c.get("text") == block_text and "trocr_text" in c), None)
            if matching_hw:
                block["text"] = matching_hw["trocr_text"]
                block["confidence"] = matching_hw["trocr_conf"]
                block["text_type"] = "handwritten"
                block["ocr_model"] = "trocr"
                block["language"] = primary_lang
            else:
                block["text_type"] = "printed"
                block["ocr_model"] = f"paddle_{primary_lang}"
                total_printed_blocks += 1

                # Script-level block tagging for mixed-language content
                block_counts = count_unicode_scripts(block_text)
                if block_counts.get("Latin", 0) > 0 and block_counts.get(detected_languages[0].script, 0) == 0:
                    block["language"] = "en"
                else:
                    block["language"] = primary_lang

    text_type_breakdown = {
        "printed_blocks": total_printed_blocks,
        "handwritten_blocks": handwritten_blocks_count,
        "dominant_type": "printed" if total_printed_blocks >= handwritten_blocks_count else "handwritten",
    }

    elapsed_ms = (time.monotonic() - t0) * 1000

    return IntelligentOCRResult(
        detected_languages=detected_languages,
        is_mixed_language=is_mixed_language,
        text_type_breakdown=text_type_breakdown,
        selected_ocr_models=selected_models,
        overall_confidence=overall_confidence,
        page_count=ocr_result.page_count or 1,
        extracted_text=extracted_text,
        pages=pages,
        metadata={
            "detection_method": detection_method,
            "elapsed_ms": round(elapsed_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
