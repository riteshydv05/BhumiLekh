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
    """Persist extracted field results to document_results table."""
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
                original_text=item.get("original_text"),
                normalized_text=item.get("normalized_text"),
                transliteration=item.get("transliteration"),
                translation=item.get("translation"),
                confidence=item.get("confidence"),
                validated=item.get("validated", False),
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

    logger.info("[%s][OCR_PROCESSING] Starting OCR (type=%s)", doc_id, content_type)
    ocr_result = run_ocr(file_bytes, content_type)

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


def _stage_extraction(doc_id: str, text: str, language: str) -> list:
    """EXTRACTION: Run NLP entity extraction.

    Returns list of LandRecordEntity / ExtractedField objects.
    """
    from app.services.nlp_service import extract_entities, score_confidence

    logger.info("[%s][EXTRACTION] Extracting entities", doc_id)
    extraction = extract_entities(text, language)
    extraction = score_confidence(extraction)

    logger.info(
        "[%s][EXTRACTION] Extracted %d fields", doc_id, len(extraction.fields)
    )
    return extraction.fields


def _stage_multilingual(doc_id: str, fields: list) -> list:
    """MULTILINGUAL: Transliterate, digit-normalize, and translate extracted fields."""
    from app.services.multilingual_service import enrich_entity

    logger.info("[%s][MULTILINGUAL] Enriching %d fields with IndicXlit/translation", doc_id, len(fields))
    enriched_fields = []
    for field_obj in fields:
        try:
            enriched = enrich_entity(field_obj)
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
        # Stage 5: EXTRACTION (IndicNER / rules)
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_EXTRACTION)
        fields = []
        try:
            fields = _stage_extraction(doc_id, text, language)
            metadata["stages"]["extraction"] = {
                "status": "ok",
                "field_count": len(fields),
                "fields": [getattr(f, "entity_type", getattr(f, "field_name", "")) for f in fields],
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
        # Stage 7: STORE RESULTS (Idempotent DB update)
        # --------------------------------------------------------------
        results_to_save: list[dict] = []
        if validation and validation.field_results:
            validation_map = {
                r.field_name: r.is_valid for r in validation.field_results
            }
        else:
            validation_map = {}

        for ef in fields:
            f_name = getattr(ef, "field_name", getattr(ef, "entity_type", ""))
            f_val = getattr(ef, "field_value", getattr(ef, "extracted_value", None))
            is_valid = validation_map.get(f_name, True)
            
            results_to_save.append({
                "field_name": f_name,
                "field_value": f_val,
                "original_text": getattr(ef, "original_text", f_val),
                "normalized_text": getattr(ef, "normalized_text", f_val),
                "transliteration": getattr(ef, "transliteration", ""),
                "translation": getattr(ef, "translation", None),
                "confidence": getattr(ef, "confidence", 1.0),
                "validated": is_valid,
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
        # Stage 8: Final status
        # --------------------------------------------------------------
        metadata["pipeline_end"] = datetime.utcnow().isoformat()
        final_status = STATUS_VERIFICATION if requires_review else STATUS_COMPLETED

        _set_status(
            doc_id,
            final_status,
            processing_metadata=metadata,
        )

        logger.info(
            "%s Pipeline complete → %s (anomalies=%d, fields=%d)",
            log_prefix, final_status, len(anomalies), len(fields),
        )
        return {
            "status": final_status,
            "field_count": len(fields),
            "anomaly_count": len(anomalies),
            "ml_anomaly_score": ml_anomaly_meta.get("anomaly_score", 0.0),
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
