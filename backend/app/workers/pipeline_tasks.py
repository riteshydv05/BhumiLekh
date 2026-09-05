"""Celery AI Processing Pipeline.

Task: process_document(document_id: str)

Pipeline stages:
  UPLOADED → QUEUED → PREPROCESSING → OCR_PROCESSING → LAYOUT_ANALYSIS
  → EXTRACTION → VALIDATING → COMPLETED | VERIFICATION_REQUIRED | FAILED

Every stage:
  - Updates document.status in the DB
  - Uses structured logging with [document_id][STAGE] prefix
  - Catches all exceptions
  - Stores errors in document.error_message
  - Never crashes the Celery worker
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
STATUS_QUEUED = "QUEUED"
STATUS_PREPROCESSING = "PREPROCESSING"
STATUS_OCR = "OCR_PROCESSING"
STATUS_LAYOUT = "LAYOUT_ANALYSIS"
STATUS_EXTRACTION = "EXTRACTION"
STATUS_VALIDATING = "VALIDATING"
STATUS_COMPLETED = "COMPLETED"
STATUS_VERIFICATION = "VERIFICATION_REQUIRED"
STATUS_FAILED = "FAILED"


# ---------------------------------------------------------------------------
# DB helpers (local imports to keep Celery serialisation clean)
# ---------------------------------------------------------------------------

def _get_db_session():
    from app.db.session import SessionLocal
    return SessionLocal()


def _set_status(
    doc_id: str | uuid.UUID,
    status: str,
    error: str | None = None,
    **extra_fields: Any,
) -> None:
    """Update document status (and optional fields) in the database."""
    from app.models.document import Document

    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        doc = db.query(Document).filter(Document.id == target_uuid).first()
        if not doc:
            logger.error("[%s] Document not found in DB", doc_id)
            return
        doc.status = status
        doc.updated_at = datetime.utcnow()
        if error is not None:
            doc.error_message = error
        for key, value in extra_fields.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        db.commit()
        logger.info("[%s] Status → %s", doc_id, status)
    except Exception as exc:
        logger.error("[%s] Failed to update status to %s: %s", doc_id, status, exc)
        db.rollback()
    finally:
        db.close()


def _save_results(doc_id: str | uuid.UUID, fields_with_meta: list[dict]) -> None:
    """Persist extracted field results to document_results table.

    Supports both old-style (fixed field names) and new dynamic fields
    with data_type, page_number, bounding_box, extraction_method,
    canonical_key, source_text, and validation_status.
    """
    from app.models.document_result import DocumentResult

    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        # Remove existing results for this document (idempotent re-runs)
        db.query(DocumentResult).filter(
            DocumentResult.document_id == target_uuid
        ).delete()

        for item in fields_with_meta:
            result = DocumentResult(
                document_id=target_uuid,
                field_name=item["field_name"],
                field_value=item.get("field_value"),
                original_text=item.get("original_text", item.get("source_text")),
                normalized_text=item.get("normalized_text"),
                normalized_value=item.get("normalized_value"),
                transliteration=item.get("transliteration"),
                translation=item.get("translation"),
                confidence=item.get("confidence"),
                data_type=item.get("data_type", "string"),
                page_number=item.get("page_number"),
                bounding_box=item.get("bounding_box"),
                source_text=item.get("source_text"),
                extraction_method=item.get("extraction_method", "key_value_extraction"),
                canonical_key=item.get("canonical_key"),
                validated=item.get("validated", False),
                validation_status=item.get("validation_status", "pending"),
                anomaly_flag=item.get("anomaly_flag", False),
                anomaly_reason=item.get("anomaly_reason"),
            )
            db.add(result)

        db.commit()
        logger.info("[%s] Saved %d field results to DB", doc_id, len(fields_with_meta))
    except Exception as exc:
        logger.error("[%s] Failed to save results: %s", doc_id, exc)
        db.rollback()
    finally:
        db.close()


def _save_ocr_pages(doc_id: str | uuid.UUID, ocr_pages: list[dict], language: str = "en") -> None:
    """Store raw OCR output per page in the document_pages table."""
    from app.models.document_page import DocumentPage

    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        # Remove existing OCR pages (idempotent)
        db.query(DocumentPage).filter(
            DocumentPage.document_id == target_uuid
        ).delete()

        for page_data in ocr_pages:
            page_num = page_data.get("page", 1)
            blocks = page_data.get("blocks", [])
            raw_text = "\n".join(
                str(b.get("text", "")) for b in blocks
                if isinstance(b, dict) and b.get("text")
            )
            avg_conf = 0.0
            conf_blocks = [b.get("confidence", 0.0) for b in blocks if isinstance(b, dict) and b.get("confidence")]
            if conf_blocks:
                avg_conf = sum(conf_blocks) / len(conf_blocks)

            engines = set(b.get("ocr_engine", "unknown") for b in blocks if isinstance(b, dict))

            page = DocumentPage(
                document_id=target_uuid,
                page_number=page_num,
                raw_text=raw_text if raw_text.strip() else None,
                language=language,
                ocr_confidence=avg_conf,
                ocr_engine=", ".join(sorted(engines)) if engines else None,
                blocks_json=blocks,
            )
            db.add(page)

        db.commit()
        logger.info("[%s] Stored raw OCR for %d pages", doc_id, len(ocr_pages))
    except Exception as exc:
        logger.error("[%s] Failed to store OCR pages: %s", doc_id, exc)
        db.rollback()
    finally:
        db.close()


def _stage_classify(doc_id: str, text: str) -> tuple[str, float]:
    """CLASSIFICATION: Determine document type from OCR text."""
    from app.services.dynamic_extraction_service import classify_document

    logger.info("[%s][CLASSIFICATION] Classifying document type", doc_id)
    doc_type, confidence = classify_document(text)

    # Persist document_type
    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        from app.models.document import Document
        doc = db.query(Document).filter(Document.id == target_uuid).first()
        if doc:
            doc.document_type = doc_type
            doc.updated_at = datetime.utcnow()
            db.commit()
    except Exception as exc:
        logger.warning("[%s] Failed to persist document_type: %s", doc_id, exc)
        db.rollback()
    finally:
        db.close()

    logger.info("[%s][CLASSIFICATION] type=%s confidence=%.2f", doc_id, doc_type, confidence)
    return doc_type, confidence


def _stage_handwriting(
    doc_id: str,
    file_bytes: bytes,
    content_type: str,
    ocr_pages: list,
    handwriting_regions: list[dict] | None = None,
) -> list[dict]:
    """HANDWRITING stage: run TrOCR on detected or explicit handwriting regions.

    Strategy:
      1. If ``handwriting_regions`` are provided explicitly (caller-supplied
         bounding boxes), process those on their respective pages.
      2. Otherwise, identify blocks in ``ocr_pages`` where the PaddleOCR
         confidence is below ``HANDWRITING_CONF_THRESHOLD`` — these are
         likely to be handwritten or poorly printed regions.
      3. Render the relevant page images (via pdf_renderer or direct PIL)
         and pass each crop to TrOCR.
      4. Returns a list of HwOcrResult dicts (serializable).
      5. If TrOCR is unavailable, returns a single dict with status=unavailable.
      6. Never raises — all exceptions are caught and logged.
    """
    from app.services.trocr_service import (
        run_trocr_on_regions, get_trocr_status, HwOcrResult
    )

    status = get_trocr_status()
    if not status["transformers_available"] or not status["torch_available"]:
        logger.info(
            "[%s][HANDWRITING] TrOCR skipped — transformers/torch unavailable",
            doc_id,
        )
        return [{"status": "unavailable", "reason": "transformers or torch not installed"}]

    hw_results: list[dict] = []

    # -----------------------------------------------------------------------
    # Case 1: Explicit handwriting regions provided
    # -----------------------------------------------------------------------
    if handwriting_regions:
        logger.info(
            "[%s][HANDWRITING] Processing %d explicit handwriting regions",
            doc_id, len(handwriting_regions),
        )
        # Group regions by page number
        from collections import defaultdict
        by_page: dict[int, list] = defaultdict(list)
        for r in handwriting_regions:
            pg = r.get("page", 1)
            by_page[pg].append(r)

        page_images = _render_page_images(file_bytes, content_type)

        for page_num, regions in by_page.items():
            pil_img = page_images.get(page_num)
            if pil_img is None:
                logger.warning(
                    "[%s][HANDWRITING] No rendered image for page %d", doc_id, page_num
                )
                continue
            results = run_trocr_on_regions(pil_img, regions, page=page_num)
            hw_results.extend(r.to_dict() for r in results)

    # -----------------------------------------------------------------------
    # Case 2: Auto-detect low-confidence blocks from PaddleOCR
    # -----------------------------------------------------------------------
    else:
        CONF_THRESHOLD = 0.5  # blocks below this are handwriting candidates
        candidate_blocks: list[dict] = []

        for page_dict in ocr_pages:
            page_num = page_dict.get("page", 1)
            for block in page_dict.get("blocks", []):
                conf = block.get("confidence", 1.0)
                engine = block.get("ocr_engine", "")
                # Only examine paddle blocks — pypdf blocks have no confidence
                if engine == "paddle" and conf < CONF_THRESHOLD:
                    candidate_blocks.append({
                        "page": page_num,
                        "bbox": block["bbox"],
                        "label": f"low-conf-{conf:.2f}",
                    })

        if not candidate_blocks:
            logger.info(
                "[%s][HANDWRITING] No low-confidence blocks found (threshold=%.2f)"
                " — skipping TrOCR",
                doc_id, CONF_THRESHOLD,
            )
            return [{"status": "skipped", "reason": "no handwriting candidates detected"}]

        logger.info(
            "[%s][HANDWRITING] Found %d low-confidence blocks as handwriting candidates",
            doc_id, len(candidate_blocks),
        )

        page_images = _render_page_images(file_bytes, content_type)

        from collections import defaultdict
        by_page: dict[int, list] = defaultdict(list)
        for c in candidate_blocks:
            by_page[c["page"]].append(c)

        for page_num, regions in by_page.items():
            pil_img = page_images.get(page_num)
            if pil_img is None:
                logger.warning(
                    "[%s][HANDWRITING] No image for page %d — cannot process candidates",
                    doc_id, page_num,
                )
                continue
            results = run_trocr_on_regions(pil_img, regions, page=page_num)
            hw_results.extend(r.to_dict() for r in results)

    logger.info(
        "[%s][HANDWRITING] TrOCR complete: %d regions processed",
        doc_id, len(hw_results),
    )
    return hw_results


def _stage_vlm_fallback(
    doc_id: str,
    file_bytes: bytes,
    content_type: str,
    ocr_pages: list,
    ocr_confidence: float,
) -> dict:
    """VLM Fallback Stage: Invoke external VLM provider when confidence is low.

    Checks settings.ENABLE_VLM_FALLBACK, provider configuration, and VLM_CONFIDENCE_THRESHOLD.
    Never overwrites original OCR results, only appends / stores fallback interpretations.
    """
    from app.core.config import settings
    from app.services.external import get_vlm_provider

    if not settings.ENABLE_VLM_FALLBACK:
        logger.info("[%s][VLM_FALLBACK] Disabled in configuration", doc_id)
        return {"status": "disabled", "invoked": False}

    provider = get_vlm_provider()
    if not provider.is_configured:
        logger.info(
            "[%s][VLM_FALLBACK] Selected provider (%s) is not configured (missing API key)",
            doc_id, provider.name,
        )
        return {"status": "not_configured", "invoked": False, "provider": provider.name}

    if ocr_confidence >= settings.VLM_CONFIDENCE_THRESHOLD:
        logger.info(
            "[%s][VLM_FALLBACK] OCR confidence %.2f >= threshold %.2f — skipping fallback",
            doc_id, ocr_confidence, settings.VLM_CONFIDENCE_THRESHOLD,
        )
        return {"status": "skipped_high_confidence", "invoked": False}

    logger.info(
        "[%s][VLM_FALLBACK] Low confidence detected (%.2f < %.2f) — escalating to %s",
        doc_id, ocr_confidence, settings.VLM_CONFIDENCE_THRESHOLD, provider.name,
    )

    page_images = _render_page_images(file_bytes, content_type)
    if not page_images:
        return {"status": "image_render_failed", "invoked": False}

    from io import BytesIO
    target_img = page_images.get(1)
    if not target_img:
        return {"status": "no_target_image", "invoked": False}

    img_byte_arr = BytesIO()
    target_img.save(img_byte_arr, format="PNG")
    crop_bytes = img_byte_arr.getvalue()

    prompt = (
        "Please transcribe the land record document text from this low-confidence region. "
        "Extract key land record details such as owner name, Khasra number, and land area if visible."
    )

    vlm_res = provider.analyze_image(
        image_bytes=crop_bytes,
        prompt=prompt,
        mime_type="image/png",
    )

    logger.info(
        "[%s][VLM_FALLBACK] Response from %s: success=%s, source=%s",
        doc_id, provider.name, vlm_res.success, vlm_res.source,
    )

    return {
        "status": "completed" if vlm_res.success else "failed",
        "invoked": True,
        "provider": vlm_res.provider,
        "source": vlm_res.source,
        "text": vlm_res.text,
        "confidence": vlm_res.confidence,
        "timestamp": vlm_res.timestamp,
        "error": vlm_res.error,
    }



def _render_page_images(
    file_bytes: bytes,
    content_type: str,
) -> dict[int, "Any"]:
    """Return a dict mapping page_number → PIL Image.

    Handles both PDF (via pdf_renderer) and direct image inputs.
    Returns an empty dict if rendering fails. Never raises.
    """
    from PIL import Image
    from io import BytesIO

    page_images: dict[int, Any] = {}

    if content_type == "application/pdf":
        try:
            from app.services.pdf_renderer import render_pdf_pages
            rendered = render_pdf_pages(file_bytes, dpi=150)
            for page_num, pil_img, w, h in rendered:
                page_images[page_num] = pil_img
        except Exception as exc:
            logger.warning("_render_page_images: PDF rendering failed: %s", exc)
    else:
        try:
            img = Image.open(BytesIO(file_bytes)).convert("RGB")
            page_images[1] = img
        except Exception as exc:
            logger.warning("_render_page_images: image load failed: %s", exc)

    return page_images

def _stage_download(doc_id: str | uuid.UUID) -> tuple[bytes, str]:
    """PREPROCESSING: Download file bytes from MinIO.

    Returns (file_bytes, content_type).
    """
    from app.models.document import Document
    from app.services.storage_service import download_file_bytes

    logger.info("[%s][PREPROCESSING] Downloading from MinIO", doc_id)
    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        doc = db.query(Document).filter(Document.id == target_uuid).first()
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
        storage_key = doc.storage_key
        content_type = doc.content_type
    finally:
        db.close()

    file_bytes = download_file_bytes(storage_key)
    logger.info(
        "[%s][PREPROCESSING] Downloaded %d bytes (type=%s)",
        doc_id, len(file_bytes), content_type,
    )
    return file_bytes, content_type


def _stage_ocr(doc_id: str, file_bytes: bytes, content_type: str) -> tuple[str, list]:
    """OCR_PROCESSING: Extract text and block-level structure from document.

    Returns (full_text, pages_list).
    pages_list contains the normalized per-page block dicts for layout analysis.
    Updates DB with page_count and ocr_confidence.
    """
    from app.services.ocr_service import run_ocr
    from app.models.document import Document

    target_lang = "auto"
    db = _get_db_session()
    try:
        doc = db.query(Document).filter(Document.id == uuid.UUID(str(doc_id))).first()
        if doc and doc.detected_language and doc.detected_language != "unknown":
            target_lang = doc.detected_language
    except Exception:
        pass
    finally:
        db.close()

    logger.info("[%s][OCR_PROCESSING] Starting OCR (type=%s, lang=%s)", doc_id, content_type, target_lang)
    ocr_result = run_ocr(file_bytes, content_type, language=target_lang)

    logger.info(
        "[%s][OCR_PROCESSING] Complete: pages=%d confidence=%.2f method=%s blocks=%d",
        doc_id, ocr_result.page_count, ocr_result.confidence, ocr_result.method,
        sum(len(p.get('blocks', [])) for p in ocr_result.pages),
    )

    if not ocr_result.text and file_bytes:
        try:
            decoded = file_bytes.decode("utf-8", errors="ignore").strip()
            if decoded and len(decoded) > 10:
                lines = [line.strip() for line in decoded.split("\n") if line.strip()]
                blocks = [{"text": l, "bbox": [0, 0, 100, 20], "confidence": 0.9, "ocr_engine": "text_fallback"} for l in lines]
                ocr_result.text = decoded
                ocr_result.pages = [{"page": 1, "blocks": blocks}]
                ocr_result.confidence = 0.90
        except Exception:
            pass

    # Persist OCR metadata back to document
    _set_status(
        doc_id,
        STATUS_OCR,
        page_count=ocr_result.page_count or 1,
        ocr_confidence=ocr_result.confidence or 0.9,
    )

    return ocr_result.text, ocr_result.pages


def _stage_layout_analysis(
    doc_id: str, text: str, page_count: int,
    ocr_pages: list[dict] | None = None,
    file_bytes: bytes | None = None,
    content_type: str = "application/pdf",
) -> dict:
    """LAYOUT_ANALYSIS: Heuristic section and table detection + LayoutLMv3 layout processing.

    Returns a dict of layout metadata including LayoutLMv3-derived structure.
    LayoutLMv3 inference is attempted but does NOT provide land-record field
    classification without fine-tuning.
    """
    from app.services.layoutlmv3_service import (
        build_layout_document,
        LayoutLMv3ProcessorService,
    )
    from app.services.pdf_renderer import render_pdf_pages
    from PIL import Image
    from io import BytesIO

    logger.info(
        "[%s][LAYOUT_ANALYSIS] Analysing layout: %d pages, %d chars",
        doc_id, page_count, len(text),
    )
    import re

    # Count lines and non-empty sections
    lines = [l for l in text.split("\n") if l.strip()]
    line_count = len(lines)

    # Detect table-like rows: lines with 3+ tab/pipe-separated columns
    table_rows = sum(
        1 for l in lines if len(re.split(r"[\t|]{1,}", l)) >= 3
    )

    # Count heading-like lines (all caps, short)
    headings = sum(
        1 for l in lines if l.strip().isupper() and 5 < len(l.strip()) < 80
    )

    layout = {
        "page_count": page_count,
        "line_count": line_count,
        "estimated_table_rows": table_rows,
        "estimated_headings": headings,
        "text_length": len(text),
        "layoutlmv3_available": False,
        "layoutlmv3_structure": None,
    }

    # -----------------------------------------------------------------------
    # Attempt LayoutLMv3 layout processing (structure detection only)
    # -----------------------------------------------------------------------
    try:
        ocr_doc = {
            "pages": ocr_pages or [],
            "method": "paddle",
            "error": None,
            "warnings": [],
        }
        page_images: dict[int, Image.Image] = {}

        if content_type == "application/pdf" and file_bytes:
            try:
                renders = render_pdf_pages(file_bytes, dpi=150)
                for pn, pil_img, w, h in renders:
                    page_images[pn] = pil_img
            except Exception:
                logger.warning("[%s] Could not render page images for LayoutLMv3", doc_id)
        elif content_type in {"image/jpeg", "image/png", "image/tiff"} and file_bytes:
            try:
                img = Image.open(BytesIO(file_bytes)).convert("RGB")
                page_images[1] = img
            except Exception:
                pass

        layout_doc = build_layout_document(ocr_doc, page_images=page_images)

        # Try to initialize LayoutLMv3 for structure detection
        lm_service = LayoutLMv3ProcessorService()
        if lm_service.initialize():
            layout["layoutlmv3_available"] = True
            layout["layoutlmv3_structure"] = layout_doc.to_dict()
            logger.info(
                "[%s][LAYOUT_ANALYSIS] LayoutLMv3 structure available for %d pages",
                doc_id, layout_doc.page_count,
            )
        else:
            logger.info(
                "[%s][LAYOUT_ANALYSIS] LayoutLMv3 not available; heuristic only",
                doc_id,
            )
    except Exception as exc:
        logger.warning(
            "[%s][LAYOUT_ANALYSIS] LayoutLMv3 processing failed (non-critical): %s",
            doc_id, exc,
        )

    logger.info("[%s][LAYOUT_ANALYSIS] %s", doc_id, layout)
    return layout


def _stage_language_detection(doc_id: str | uuid.UUID, text: str) -> str:
    """Detect language and persist to document."""
    from app.services.language_service import detect_language

    lang = detect_language(text)
    logger.info("[%s] Detected language: %s", doc_id, lang)

    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        from app.models.document import Document
        doc = db.query(Document).filter(Document.id == target_uuid).first()
        if doc:
            doc.detected_language = lang
            doc.updated_at = datetime.utcnow()
            db.commit()
    except Exception as exc:
        logger.warning("[%s] Failed to persist language: %s", doc_id, exc)
        db.rollback()
    finally:
        db.close()

    return lang


def _stage_extraction(doc_id: str, text: str, language: str, ocr_pages: list | None = None) -> list:
    """EXTRACTION: Dynamic field discovery + optional NLP entity extraction.

    Uses the new dynamic_extraction_service to discover fields from the
    document content rather than searching for predefined fields.
    Falls back to legacy nlp_service extraction and merges results.

    Returns list of DynamicField / LandRecordEntity objects.
    """
    from app.services.dynamic_extraction_service import extract_dynamic_fields

    logger.info("[%s][EXTRACTION] Running dynamic field discovery", doc_id)
    dynamic_result = extract_dynamic_fields(text, ocr_pages, language)
    dynamic_fields = dynamic_result.fields

    logger.info(
        "[%s][EXTRACTION] Dynamic discovery: %d fields (type=%s)",
        doc_id, len(dynamic_fields), dynamic_result.document_type,
    )

    # Also run legacy NLP extraction for backward compatibility
    legacy_fields = []
    try:
        from app.services.nlp_service import extract_entities, score_confidence
        extraction = extract_entities(text, language)
        extraction = score_confidence(extraction)
        legacy_fields = extraction.fields
        logger.info(
            "[%s][EXTRACTION] Legacy NLP: %d fields", doc_id, len(legacy_fields)
        )
    except Exception as exc:
        logger.warning("[%s][EXTRACTION] Legacy NLP failed (non-critical): %s", doc_id, exc)

    # Merge: dynamic fields take priority; add legacy fields for types not already covered
    seen_canonical = set()
    for f in dynamic_fields:
        if f.canonical_key:
            seen_canonical.add(f.canonical_key)

    merged = list(dynamic_fields)
    for lf in legacy_fields:
        entity_type = getattr(lf, "entity_type", "")
        if entity_type and entity_type not in seen_canonical:
            seen_canonical.add(entity_type)
            merged.append(lf)

    logger.info("[%s][EXTRACTION] Total merged fields: %d", doc_id, len(merged))
    return merged


def _stage_multilingual(doc_id: str, fields: list) -> list:
    """MULTILINGUAL: Transliterate, digit-normalize, and translate extracted fields."""
    from app.services.multilingual_service import enrich_entity
    from app.services.translation_service import translate_text

    logger.info("[%s][MULTILINGUAL] Enriching %d fields with IndicXlit/translation", doc_id, len(fields))
    enriched_fields = []
    for field_obj in fields:
        try:
            enriched = enrich_entity(field_obj)
            val_text = getattr(enriched, "normalized_text", None) or getattr(enriched, "original_text", None) or getattr(enriched, "field_value", None) or getattr(enriched, "source_text", None) or ""
            if val_text and not getattr(enriched, "translation", None):
                tr = translate_text(val_text, target_lang="en")
                if tr:
                    enriched.translation = tr
            enriched_fields.append(enriched)
        except Exception as exc:
            logger.warning("[%s][MULTILINGUAL] Failed to enrich field %s: %s", doc_id, getattr(field_obj, "entity_type", ""), exc)
            enriched_fields.append(field_obj)
    return enriched_fields


def _stage_ml_anomaly(doc_id: str, fields: list) -> dict:
    """ISOLATION_FOREST: Run scikit-learn IsolationForest ML anomaly detection."""
    from app.services.anomaly_service import detect_anomalies as detect_ml_anomalies

    logger.info("[%s][ISOLATION_FOREST] Running ML anomaly detection", doc_id)
    ml_result = detect_ml_anomalies(fields)
    logger.info(
        "[%s][ISOLATION_FOREST] Result: flag=%s score=%.4f risk=%s",
        doc_id, ml_result.anomaly_flag, ml_result.anomaly_score, ml_result.risk_classification
    )
    return ml_result.to_dict()


def _stage_validation(
    doc_id: str, fields: list, text: str
) -> tuple[bool, list[str]]:
    """VALIDATING: Validate fields and detect anomalies.

    Returns (requires_human_review, anomalies).
    """
    from app.services.validation_service import detect_anomalies, validate_fields

    logger.info("[%s][VALIDATING] Validating %d fields", doc_id, len(fields))
    validation = validate_fields(fields)
    anomalies = detect_anomalies(fields, text, validation)

    logger.info(
        "[%s][VALIDATING] requires_review=%s, anomalies=%d",
        doc_id, validation.requires_human_review, len(anomalies),
    )
    return validation, anomalies


# ---------------------------------------------------------------------------
# Main Celery task
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.workers.pipeline_tasks.process_document",
    bind=True,
    max_retries=3,      # Retry up to 3 times for transient infrastructure failures
    default_retry_delay=5,
    acks_late=True,
)
def process_document(self, document_id: str) -> dict:
    """Full AI processing pipeline for a single document.

    This task is idempotent: re-running it for the same document_id
    will overwrite previous results safely.
    Intermediate stage results are checkpointed so retries avoid repeating
    successful expensive stages.
    """
    doc_id = document_id
    log_prefix = f"[{doc_id}]"
    logger.info("%s Pipeline started", log_prefix)

    # Fetch existing metadata for stage checkpointing
    db = _get_db_session()
    existing_stages: dict[str, Any] = {}
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id
    try:
        from app.models.document import Document
        doc = db.query(Document).filter(Document.id == target_uuid).first()
        if doc and doc.processing_metadata and "stages" in doc.processing_metadata:
            existing_stages = doc.processing_metadata["stages"]
    except Exception:
        existing_stages = {}
    finally:
        db.close()

    metadata: dict[str, Any] = {
        "pipeline_start": datetime.utcnow().isoformat(),
        "stages": existing_stages,
    }

    # ------------------------------------------------------------------
    # Stage 0: Mark QUEUED
    # ------------------------------------------------------------------
    _set_status(doc_id, STATUS_QUEUED)

    try:
        # --------------------------------------------------------------
        # Stage 1: PREPROCESSING — download from MinIO (or use cached bytes)
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_PREPROCESSING)
        file_bytes: bytes = b""
        content_type: str = "application/pdf"
        try:
            file_bytes, content_type = _stage_download(doc_id)
            metadata["stages"]["preprocessing"] = {
                "status": "ok",
                "bytes": len(file_bytes),
                "content_type": content_type,
            }
        except (OSError, ConnectionError) as transient_exc:
            logger.warning("%s[PREPROCESSING] Transient error: %s. Retrying task.", log_prefix, transient_exc)
            if self.request.retries < self.max_retries:
                raise self.retry(exc=transient_exc)
            _set_status(doc_id, STATUS_FAILED, error=f"Preprocessing failed: {transient_exc}")
            return {"status": STATUS_FAILED, "error": str(transient_exc)}
        except Exception as exc:
            logger.error("%s[PREPROCESSING] Permanent failure: %s", log_prefix, exc, exc_info=True)
            _set_status(doc_id, STATUS_FAILED, error=f"Preprocessing failed: {exc}")
            return {"status": STATUS_FAILED, "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 2: OCR_PROCESSING (Check checkpoint first)
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_OCR)
        text: str = ""
        ocr_pages: list = []
        
        # Check if OCR was already completed in prior run
        if metadata["stages"].get("ocr", {}).get("status") == "ok" and "ocr_pages" in metadata["stages"]["ocr"]:
            logger.info("%s[OCR] Reusing checkpointed OCR results", log_prefix)
            ocr_pages = metadata["stages"]["ocr"]["ocr_pages"]
            text = metadata["stages"]["ocr"].get("text_preview", "")
        else:
            try:
                text, ocr_pages = _stage_ocr(doc_id, file_bytes, content_type)
                total_blocks = sum(len(p.get('blocks', [])) for p in ocr_pages)
                metadata["stages"]["ocr"] = {
                    "status": "ok",
                    "text_length": len(text),
                    "text_preview": text[:300] if text else "",
                    "method": "paddle" if ocr_pages and any(
                        b.get("ocr_engine") == "paddle"
                        for p in ocr_pages for b in p.get("blocks", [])
                    ) else "pypdf_text",
                    "total_blocks": total_blocks,
                    "ocr_pages": ocr_pages,
                }
            except Exception as exc:
                logger.error("%s[OCR] Failed: %s", log_prefix, exc, exc_info=True)
                text = ""
                ocr_pages = []
                metadata["stages"]["ocr"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 2b: Language Detection
        # --------------------------------------------------------------
        language = _stage_language_detection(doc_id, text)
        metadata["stages"]["language"] = {"detected": language}

        # --------------------------------------------------------------
        # Stage 2c: Store raw OCR pages (audit trail / reprocessing)
        # --------------------------------------------------------------
        try:
            _save_ocr_pages(doc_id, ocr_pages, language)
            metadata["stages"]["ocr_storage"] = {"status": "ok", "pages": len(ocr_pages)}
        except Exception as exc:
            logger.warning("%s[OCR_STORAGE] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["ocr_storage"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 2d: Document Classification
        # --------------------------------------------------------------
        doc_type = "Unknown"
        try:
            doc_type, doc_type_conf = _stage_classify(doc_id, text)
            metadata["stages"]["classification"] = {
                "status": "ok",
                "document_type": doc_type,
                "confidence": doc_type_conf,
            }
        except Exception as exc:
            logger.warning("%s[CLASSIFICATION] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["classification"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 3: LAYOUT_ANALYSIS
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_LAYOUT)
        try:
            page_count = len(ocr_pages) if ocr_pages else 1
            layout = _stage_layout_analysis(
                doc_id, text, page_count,
                ocr_pages=ocr_pages,
                file_bytes=file_bytes,
                content_type=content_type,
            )
            metadata["stages"]["layout"] = {"status": "ok", **layout}
        except Exception as exc:
            logger.warning("%s[LAYOUT] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["layout"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 4: HANDWRITING (TrOCR)
        # --------------------------------------------------------------
        try:
            hw_results = _stage_handwriting(
                doc_id, file_bytes, content_type, ocr_pages
            )
            processed = [r for r in hw_results if r.get("text")]
            metadata["stages"]["handwriting"] = {
                "status": "ok" if processed else "skipped",
                "regions_processed": len(hw_results),
                "regions_with_text": len(processed),
                "results": hw_results,
            }
            if processed:
                hw_text = " ".join(r["text"] for r in processed if r.get("text"))
                if hw_text.strip():
                    text = text + "\n" + hw_text
                    logger.info(
                        "%s[HANDWRITING] Appended %d chars from TrOCR",
                        log_prefix, len(hw_text),
                    )
        except Exception as exc:
            logger.warning("%s[HANDWRITING] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["handwriting"] = {
                "status": "failed",
                "error": str(exc),
            }

        # --------------------------------------------------------------
        # Stage 4b: OPTIONAL VLM FALLBACK (Gemini/OpenAI/Anthropic)
        # --------------------------------------------------------------
        try:
            ocr_conf = metadata["stages"].get("ocr", {}).get("confidence", 0.8)
            vlm_meta = _stage_vlm_fallback(
                doc_id, file_bytes, content_type, ocr_pages, ocr_conf
            )
            metadata["stages"]["vlm_fallback"] = vlm_meta
            if vlm_meta.get("invoked") and vlm_meta.get("text"):
                # Append VLM interpretation without overwriting original OCR text
                text = text + f"\n[{vlm_meta.get('source', 'vlm')}_interpretation]: " + vlm_meta["text"]
                logger.info(
                    "%s[VLM_FALLBACK] Appended %d chars from VLM provider %s",
                    log_prefix, len(vlm_meta["text"]), vlm_meta.get("provider"),
                )
        except Exception as exc:
            logger.warning("%s[VLM_FALLBACK] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["vlm_fallback"] = {"status": "failed", "error": str(exc)}


        # --------------------------------------------------------------
        # Stage 5: EXTRACTION (Dynamic Discovery + Legacy NLP)
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_EXTRACTION)
        fields = []
        try:
            fields = _stage_extraction(doc_id, text, language, ocr_pages)
            metadata["stages"]["extraction"] = {
                "status": "ok",
                "field_count": len(fields),
                "fields": [getattr(f, "field_name", getattr(f, "entity_type", "")) for f in fields],
            }
        except Exception as exc:
            logger.error("%s[EXTRACTION] Failed: %s", log_prefix, exc, exc_info=True)
            metadata["stages"]["extraction"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 5b: MULTILINGUAL ENRICHMENT (IndicXlit / translation)
        # --------------------------------------------------------------
        try:
            fields = _stage_multilingual(doc_id, fields)
            metadata["stages"]["multilingual"] = {
                "status": "ok",
                "enriched_count": len(fields),
            }
        except Exception as exc:
            logger.warning("%s[MULTILINGUAL] Failed: %s", log_prefix, exc)
            metadata["stages"]["multilingual"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 6: VALIDATING & ISOLATION FOREST ANOMALY DETECTION
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_VALIDATING)
        anomalies: list[str] = []
        requires_review = False
        validation = None
        ml_anomaly_meta: dict = {}
        try:
            validation, anomalies = _stage_validation(doc_id, fields, text)
            requires_review = validation.requires_human_review
            
            # Execute IsolationForest ML Anomaly Service explicitly for pipeline metadata
            ml_anomaly_meta = _stage_ml_anomaly(doc_id, fields)
            if ml_anomaly_meta.get("anomaly_flag"):
                requires_review = True

            metadata["stages"]["validation"] = {
                "status": "ok",
                "anomalies": anomalies,
                "missing_mandatory": validation.missing_mandatory,
                "requires_human_review": requires_review,
            }
            metadata["stages"]["isolation_forest_anomaly_detection"] = {
                "status": "ok",
                **ml_anomaly_meta,
            }
        except Exception as exc:
            logger.error("%s[VALIDATION] Failed: %s", log_prefix, exc, exc_info=True)
            metadata["stages"]["validation"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 6b: CONFIDENCE SCORING
        # --------------------------------------------------------------
        confidence_report = None
        try:
            from app.services.confidence_service import score_document_fields
            confidence_report = score_document_fields(fields)
            metadata["stages"]["confidence"] = {
                "status": "ok",
                **confidence_report.to_dict(),
            }
            # Flag for review if overall confidence is LOW or UNCERTAIN
            if confidence_report.overall_category in ("LOW", "UNCERTAIN"):
                requires_review = True
            logger.info(
                "%s[CONFIDENCE] Overall=%.2f (%s), flagged=%d",
                log_prefix, confidence_report.overall_confidence,
                confidence_report.overall_category,
                len(confidence_report.flagged_fields),
            )
        except Exception as exc:
            logger.warning("%s[CONFIDENCE] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["confidence"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 6c: CROSS-DATABASE VERIFICATION
        # --------------------------------------------------------------
        verification_report = None
        try:
            from app.services.verification_service import verify_against_reference
            verification_report = verify_against_reference(str(doc_id), fields)
            metadata["stages"]["verification"] = {
                "status": "ok",
                **verification_report.to_dict(),
            }
            if verification_report.mismatch_count > 0:
                requires_review = True
            logger.info(
                "%s[VERIFICATION] status=%s, matches=%d, mismatches=%d",
                log_prefix, verification_report.overall_status,
                verification_report.match_count,
                verification_report.mismatch_count,
            )
        except Exception as exc:
            logger.warning("%s[VERIFICATION] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["verification"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 6d: DUPLICATE DETECTION
        # --------------------------------------------------------------
        duplicate_report = None
        try:
            from app.services.duplicate_service import detect_duplicates
            duplicate_report = detect_duplicates(
                str(doc_id),
                file_bytes=file_bytes,
                fields=fields,
            )
            metadata["stages"]["duplicate_detection"] = {
                "status": "ok",
                **duplicate_report.to_dict(),
            }
            if duplicate_report.has_file_duplicate or duplicate_report.has_content_duplicate:
                requires_review = True
            logger.info(
                "%s[DUPLICATE] file_dup=%s, content_dup=%s, total=%d",
                log_prefix, duplicate_report.has_file_duplicate,
                duplicate_report.has_content_duplicate,
                len(duplicate_report.duplicates),
            )
        except Exception as exc:
            logger.warning("%s[DUPLICATE] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["duplicate_detection"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 7: STORE RESULTS (Idempotent DB update)
        # --------------------------------------------------------------
        results_to_save: list[dict] = []
        if validation and validation.field_results:
            validation_map = {
                r.field_name: r.is_valid for r in validation.field_results
            }
        else:
            validation_map = {}

        # Build confidence map
        confidence_map: dict[str, dict] = {}
        if confidence_report:
            for fc in confidence_report.field_scores:
                confidence_map[fc.field_name] = {
                    "category": fc.category,
                    "needs_review": fc.needs_review,
                }

        # Build verification map
        verification_map: dict[str, dict] = {}
        if verification_report:
            for fv in verification_report.field_verifications:
                verification_map[fv.field_name] = {
                    "status": fv.status,
                    "reference_value": fv.reference_value,
                }

        for ef in fields:
            f_name = getattr(ef, "field_name", getattr(ef, "entity_type", ""))
            f_val = getattr(ef, "field_value", getattr(ef, "extracted_value", None))
            is_valid = validation_map.get(f_name, True)
            conf_info = confidence_map.get(f_name, {})
            verif_info = verification_map.get(f_name, {})

            # Determine validation_status from multiple signals
            v_status = "valid" if is_valid else "invalid"
            if verif_info.get("status") == "MISMATCH":
                v_status = "mismatch"
            elif conf_info.get("needs_review"):
                v_status = "review_needed" if is_valid else "invalid"

            results_to_save.append({
                "field_name": f_name,
                "field_value": f_val,
                "original_text": getattr(ef, "source_text", getattr(ef, "original_text", f_val)),
                "normalized_text": getattr(ef, "normalized_text", f_val),
                "transliteration": getattr(ef, "transliteration", ""),
                "translation": getattr(ef, "translation", None),
                "confidence": getattr(ef, "confidence", 1.0),
                "data_type": getattr(ef, "data_type", "string"),
                "page_number": getattr(ef, "page_number", getattr(ef, "page", None)),
                "bounding_box": getattr(ef, "bounding_box", None),
                "source_text": getattr(ef, "source_text", getattr(ef, "original_text", "")),
                "extraction_method": getattr(ef, "extraction_method", "key_value_extraction"),
                "canonical_key": getattr(ef, "canonical_key", None),
                "validated": is_valid,
                "validation_status": v_status,
                "anomaly_flag": False,
                "anomaly_reason": None,
            })

        # Attach anomalies to matching fields
        for anomaly in anomalies:
            associated = False
            for keyword in ("area", "date", "market_value", "owner"):
                for res in results_to_save:
                    if keyword in res["field_name"] and not res["anomaly_flag"]:
                        res["anomaly_flag"] = True
                        res["anomaly_reason"] = anomaly
                        associated = True
                        break
                if associated:
                    break

        _save_results(doc_id, results_to_save)

        # --------------------------------------------------------------
        # Stage 7b: STORE VALIDATION RESULTS
        # --------------------------------------------------------------
        try:
            _save_validation_results(
                doc_id, results_to_save,
                confidence_report=confidence_report,
                verification_report=verification_report,
                duplicate_report=duplicate_report,
                anomalies=anomalies,
            )
            metadata["stages"]["validation_storage"] = {"status": "ok"}
        except Exception as exc:
            logger.warning("%s[VALIDATION_STORAGE] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["validation_storage"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 8: Final status
        # --------------------------------------------------------------
        metadata["pipeline_end"] = datetime.utcnow().isoformat()
        final_status = STATUS_VERIFICATION if requires_review else STATUS_COMPLETED

        _set_status(
            doc_id,
            final_status,
            processing_metadata=metadata,
        )

        # --------------------------------------------------------------
        # Stage 8b: LEARNING FEEDBACK (Auto-record verified fields)
        # --------------------------------------------------------------
        learning_samples_count = 0
        try:
            if final_status == STATUS_COMPLETED:
                from app.services.learning_service import record_verified_document
                learning_samples_count = record_verified_document(str(doc_id))
                metadata["stages"]["learning_feedback"] = {
                    "status": "ok",
                    "samples_recorded": learning_samples_count,
                }
                logger.info(
                    "%s[LEARNING] Recorded %d verified fields as training data",
                    log_prefix, learning_samples_count,
                )
            else:
                metadata["stages"]["learning_feedback"] = {
                    "status": "skipped",
                    "reason": f"Document status is {final_status}, not COMPLETED",
                }
        except Exception as exc:
            logger.warning("%s[LEARNING] Failed (non-critical): %s", log_prefix, exc)
            metadata["stages"]["learning_feedback"] = {"status": "failed", "error": str(exc)}

        logger.info(
            "%s Pipeline complete → %s (anomalies=%d, fields=%d, confidence=%s, verification=%s, learning=%d)",
            log_prefix, final_status, len(anomalies), len(fields),
            confidence_report.overall_category if confidence_report else "N/A",
            verification_report.overall_status if verification_report else "N/A",
            learning_samples_count,
        )
        return {
            "status": final_status,
            "field_count": len(fields),
            "anomaly_count": len(anomalies),
            "ml_anomaly_score": ml_anomaly_meta.get("anomaly_score", 0.0),
            "confidence_overall": confidence_report.overall_confidence if confidence_report else None,
            "confidence_category": confidence_report.overall_category if confidence_report else None,
            "verification_status": verification_report.overall_status if verification_report else None,
            "duplicate_detected": (duplicate_report.has_file_duplicate or duplicate_report.has_content_duplicate) if duplicate_report else False,
            "learning_samples_recorded": learning_samples_count,
        }

    except Exception as exc:
        logger.error(
            "%s Unexpected pipeline error: %s", log_prefix, exc, exc_info=True
        )
        metadata["pipeline_end"] = datetime.utcnow().isoformat()
        metadata["fatal_error"] = str(exc)
        try:
            _set_status(
                doc_id,
                STATUS_FAILED,
                error=f"Unexpected error: {exc}",
                processing_metadata=metadata,
            )
        except Exception:
            pass
        return {"status": STATUS_FAILED, "error": str(exc)}


def _save_validation_results(
    doc_id: str | uuid.UUID,
    results_to_save: list[dict],
    confidence_report: Any = None,
    verification_report: Any = None,
    duplicate_report: Any = None,
    anomalies: list[str] | None = None,
) -> None:
    """Persist per-field validation/verification/confidence results to validation_results table."""
    from app.models.validation_result import ValidationResult
    from app.models.document_result import DocumentResult

    db = _get_db_session()
    target_uuid = uuid.UUID(str(doc_id)) if not isinstance(doc_id, uuid.UUID) else doc_id

    try:
        # Remove existing validation results (idempotent re-runs)
        db.query(ValidationResult).filter(
            ValidationResult.document_id == target_uuid
        ).delete()

        # Build lookup maps
        confidence_map: dict[str, Any] = {}
        if confidence_report:
            for fc in confidence_report.field_scores:
                confidence_map[fc.field_name] = fc

        verification_map: dict[str, Any] = {}
        if verification_report:
            for fv in verification_report.field_verifications:
                verification_map[fv.field_name] = fv

        # Get document_result IDs for linking
        doc_results = db.query(DocumentResult).filter(
            DocumentResult.document_id == target_uuid
        ).all()
        result_id_map = {dr.field_name: dr.id for dr in doc_results}

        for field_data in results_to_save:
            f_name = field_data["field_name"]
            fc = confidence_map.get(f_name)
            fv = verification_map.get(f_name)

            vr = ValidationResult(
                document_id=target_uuid,
                field_result_id=result_id_map.get(f_name),
                field_name=f_name,
                confidence_score=field_data.get("confidence"),
                confidence_category=fc.category if fc else None,
                validation_passed=field_data.get("validated", True),
                validation_errors=None,
                verification_status=fv.status if fv else None,
                reference_value=fv.reference_value if fv else None,
                verification_source=fv.source if fv else None,
                anomaly_detected=field_data.get("anomaly_flag", False),
                anomaly_details=field_data.get("anomaly_reason"),
                is_duplicate_flag=False,
            )
            db.add(vr)

        db.commit()
        logger.info("[%s] Saved %d validation results to DB", doc_id, len(results_to_save))
    except Exception as exc:
        logger.error("[%s] Failed to save validation results: %s", doc_id, exc)
        db.rollback()
    finally:
        db.close()

