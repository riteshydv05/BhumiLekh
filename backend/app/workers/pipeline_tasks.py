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
    doc_id: str,
    status: str,
    error: str | None = None,
    **extra_fields: Any,
) -> None:
    """Update document status (and optional fields) in the database."""
    from app.models.document import Document

    db = _get_db_session()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
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


def _save_results(doc_id: str, fields_with_meta: list[dict]) -> None:
    """Persist extracted field results to document_results table."""
    from app.models.document_result import DocumentResult

    db = _get_db_session()
    try:
        # Remove existing results for this document (idempotent re-runs)
        db.query(DocumentResult).filter(
            DocumentResult.document_id == doc_id
        ).delete()

        for item in fields_with_meta:
            result = DocumentResult(
                document_id=doc_id,
                field_name=item["field_name"],
                field_value=item.get("field_value"),
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

def _stage_download(doc_id: str) -> tuple[bytes, str]:
    """PREPROCESSING: Download file bytes from MinIO.

    Returns (file_bytes, content_type).
    """
    from app.models.document import Document
    from app.services.storage_service import download_file_bytes

    logger.info("[%s][PREPROCESSING] Downloading from MinIO", doc_id)
    db = _get_db_session()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
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

    if ocr_result.warnings:
        for w in ocr_result.warnings:
            logger.warning("[%s][OCR_PROCESSING] Warning: %s", doc_id, w)

    # Persist OCR metadata back to document
    _set_status(
        doc_id,
        STATUS_OCR,
        page_count=ocr_result.page_count,
        ocr_confidence=ocr_result.confidence,
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


def _stage_language_detection(doc_id: str, text: str) -> str:
    """Detect language and persist to document."""
    from app.services.language_service import detect_language

    lang = detect_language(text)
    logger.info("[%s] Detected language: %s", doc_id, lang)

    db = _get_db_session()
    try:
        from app.models.document import Document
        doc = db.query(Document).filter(Document.id == doc_id).first()
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

    Returns list of ExtractedField objects.
    """
    from app.services.nlp_service import extract_entities, score_confidence

    logger.info("[%s][EXTRACTION] Extracting entities", doc_id)
    extraction = extract_entities(text, language)
    extraction = score_confidence(extraction)

    logger.info(
        "[%s][EXTRACTION] Extracted %d fields", doc_id, len(extraction.fields)
    )
    return extraction.fields


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
    max_retries=0,      # Do not auto-retry — failures are stored in DB
    acks_late=True,
)
def process_document(self, document_id: str) -> dict:
    """Full AI processing pipeline for a single document.

    This task is idempotent: re-running it for the same document_id
    will overwrite previous results.
    """
    doc_id = document_id
    log_prefix = f"[{doc_id}]"
    logger.info("%s Pipeline started", log_prefix)

    metadata: dict[str, Any] = {
        "pipeline_start": datetime.utcnow().isoformat(),
        "stages": {},
    }

    # ------------------------------------------------------------------
    # Stage 0: Mark QUEUED
    # ------------------------------------------------------------------
    _set_status(doc_id, STATUS_QUEUED)

    try:
        # --------------------------------------------------------------
        # Stage 1: PREPROCESSING — download from MinIO
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_PREPROCESSING)
        try:
            file_bytes, content_type = _stage_download(doc_id)
            metadata["stages"]["preprocessing"] = {
                "status": "ok",
                "bytes": len(file_bytes),
                "content_type": content_type,
            }
        except Exception as exc:
            logger.error("%s[PREPROCESSING] Failed: %s", log_prefix, exc, exc_info=True)
            _set_status(doc_id, STATUS_FAILED, error=f"Preprocessing failed: {exc}")
            return {"status": STATUS_FAILED, "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 2: OCR_PROCESSING
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_OCR)
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
                # Store full structured OCR pages for LayoutLMv3 consumption
                "ocr_pages": ocr_pages,
            }
        except Exception as exc:
            logger.error("%s[OCR] Failed: %s", log_prefix, exc, exc_info=True)
            # OCR failure is non-critical for PDFs with embedded text
            text = ""
            ocr_pages = []
            metadata["stages"]["ocr"] = {"status": "failed", "error": str(exc)}
            logger.warning("%s Continuing with empty text after OCR failure", log_prefix)

        # --------------------------------------------------------------
        # Stage 2b: Language Detection (part of OCR stage)
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
                # Append TrOCR text to the main text for NLP extraction
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
        # Stage 5: EXTRACTION
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_EXTRACTION)
        fields = []
        try:
            fields = _stage_extraction(doc_id, text, language)
            metadata["stages"]["extraction"] = {
                "status": "ok",
                "field_count": len(fields),
                "fields": [f.field_name for f in fields],
            }
        except Exception as exc:
            logger.error("%s[EXTRACTION] Failed: %s", log_prefix, exc, exc_info=True)
            metadata["stages"]["extraction"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 6: VALIDATING
        # --------------------------------------------------------------
        _set_status(doc_id, STATUS_VALIDATING)
        anomalies: list[str] = []
        requires_review = False
        validation = None
        try:
            validation, anomalies = _stage_validation(doc_id, fields, text)
            requires_review = validation.requires_human_review
            metadata["stages"]["validation"] = {
                "status": "ok",
                "anomalies": anomalies,
                "missing_mandatory": validation.missing_mandatory,
                "requires_human_review": requires_review,
            }
        except Exception as exc:
            logger.error("%s[VALIDATION] Failed: %s", log_prefix, exc, exc_info=True)
            metadata["stages"]["validation"] = {"status": "failed", "error": str(exc)}

        # --------------------------------------------------------------
        # Stage 7: STORE RESULTS
        # --------------------------------------------------------------
        results_to_save: list[dict] = []
        anomaly_field_names = set()

        if validation and validation.field_results:
            validation_map = {
                r.field_name: r.is_valid for r in validation.field_results
            }
        else:
            validation_map = {}

        for ef in fields:
            is_valid = validation_map.get(ef.field_name, True)
            results_to_save.append({
                "field_name": ef.field_name,
                "field_value": ef.field_value,
                "confidence": ef.confidence,
                "validated": is_valid,
                "anomaly_flag": False,
                "anomaly_reason": None,
            })

        # Attach anomalies — associate with area/date fields when possible
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
        }

    except Exception as exc:
        # Catch-all safety net — the worker must never crash
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
            pass  # Don't cascade failures
        return {"status": STATUS_FAILED, "error": str(exc)}
